"""PyGambit-based Nash equilibrium solver."""

import tempfile
import os
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
import pygambit as gbt


class SolverResult:
    """Represents Nash equilibrium solution results."""
    
    def __init__(self):
        """Initialize solver result."""
        self.equilibria: List[Dict[str, Any]] = []
        self.game_info: Dict[str, Any] = {}
        self.error: Optional[str] = None
    
    def add_equilibrium(self, equilibrium: Dict[str, Any]):
        """Add an equilibrium to results."""
        self.equilibria.append(equilibrium)
    
    def set_error(self, error: str):
        """Set error message."""
        self.error = error
    
    def is_success(self) -> bool:
        """Check if solving was successful."""
        return self.error is None


class GameSolver:
    """Nash equilibrium solver using PyGambit."""
    
    # Available solvers with descriptions
    AVAILABLE_SOLVERS = {
        'enumpure': 'Pure strategy enumeration',
        'enummixed': 'Mixed strategy enumeration (2-player)',
        'lcp': 'Linear complementarity (2-player)',
        'lp': 'Linear programming (2-player zero-sum)',
        'liap': 'Lyapunov function minimization',
        'gnm': 'Global Newton method',
    }
    
    @staticmethod
    def _get_solver_function(solver_name: str, game) -> Optional[Callable]:
        """Get the solver function for a given solver name.
        
        Args:
            solver_name: Name of the solver.
            game: PyGambit game object.
            
        Returns:
            Callable that executes the solver, or None if solver doesn't exist.
        """
        solver_name = solver_name.lower()
        
        # Map solver names to their execution functions
        solver_map = {
            'enumpure': lambda: gbt.nash.enumpure_solve(game),
            'enummixed': lambda: gbt.nash.enummixed_solve(game),
            'lcp': lambda: gbt.nash.lcp_solve(game),
            'lp': lambda: gbt.nash.lp_solve(game),
            'liap': lambda: gbt.nash.liap_solve(game.mixed_strategy_profile()),
            'gnm': lambda: gbt.nash.gnm_solve(game),
        }
        
        return solver_map.get(solver_name)
    
    @staticmethod
    def solve_from_content(content: str, solver: Optional[str] = None) -> SolverResult:
        """Solve game from file content.
        
        Args:
            content: Game file content (.nfg or .efg).
            solver: Optional specific solver to use. If None, tries multiple solvers.
            
        Returns:
            SolverResult with equilibria or error.
        """
        result = SolverResult()
        
        # Detect game type
        content = content.strip()
        if not content:
            result.set_error("Empty game file")
            return result
        
        if content.startswith("NFG"):
            return GameSolver._solve_nfg(content, solver)
        elif content.startswith("EFG"):
            return GameSolver._solve_efg(content, solver)
        else:
            result.set_error("Unknown game format. File must start with 'NFG' or 'EFG'")
            return result
    
    @staticmethod
    def _solve_nfg(content: str, solver: Optional[str] = None) -> SolverResult:
        """Solve strategic form game.
        
        Args:
            content: NFG file content.
            solver: Optional specific solver to use.
            
        Returns:
            SolverResult with equilibria.
        """
        result = SolverResult()
        
        try:
            # Write content to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.nfg', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Load game
                game = gbt.read_nfg(temp_path) # type: ignore
                
                # Store game info
                result.game_info = {
                    'title': game.title,
                    'num_players': len(game.players),
                    'players': [p.label for p in game.players],
                    'num_strategies': [len(p.strategies) for p in game.players],
                    'is_const_sum': game.is_const_sum,
                    'is_perfect_recall': game.is_perfect_recall
                }
                
                # Choose appropriate solver based on game properties
                equilibria = []
                solver_errors = []
                
                # If specific solver requested, use only that one
                if solver:
                    solver = solver.lower()
                    if solver not in GameSolver.AVAILABLE_SOLVERS:
                        result.set_error(f"Unknown solver: {solver}. Available: {', '.join(GameSolver.AVAILABLE_SOLVERS.keys())}")
                        return result
                    
                    solver_func = GameSolver._get_solver_function(solver, game)
                    if solver_func is None:
                        result.set_error(f"Solver '{solver}' not available")
                        return result
                    
                    try:
                        nash_result = solver_func()
                        equilibria = list(nash_result.equilibria)
                    except Exception as e:
                        result.set_error(f"Solver '{solver}' failed: {str(e)}")
                        return result
                else:
                    # Try multiple solvers automatically in priority order
                    # Priority order optimized for game type
                    solver_order = ['enumpure']  # Always try pure first
                    
                    if len(game.players) == 2:
                        # 2-player games: try LCP, then LP for const-sum, then enummixed
                        solver_order.extend(['lcp'])
                        if game.is_const_sum:
                            solver_order.append('lp')
                        solver_order.extend(['enummixed', 'liap', 'gnm'])
                    else:
                        # N-player games: try approximate methods
                        solver_order.extend(['liap', 'gnm'])
                    
                    # Try each solver in order until we find equilibria
                    for solver_name in solver_order:
                        if solver_name not in GameSolver.AVAILABLE_SOLVERS:
                            continue
                        
                        if equilibria:  # Stop if we found equilibria
                            break
                        
                        solver_func = GameSolver._get_solver_function(solver_name, game)
                        if solver_func is None:
                            continue
                        
                        try:
                            nash_result = solver_func()
                            equilibria.extend(nash_result.equilibria)
                        except Exception as e:
                            solver_errors.append(f"{solver_name}: {str(e)}")
                
                # Process equilibria
                for eq in equilibria:
                    eq_data = GameSolver._format_equilibrium(game, eq)
                    result.add_equilibrium(eq_data)
                
                if not result.equilibria:
                    error_msg = "No Nash equilibria found."
                    if solver_errors:
                        error_msg += "\n\nSolver errors encountered:\n" + "\n".join(f"• {err}" for err in solver_errors[:3])
                    result.set_error(error_msg)
            
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
        
        except ImportError:
            result.set_error("PyGambit not installed. Run: pip install pygambit")
        except Exception as e:
            result.set_error(f"Error solving game: {str(e)}")
        
        return result
    
    @staticmethod
    def _solve_efg(content: str, solver: Optional[str] = None) -> SolverResult:
        """Solve extensive form game.
        
        Args:
            content: EFG file content.
            solver: Optional specific solver to use.
            
        Returns:
            SolverResult with equilibria.
        """
        result = SolverResult()
        
        try:
            # Write content to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.efg', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Load game
                game = gbt.read_efg(temp_path) # type: ignore
                
                # Store game info
                result.game_info = {
                    'title': game.title,
                    'num_players': len(game.players),
                    'players': [p.label for p in game.players],
                    'is_perfect_recall': game.is_perfect_recall
                }
                
                # Solve extensive form game
                equilibria = []
                solver_errors = []
                
                # If specific solver requested, use only that one
                if solver:
                    solver = solver.lower()
                    if solver not in GameSolver.AVAILABLE_SOLVERS:
                        result.set_error(f"Unknown solver: {solver}. Available: {', '.join(GameSolver.AVAILABLE_SOLVERS.keys())}")
                        return result
                    
                    solver_func = GameSolver._get_solver_function(solver, game)
                    if solver_func is None:
                        result.set_error(f"Solver '{solver}' not available")
                        return result
                    
                    try:
                        nash_result = solver_func()
                        equilibria = list(nash_result.equilibria)
                    except Exception as e:
                        result.set_error(f"Solver '{solver}' failed: {str(e)}")
                        return result
                else:
                    # Try multiple solvers automatically
                    solver_order = ['enumpure', 'lcp', 'enummixed', 'liap']
                    
                    for solver_name in solver_order:
                        if solver_name not in GameSolver.AVAILABLE_SOLVERS:
                            continue
                        
                        if equilibria:  # Stop if we found equilibria
                            break
                        
                        solver_func = GameSolver._get_solver_function(solver_name, game)
                        if solver_func is None:
                            continue
                        
                        try:
                            nash_result = solver_func()
                            equilibria.extend(nash_result.equilibria)
                        except Exception as e:
                            solver_errors.append(f"{solver_name}: {str(e)}")
                
                # Filter to subgame perfect equilibria
                spne = [eq for eq in equilibria
                        if GameSolver._is_subgame_perfect(game, eq)]

                if not spne:
                    error_msg = "No subgame-perfect equilibria found among computed equilibria."
                    if equilibria:
                        error_msg += f"\n\nComputed {len(equilibria)} Nash equilibria, but none satisfied subgame perfection."
                    if solver_errors:
                        error_msg += "\n\nSolver errors encountered:\n" + "\n".join(f"• {err}" for err in solver_errors[:3])
                    result.set_error(error_msg)
                    return result

                # Process equilibria
                formatted = []
                for eq in spne:
                    eq_data = GameSolver._format_equilibrium(game, eq)
                    formatted.append(eq_data)

                # Merge equilibria that differ only in off-path actions
                merged = GameSolver._merge_efg_equilibria(game, formatted)
                for eq_data in merged:
                    result.add_equilibrium(eq_data)

                if not result.equilibria:
                    result.set_error("No subgame-perfect equilibria found.")

            finally:
                # Clean up temporary file
                os.unlink(temp_path)

        except ImportError:
            result.set_error("PyGambit not installed. Run: pip install pygambit")
        except Exception as e:
            result.set_error(f"Error solving game: {str(e)}")

        return result

    @staticmethod
    def _get_infoset_label(infoset) -> str:
        """Get a human-readable label for an information set.

        Args:
            infoset: PyGambit infoset object.

        Returns:
            Best available label for the information set.
        """
        # Get the infoset label directly from the infoset object
        # This corresponds to the infoset label in the EFG file (e.g., "EntryDecision")
        label = str(infoset.label) if infoset.label else ""

        return label if label else "Decision"

    @staticmethod
    def _get_unique_infoset_labels(player) -> Dict:
        """Build a mapping from infoset to unique label for a player.

        When multiple infosets share the same label, disambiguates using
        the member node label (e.g., "User Reaction (Users vs StatusQuo)").

        Args:
            player: PyGambit player object.

        Returns:
            Dict mapping infoset to unique label string.
        """
        # Count label occurrences
        label_counts: Dict[str, int] = {}
        for infoset in player.infosets:
            label = GameSolver._get_infoset_label(infoset)
            label_counts[label] = label_counts.get(label, 0) + 1

        # Build unique labels
        labels = {}
        for infoset in player.infosets:
            label = GameSolver._get_infoset_label(infoset)
            if label_counts[label] > 1:
                # Disambiguate using member node label
                members = list(infoset.members)
                if members and members[0].label and members[0].label.strip():
                    label = f"{label} ({members[0].label})"
                else:
                    # Fallback: append infoset number
                    label = f"{label} #{infoset.number + 1}"
            labels[infoset] = label

        return labels
    
    @staticmethod
    def _is_subgame_perfect(game, equilibrium) -> bool:
        """Check if an equilibrium is subgame perfect.

        Uses the one-shot deviation principle: a strategy profile is SPNE
        iff no player can profitably deviate at any single information set
        within any proper subgame. Proper subgames are identified by finding
        nodes that are singleton information sets with subtrees closed under
        all information sets.

        This correctly handles both perfect and imperfect information games.

        Args:
            game: PyGambit game object.
            equilibrium: PyGambit equilibrium profile.

        Returns:
            True if the equilibrium is subgame perfect.
        """
        # Get or convert to behavior strategy profile
        if hasattr(equilibrium, 'infoset_prob'):
            behavior = equilibrium
        else:
            try:
                behavior = equilibrium.as_behavior()
            except Exception:
                return True  # Can't verify, keep it

        num_players = len(game.players)

        def get_subtree(node):
            """Collect all nodes in the subtree rooted at node."""
            nodes = set()
            stack = [node]
            while stack:
                n = stack.pop()
                nodes.add(n)
                if not n.is_terminal:
                    for child in n.children:
                        stack.append(child)
            return nodes

        def is_subgame_root(node):
            """Check if node is the root of a proper subgame."""
            if node.is_terminal:
                return False
            infoset = node.infoset
            # Chance nodes or singleton player info sets can start subgames
            if not infoset.is_chance and len(list(infoset.members)) != 1:
                return False
            # Subtree must be closed: every player info set that intersects
            # the subtree must have ALL its members within the subtree
            nodes = get_subtree(node)
            for n in nodes:
                if n.is_terminal or n.infoset.is_chance:
                    continue
                for member in n.infoset.members:
                    if member not in nodes:
                        return False
            return True

        def node_payoff(node, override_infoset=None, override_action_idx=None):
            """Compute expected payoff vector from a node under the profile.

            If override_infoset/override_action_idx are set, the player
            deviates to that action at that info set (one-shot deviation).
            """
            if node.is_terminal:
                outcome = node.outcome
                if outcome:
                    return tuple(float(outcome[p]) for p in game.players)
                return (0.0,) * num_players

            infoset = node.infoset
            val = [0.0] * num_players

            for i, action in enumerate(infoset.actions):
                child_val = node_payoff(
                    node.children[i], override_infoset, override_action_idx
                )
                if infoset.is_chance:
                    prob = float(action.prob)
                elif override_infoset is not None and infoset == override_infoset:
                    prob = 1.0 if i == override_action_idx else 0.0
                else:
                    prob = float(behavior[action])
                for j in range(num_players):
                    val[j] += prob * child_val[j]

            return tuple(val)

        # Find all proper subgame roots
        all_nodes = get_subtree(game.root)
        subgame_roots = [n for n in all_nodes if is_subgame_root(n)]

        # Check for profitable one-shot deviations in each subgame
        for sg_root in subgame_roots:
            sg_nodes = get_subtree(sg_root)
            current_payoff = node_payoff(sg_root)

            # Collect player info sets within this subgame
            infosets_in_sg = set()
            for n in sg_nodes:
                if not n.is_terminal and not n.infoset.is_chance:
                    infosets_in_sg.add(n.infoset)

            for infoset in infosets_in_sg:
                pidx = infoset.player.number
                for aidx in range(len(infoset.actions)):
                    dev_payoff = node_payoff(sg_root, infoset, aidx)
                    if dev_payoff[pidx] > current_payoff[pidx] + 1e-6:
                        return False

        return True

    @staticmethod
    def _format_equilibrium(game, equilibrium) -> Dict[str, Any]:
        """Format equilibrium for display.
        
        Args:
            game: PyGambit game object.
            equilibrium: PyGambit equilibrium object.
            
        Returns:
            Dict with formatted equilibrium data.
        """
        eq_data = {
            'strategies': {},
            'payoffs': {},
            'is_pure': True
        }
        
        # Check if this is a behavior strategy profile (extensive form game)
        # or a mixed strategy profile (strategic form game)
        if hasattr(equilibrium, 'infoset_prob'):
            # Behavior strategy profile - format by infosets and actions
            for player in game.players:
                player_strats = {}
                unique_labels = GameSolver._get_unique_infoset_labels(player)
                for infoset in player.infosets:
                    infoset_label = unique_labels[infoset]
                    for action in infoset.actions:
                        prob = float(equilibrium[action])
                        action_label = f"{infoset_label}:{action.label}" if infoset_label else action.label
                        player_strats[action_label] = prob

                        # Check if this is a mixed strategy
                        if prob > 0 and prob < 1:
                            eq_data['is_pure'] = False

                eq_data['strategies'][player.label] = player_strats
        else:
            # Mixed strategy profile - format by strategies
            # For extensive form games, convert to behavior strategy profile to show action names
            # Check if this is an extensive form game by checking if players have infosets
            is_efg = False
            try:
                # Try accessing root - will raise exception for NFG games
                _ = game.root
                is_efg = len(game.players[0].infosets) > 0 if game.players else False
            except Exception:
                is_efg = False
            
            if is_efg:
                # This is an extensive form game - convert to behavior strategy
                try:
                    behavior_profile = equilibrium.as_behavior()
                    for player in game.players:
                        player_strats = {}
                        unique_labels = GameSolver._get_unique_infoset_labels(player)
                        for infoset in player.infosets:
                            infoset_label = unique_labels[infoset]
                            for action in infoset.actions:
                                prob = float(behavior_profile[action])
                                action_label = f"{infoset_label}:{action.label}" if infoset_label else action.label
                                player_strats[action_label] = prob

                                # Check if this is a mixed strategy
                                if prob > 0 and prob < 1:
                                    eq_data['is_pure'] = False

                        eq_data['strategies'][player.label] = player_strats
                except Exception:
                    # Fallback to mixed strategy format if conversion fails
                    for player in game.players:
                        player_strats = {}
                        for strategy in player.strategies:
                            prob = float(equilibrium[strategy])
                            player_strats[strategy.label] = prob
                            
                            # Check if this is a mixed strategy
                            if prob > 0 and prob < 1:
                                eq_data['is_pure'] = False
                        
                        eq_data['strategies'][player.label] = player_strats
            else:
                # Strategic form game - use strategy labels directly
                for player in game.players:
                    player_strats = {}
                    for strategy in player.strategies:
                        prob = float(equilibrium[strategy])
                        player_strats[strategy.label] = prob
                        
                        # Check if this is a mixed strategy
                        if prob > 0 and prob < 1:
                            eq_data['is_pure'] = False
                    
                    eq_data['strategies'][player.label] = player_strats
        
        # Calculate expected payoffs
        try:
            for i, player in enumerate(game.players):
                eq_data['payoffs'][player.label] = float(equilibrium.payoff(player))
        except Exception:
            # If payoff calculation fails, skip it
            pass

        return eq_data

    @staticmethod
    def _get_on_path_actions(game, eq_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Extract only on-path actions from an equilibrium's strategy profile.

        Walks the game tree following the chosen actions to determine which
        information sets are actually reached on the equilibrium path.

        Args:
            game: PyGambit game object.
            eq_data: Formatted equilibrium data with 'strategies' dict.

        Returns:
            Dict mapping player label to dict of on-path action_label:prob pairs.
        """
        # Build lookup: infoset -> unique label (matching _format_equilibrium keys)
        infoset_labels = {}
        for player in game.players:
            unique = GameSolver._get_unique_infoset_labels(player)
            for infoset, label in unique.items():
                infoset_labels[infoset] = label

        # Walk tree to find on-path infosets
        on_path_infosets = set()

        def walk(node):
            if node.is_terminal:
                return
            infoset = node.infoset
            if infoset.is_chance:
                # All chance branches are on-path
                for action in infoset.actions:
                    child_idx = list(infoset.actions).index(action)
                    walk(node.children[child_idx])
                return

            on_path_infosets.add(infoset)
            player_label = node.player.label
            iset_label = infoset_labels.get(infoset, "")

            # Find which action is chosen (prob > 0.99 for pure)
            player_strats = eq_data['strategies'].get(player_label, {})
            for i, action in enumerate(infoset.actions):
                action_key = f"{iset_label}:{action.label}" if iset_label else action.label
                prob = player_strats.get(action_key, 0)
                if prob > 0:
                    walk(node.children[i])

        walk(game.root)

        # Filter strategies to on-path only
        on_path = {}
        for player in game.players:
            unique = GameSolver._get_unique_infoset_labels(player)
            player_strats = eq_data['strategies'].get(player.label, {})
            filtered = {}
            for infoset in player.infosets:
                if infoset not in on_path_infosets:
                    continue
                iset_label = unique[infoset]
                for action in infoset.actions:
                    key = f"{iset_label}:{action.label}" if iset_label else action.label
                    if key in player_strats:
                        filtered[key] = player_strats[key]
            on_path[player.label] = filtered

        return on_path

    @staticmethod
    def _merge_efg_equilibria(game, equilibria: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge equilibria that share the same on-path outcome.

        Equilibria in extensive form games can differ only in off-path actions
        (actions at unreached information sets). These are strategically
        equivalent from the players' perspective and are merged into one.

        Args:
            game: PyGambit game object.
            equilibria: List of formatted equilibrium dicts.

        Returns:
            Deduplicated list with off-path actions removed from strategies.
        """
        seen = {}  # on-path signature -> merged eq_data
        merged = []

        for eq in equilibria:
            on_path = GameSolver._get_on_path_actions(game, eq)

            # Build a hashable signature from on-path actions
            sig_parts = []
            for player_label in sorted(on_path.keys()):
                for action_key in sorted(on_path[player_label].keys()):
                    sig_parts.append((player_label, action_key, on_path[player_label][action_key]))
            sig = tuple(sig_parts)

            if sig not in seen:
                # Replace full strategies with on-path only
                merged_eq = dict(eq)
                merged_eq['strategies'] = on_path
                seen[sig] = merged_eq
                merged.append(merged_eq)

        return merged

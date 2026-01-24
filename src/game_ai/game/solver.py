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
                for infoset in player.infosets:
                    infoset_label = GameSolver._get_infoset_label(infoset)
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
            if hasattr(game, 'root') and len(game.players[0].infosets) > 0:
                # This is an extensive form game - convert to behavior strategy
                try:
                    behavior_profile = equilibrium.as_behavior()
                    for player in game.players:
                        player_strats = {}
                        for infoset in player.infosets:
                            infoset_label = GameSolver._get_infoset_label(infoset)
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

"""PyGambit-based Nash equilibrium solver."""

import tempfile
import os
from typing import List, Dict, Any, Optional
from pathlib import Path


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
    
    # Available solvers
    AVAILABLE_SOLVERS = {
        'enumpure': 'Pure strategy enumeration',
        'enummixed': 'Mixed strategy enumeration (2-player)',
        'lcp': 'Linear complementarity (2-player)',
        'lp': 'Linear programming (2-player zero-sum)',
        'liap': 'Lyapunov function minimization',
        'gnm': 'Global Newton method',
    }
    
    @staticmethod
    def solve_from_content(content: str, solver: str = None) -> SolverResult:
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
    def _solve_nfg(content: str, solver: str = None) -> SolverResult:
        """Solve strategic form game.
        
        Args:
            content: NFG file content.
            solver: Optional specific solver to use.
            
        Returns:
            SolverResult with equilibria.
        """
        result = SolverResult()
        
        try:
            import pygambit as gbt
            
            # Write content to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.nfg', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Load game
                game = gbt.read_nfg(temp_path)
                
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
                    
                    try:
                        if solver == 'enumpure':
                            nash_result = gbt.nash.enumpure_solve(game)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'enummixed':
                            nash_result = gbt.nash.enummixed_solve(game)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'lcp':
                            nash_result = gbt.nash.lcp_solve(game)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'lp':
                            nash_result = gbt.nash.lp_solve(game)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'liap':
                            # LIAP requires a starting profile
                            start_profile = game.mixed_strategy_profile()
                            nash_result = gbt.nash.liap_solve(start_profile)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'gnm':
                            nash_result = gbt.nash.gnm_solve(game)
                            equilibria = list(nash_result.equilibria)
                    except Exception as e:
                        result.set_error(f"Solver '{solver}' failed: {str(e)}")
                        return result
                else:
                    # Try multiple solvers automatically
                    # Try pure strategy equilibria first
                    try:
                        nash_result = gbt.nash.enumpure_solve(game)
                        equilibria.extend(nash_result.equilibria)
                    except Exception as e:
                        solver_errors.append(f"enumpure: {str(e)}")
                    
                    # For 2-player games, try multiple solvers
                    if len(game.players) == 2:
                        # Try LCP solver first (works for most 2-player games)
                        if not equilibria:
                            try:
                                nash_result = gbt.nash.lcp_solve(game)
                                equilibria.extend(nash_result.equilibria)
                            except Exception as e:
                                solver_errors.append(f"lcp: {str(e)}")
                        
                        # Try LP solver for constant-sum games
                        if game.is_const_sum and not equilibria:
                            try:
                                nash_result = gbt.nash.lp_solve(game)
                                equilibria.extend(nash_result.equilibria)
                            except Exception as e:
                                solver_errors.append(f"lp: {str(e)}")
                        
                        # Fall back to enumeration for small games
                        if not equilibria:
                            try:
                                nash_result = gbt.nash.enummixed_solve(game)
                                equilibria.extend(nash_result.equilibria)
                            except Exception as e:
                                solver_errors.append(f"enummixed: {str(e)}")
                    else:
                        # For N-player games, try available solvers
                        if not equilibria:
                            try:
                                start_profile = game.mixed_strategy_profile()
                                nash_result = gbt.nash.liap_solve(start_profile)
                                equilibria.extend(nash_result.equilibria)
                            except Exception as e:
                                solver_errors.append(f"liap: {str(e)}")
                        
                        if not equilibria:
                            try:
                                nash_result = gbt.nash.gnm_solve(game)
                                equilibria.extend(nash_result.equilibria)
                            except Exception as e:
                                solver_errors.append(f"gnm: {str(e)}")
                
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
    def _solve_efg(content: str, solver: str = None) -> SolverResult:
        """Solve extensive form game.
        
        Args:
            content: EFG file content.
            solver: Optional specific solver to use.
            
        Returns:
            SolverResult with equilibria.
        """
        result = SolverResult()
        
        try:
            import pygambit as gbt
            
            # Write content to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.efg', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Load game
                game = gbt.read_efg(temp_path)
                
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
                    
                    try:
                        if solver == 'enumpure':
                            nash_result = gbt.nash.enumpure_solve(game)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'enummixed':
                            nash_result = gbt.nash.enummixed_solve(game)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'lcp':
                            nash_result = gbt.nash.lcp_solve(game)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'lp':
                            nash_result = gbt.nash.lp_solve(game)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'liap':
                            # LIAP requires a starting profile
                            start_profile = game.mixed_strategy_profile()
                            nash_result = gbt.nash.liap_solve(start_profile)
                            equilibria = list(nash_result.equilibria)
                        elif solver == 'gnm':
                            nash_result = gbt.nash.gnm_solve(game)
                            equilibria = list(nash_result.equilibria)
                    except Exception as e:
                        result.set_error(f"Solver '{solver}' failed: {str(e)}")
                        return result
                else:
                    # Try pure strategy equilibria
                    try:
                        nash_result = gbt.nash.enumpure_solve(game)
                        equilibria.extend(nash_result.equilibria)
                    except Exception as e:
                        solver_errors.append(f"enumpure: {str(e)}")
                    
                    # For 2-player games
                    if len(game.players) == 2:
                        if not equilibria:
                            try:
                                nash_result = gbt.nash.lcp_solve(game)
                                equilibria.extend(nash_result.equilibria)
                            except Exception as e:
                                solver_errors.append(f"lcp: {str(e)}")
                        
                        if not equilibria:
                            try:
                                nash_result = gbt.nash.enummixed_solve(game)
                                equilibria.extend(nash_result.equilibria)
                            except Exception as e:
                                solver_errors.append(f"enummixed: {str(e)}")
                    else:
                        # N-player games
                        if not equilibria:
                            try:
                                start_profile = game.mixed_strategy_profile()
                                nash_result = gbt.nash.liap_solve(start_profile)
                                equilibria.extend(nash_result.equilibria)
                            except Exception as e:
                                solver_errors.append(f"liap: {str(e)}")
                
                # Process equilibria
                for eq in equilibria:
                    eq_data = GameSolver._format_equilibrium(game, eq)
                    result.add_equilibrium(eq_data)
                
                if not result.equilibria:
                    error_msg = "No Nash equilibria found."
                    if solver_errors:
                        error_msg += "\n\nSolver errors encountered:\n" + "\n".join(f"• {err}" for err in solver_errors[:3])
                    result.set_error(error_msg)
                
                if not result.equilibria:
                    result.set_error("No Nash equilibria found (this may indicate solver limitations)")
            
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
        
        except ImportError:
            result.set_error("PyGambit not installed. Run: pip install pygambit")
        except Exception as e:
            result.set_error(f"Error solving game: {str(e)}")
        
        return result
    
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
        
        # Extract strategy probabilities for each player
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

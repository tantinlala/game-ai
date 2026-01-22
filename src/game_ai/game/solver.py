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
    
    @staticmethod
    def solve_from_content(content: str) -> SolverResult:
        """Solve game from file content.
        
        Args:
            content: Game file content (.nfg or .efg).
            
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
            return GameSolver._solve_nfg(content)
        elif content.startswith("EFG"):
            return GameSolver._solve_efg(content)
        else:
            result.set_error("Unknown game format. File must start with 'NFG' or 'EFG'")
            return result
    
    @staticmethod
    def _solve_nfg(content: str) -> SolverResult:
        """Solve strategic form game.
        
        Args:
            content: NFG file content.
            
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
                
                # Try pure strategy equilibria first
                try:
                    pure_eq = gbt.enumpure_solve(game)
                    equilibria.extend(pure_eq)
                except Exception:
                    pass
                
                # For 2-player games, try more efficient solvers
                if len(game.players) == 2:
                    try:
                        if game.is_const_sum:
                            # Linear programming for constant-sum games
                            mixed_eq = gbt.lp_solve(game)
                        else:
                            # LCP solver for general 2-player games
                            mixed_eq = gbt.lcp_solve(game)
                        equilibria.extend(mixed_eq)
                    except Exception as e:
                        # Fall back to enumeration for small games
                        try:
                            mixed_eq = gbt.enummixed_solve(game)
                            equilibria.extend(mixed_eq)
                        except Exception:
                            pass
                else:
                    # For N-player games, use global newton or liap
                    try:
                        n_player_eq = gbt.liap_solve(game)
                        equilibria.extend(n_player_eq)
                    except Exception:
                        try:
                            n_player_eq = gbt.gnm_solve(game)
                            equilibria.extend(n_player_eq)
                        except Exception:
                            pass
                
                # Process equilibria
                for eq in equilibria:
                    eq_data = GameSolver._format_equilibrium(game, eq)
                    result.add_equilibrium(eq_data)
                
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
    def _solve_efg(content: str) -> SolverResult:
        """Solve extensive form game.
        
        Args:
            content: EFG file content.
            
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
                
                # Try pure strategy equilibria
                try:
                    pure_eq = gbt.enumpure_solve(game)
                    equilibria.extend(pure_eq)
                except Exception:
                    pass
                
                # For 2-player games
                if len(game.players) == 2:
                    try:
                        mixed_eq = gbt.lcp_solve(game)
                        equilibria.extend(mixed_eq)
                    except Exception:
                        try:
                            mixed_eq = gbt.enummixed_solve(game)
                            equilibria.extend(mixed_eq)
                        except Exception:
                            pass
                else:
                    # N-player games
                    try:
                        n_player_eq = gbt.liap_solve(game)
                        equilibria.extend(n_player_eq)
                    except Exception:
                        pass
                
                # Process equilibria
                for eq in equilibria:
                    eq_data = GameSolver._format_equilibrium(game, eq)
                    result.add_equilibrium(eq_data)
                
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

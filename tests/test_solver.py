"""Tests for Nash equilibrium solver."""

import pytest
from game_ai.game.solver import GameSolver, SolverResult


@pytest.mark.unit
class TestSolverResult:
    """Tests for SolverResult class."""
    
    def test_initialization(self):
        """Test SolverResult initialization."""
        result = SolverResult()
        assert result.equilibria == []
        assert result.game_info == {}
        assert result.error is None
        assert result.is_success() is True
    
    def test_add_equilibrium(self):
        """Test adding equilibria."""
        result = SolverResult()
        eq = {'strategies': {}, 'payoffs': {}}
        result.add_equilibrium(eq)
        assert len(result.equilibria) == 1
        assert result.equilibria[0] == eq
    
    def test_set_error(self):
        """Test setting error."""
        result = SolverResult()
        result.set_error("Test error")
        assert result.error == "Test error"
        assert result.is_success() is False


@pytest.mark.unit
class TestGameSolver:
    """Tests for GameSolver class."""
    
    def test_solve_nfg_prisoners_dilemma(self, sample_nfg):
        """Test solving Prisoner's Dilemma (NFG)."""
        result = GameSolver.solve_from_content(sample_nfg)
        
        assert result.is_success(), f"Solving failed: {result.error}"
        assert len(result.equilibria) > 0, "Should find at least one equilibrium"
        
        # Check game info
        assert result.game_info['title'] == "Prisoner's Dilemma"
        assert result.game_info['num_players'] == 2
        assert result.game_info['players'] == ["Player 1", "Player 2"]
        
        # Check equilibrium structure
        eq = result.equilibria[0]
        assert 'strategies' in eq
        assert 'payoffs' in eq
        assert 'is_pure' in eq
        assert 'Player 1' in eq['strategies']
        assert 'Player 2' in eq['strategies']
    
    def test_solve_efg_simple(self, sample_efg):
        """Test solving simple EFG game."""
        result = GameSolver.solve_from_content(sample_efg)
        
        assert result.is_success(), f"Solving failed: {result.error}"
        assert len(result.equilibria) > 0
        
        # Check game info
        assert result.game_info['title'] == "Simplified Poker"
        assert result.game_info['num_players'] == 2
    
    def test_solve_empty_game(self):
        """Test solving empty game content."""
        result = GameSolver.solve_from_content("")
        
        assert not result.is_success()
        assert result.error is not None
        assert "Empty game file" in result.error
    
    def test_solve_invalid_game(self):
        """Test solving invalid game format."""
        content = "INVALID GAME"
        result = GameSolver.solve_from_content(content)
        
        assert not result.is_success()
        assert result.error is not None
        assert "Unknown game format" in result.error
    
    def test_solve_nfg_pure_coordination(self):
        """Test solving a pure coordination game."""
        # Battle of the Sexes - has multiple equilibria
        content = """NFG 1 R "Battle of Sexes"
{ "Player 1" "Player 2" }

{
{ "Opera" "Football" }
{ "Opera" "Football" }
}

{
{ "Both Opera" 2, 1 }
{ "P1 Opera P2 Football" 0, 0 }
{ "P1 Football P2 Opera" 0, 0 }
{ "Both Football" 1, 2 }
}
1 2 3 4"""
        
        result = GameSolver.solve_from_content(content)
        assert result.is_success()
        # Should find multiple equilibria (2 pure + 1 mixed)
        assert len(result.equilibria) >= 2
    
    def test_solve_nfg_with_whitespace(self, sample_nfg):
        """Test solving with extra whitespace."""
        content_with_whitespace = "\n\n" + sample_nfg + "\n\n  "
        result = GameSolver.solve_from_content(content_with_whitespace)
        assert result.is_success()
    
    def test_solve_result_structure(self, sample_nfg):
        """Test that solve result has proper structure."""
        result = GameSolver.solve_from_content(sample_nfg)
        
        assert hasattr(result, 'equilibria')
        assert hasattr(result, 'game_info')
        assert hasattr(result, 'error')
        assert callable(result.is_success)
        
        if result.equilibria:
            eq = result.equilibria[0]
            assert 'strategies' in eq
            assert 'payoffs' in eq
            assert 'is_pure' in eq
            assert isinstance(eq['strategies'], dict)
            assert isinstance(eq['payoffs'], dict)
            assert isinstance(eq['is_pure'], bool)


@pytest.mark.unit
class TestSolverMethods:
    """Tests for specific solver methods."""
    
    def test_available_solvers_list(self):
        """Test that available solvers are listed."""
        assert 'enumpure' in GameSolver.AVAILABLE_SOLVERS
        assert 'lcp' in GameSolver.AVAILABLE_SOLVERS
        assert 'enummixed' in GameSolver.AVAILABLE_SOLVERS
    
    def test_solver_with_specific_method(self, sample_nfg):
        """Test solving with specific solver."""
        result = GameSolver.solve_from_content(sample_nfg, solver='enumpure')
        assert result.is_success()
    
    def test_solver_with_invalid_method(self, sample_nfg):
        """Test solving with invalid solver name."""
        result = GameSolver.solve_from_content(sample_nfg, solver='invalid_solver')
        assert not result.is_success()
        assert result.error is not None
        assert "Unknown solver" in result.error

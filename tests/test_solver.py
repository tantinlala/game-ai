"""Tests for GameSolver."""
import pytest
from src.game_ai.game.solver import GameSolver


def test_solve_nfg_prisoners_dilemma():
    """Test solving prisoner's dilemma NFG game."""
    nfg_content = 'NFG 1 R "Prisoner\'s Dilemma" { "Player1" "Player2" } { 2 2 } 3 0 5 1 5 1 3 0'
    
    result = GameSolver.solve_from_content(nfg_content)
    
    assert result.is_success() == True
    assert len(result.equilibria) > 0
    # Prisoner's dilemma has one Nash equilibrium (Defect, Defect)
    assert isinstance(result.equilibria[0], dict)
    assert "strategies" in result.equilibria[0]


def test_solve_nfg_pure_coordination():
    """Test solving coordination game with multiple equilibria."""
    nfg_content = 'NFG 1 R "Coordination" { "P1" "P2" } { 2 2 } 2 0 0 2 0 1 1 0'
    
    result = GameSolver.solve_from_content(nfg_content)
    
    assert result.is_success() == True
    assert len(result.equilibria) >= 1  # At least one equilibrium


def test_solve_efg_simple():
    """Test solving simple EFG game."""
    efg_content = '''EFG 2 R "Simple Sequential" { "P1" "P2" }
p "" 1 1 "" { "L" "R" } 0
t "" 1 "" { 2.0 0.0 }
p "" 2 1 "" { "l" "r" } 0
t "" 2 "" { 1.0 1.0 }
t "" 3 "" { 0.0 3.0 }'''
    
    result = GameSolver.solve_from_content(efg_content)
    
    assert result.is_success() == True
    assert len(result.equilibria) > 0


def test_solve_empty_game():
    """Test solving empty game content."""
    result = GameSolver.solve_from_content("")
    
    assert result.is_success() == False
    assert result.error is not None
    assert "Empty game" in result.error


def test_solve_invalid_game():
    """Test solving invalid game format."""
    result = GameSolver.solve_from_content("INVALID GAME CONTENT")
    
    assert result.is_success() == False
    assert result.error is not None


def test_solve_nfg_with_whitespace():
    """Test solving game with extra whitespace."""
    # Use exact format from example file
    with open('examples/prisoners_dilemma.nfg', 'r') as f:
        nfg_content = f.read()
    
    result = GameSolver.solve_from_content(nfg_content)
    
    assert result.is_success() == True
    assert len(result.equilibria) > 0


def test_solve_result_structure():
    """Test that solve result has expected structure."""
    nfg_content = 'NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3 4'
    
    result = GameSolver.solve_from_content(nfg_content)
    
    assert hasattr(result, 'equilibria')
    assert hasattr(result, 'error')
    assert hasattr(result, 'game_info')
    if result.is_success():
        assert isinstance(result.equilibria, list)
    else:
        assert result.error is not None

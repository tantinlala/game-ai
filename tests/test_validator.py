"""Tests for GameValidator."""
import pytest
from src.game_ai.game.validator import GameValidator


def test_validate_empty_file():
    """Test validation of empty file."""
    errors = GameValidator.validate("")
    assert len(errors) == 1
    assert "Empty file" in str(errors[0])


def test_validate_valid_nfg():
    """Test validation of valid NFG file."""
    # Use exact format from example file
    with open('examples/prisoners_dilemma.nfg', 'r') as f:
        nfg_content = f.read()
    errors = GameValidator.validate(nfg_content)
    assert len(errors) == 0


def test_validate_valid_efg():
    """Test validation of valid EFG file."""
    efg_content = '''EFG 2 R "Simple Game"
{ "Player1" "Player2" }
p "" 1 1 "" { "L" "R" } 0
t "" 1 "" { 2 0 }
p "" 2 1 "" { "l" "r" } 0
t "" 2 "" { 1 1 }
t "" 3 "" { 0 3 }'''
    errors = GameValidator.validate(efg_content)
    assert len(errors) == 0


def test_validate_invalid_format():
    """Test validation of invalid format."""
    invalid_content = "This is not a valid game file"
    errors = GameValidator.validate(invalid_content)
    assert len(errors) > 0
    assert "must start with 'NFG' or 'EFG'" in str(errors[0])


def test_validate_nfg_missing_payoffs():
    """Test validation of NFG with missing payoffs."""
    nfg_content = 'NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3'  # Missing 4th payoff
    errors = GameValidator.validate(nfg_content)
    # pygambit should catch this
    assert len(errors) > 0


def test_validate_malformed_nfg():
    """Test validation of malformed NFG."""
    nfg_content = 'NFG 1 R "Test" { "P1" } { 2 }'  # Incomplete
    errors = GameValidator.validate(nfg_content)
    assert len(errors) > 0


def test_validate_whitespace_only():
    """Test validation of whitespace-only content."""
    errors = GameValidator.validate("   \n\t  ")
    assert len(errors) == 1
    assert "Empty file" in str(errors[0])

"""Pytest configuration and shared fixtures."""

import pytest
import tempfile
import os
from pathlib import Path


# Sample game files for testing
SAMPLE_NFG = """NFG 1 R "Prisoner's Dilemma"
{ "Player 1" "Player 2" }
{ 2 2 }

3 3 0 5 5 0 1 1"""

SAMPLE_EFG = """EFG 2 R "Simplified Poker"
{ "Player 1" "Player 2" }

c "Deal" 1 "(0,1)" { "High" 0.5 "Low" 0.5 } 0
p "P1 has High" 1 1 "(1,1)" { "Bet" "Check" } 0
p "P2 after Bet" 2 1 "(2,1)" { "Call" "Fold" } 0
t "High Bet Called" 1 "Showdown" { 2 -2 }
t "High Bet Folded" 2 "P2 Folds" { 1 -1 }
p "P2 after Check" 2 2 "(2,2)" { "Bet" "Check" } 0
t "High Check-Bet" 3 "P1 Wins" { 1 -1 }
t "High Check-Check" 4 "Showdown" { 1 -1 }
p "P1 has Low" 1 2 "(1,2)" { "Bet" "Check" } 0
p "P2 after Low Bet" 2 3 "(2,3)" { "Call" "Fold" } 0
t "Low Bet Called" 5 "Showdown" { -2 2 }
t "Low Bet Folded" 6 "P2 Folds" { 1 -1 }
p "P2 after Low Check" 2 4 "(2,4)" { "Bet" "Check" } 0
t "Low Check-Bet" 7 "P2 Wins" { -1 1 }
t "Low Check-Check" 8 "Showdown" { -1 1 }"""

INVALID_NFG = """NFG 1 R "Invalid Game"
{ "Player 1" }
{ 2 }

1 2 3"""  # Wrong number of payoffs


@pytest.fixture
def sample_nfg():
    """Return sample NFG content."""
    return SAMPLE_NFG


@pytest.fixture
def sample_efg():
    """Return sample EFG content."""
    return SAMPLE_EFG


@pytest.fixture
def invalid_nfg():
    """Return invalid NFG content."""
    return INVALID_NFG


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_nfg_file(sample_nfg, temp_dir):
    """Create a temporary NFG file."""
    path = temp_dir / "test_game.nfg"
    path.write_text(sample_nfg)
    return path


@pytest.fixture
def temp_efg_file(sample_efg, temp_dir):
    """Create a temporary EFG file."""
    path = temp_dir / "test_game.efg"
    path.write_text(sample_efg)
    return path


@pytest.fixture
def mock_session_manager(temp_dir):
    """Create a SessionManager instance with temporary directory."""
    from game_ai.chat.session_manager import SessionManager
    return SessionManager(session_dir=str(temp_dir))

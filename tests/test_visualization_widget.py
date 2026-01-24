"""Tests for VisualizationWidget."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.game_ai.ui.visualization_widget import VisualizationWidget


@pytest.fixture
def mock_tree():
    """Create a mock Tree widget."""
    return Mock()


@pytest.fixture
def viz_widget(mock_tree):
    """Create a VisualizationWidget with mocked dependencies."""
    with patch('src.game_ai.ui.visualization_widget.Tree', return_value=mock_tree):
        widget = VisualizationWidget()
        return widget


def test_initialization(viz_widget):
    """Test widget initialization."""
    assert viz_widget._content == ""
    assert viz_widget._game_type is None


def test_set_content_nfg():
    """Test setting visualization with NFG content."""
    widget = VisualizationWidget()
    nfg_content = 'NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3 4'
    
    # This should not raise an error
    widget.set_content(nfg_content)
    
    assert widget._content == nfg_content
    assert widget._game_type == "NFG"


def test_set_content_efg():
    """Test setting visualization with EFG content."""
    widget = VisualizationWidget()
    efg_content = '''EFG 2 R "Test" { "P1" "P2" }
p "" 1 1 "" { "L" "R" } 0
t "" 1 { 1 2 }
t "" 2 { 3 4 }'''
    
    widget.set_content(efg_content)
    
    assert widget._content == efg_content
    assert widget._game_type == "EFG"


def test_set_content_empty():
    """Test setting visualization with empty content."""
    widget = VisualizationWidget()
    
    widget.set_content("")
    
    assert widget._content == ""
    assert widget._game_type is None


def test_set_content_invalid():
    """Test setting visualization with invalid content."""
    widget = VisualizationWidget()
    
    # Should handle gracefully without crashing
    widget.set_content("INVALID CONTENT")
    
    # State should be updated
    assert widget._content == "INVALID CONTENT"


def test_clear_visualization():
    """Test clearing the visualization."""
    widget = VisualizationWidget()
    
    # Set some content first
    widget.set_content('NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3 4')
    
    # Clear it
    widget.set_content("")
    
    assert widget._content == ""


def test_visualization_handles_pygambit_errors():
    """Test that visualization handles pygambit parsing errors gracefully."""
    widget = VisualizationWidget()
    
    # Malformed game content
    malformed_content = 'NFG 1 R "Test" { "P1" }'  # Incomplete
    
    # Should not raise exception
    try:
        widget.set_content(malformed_content)
        assert True
    except Exception as e:
        pytest.fail(f"Visualization raised exception: {e}")


def test_consecutive_updates():
    """Test multiple consecutive visualization updates."""
    widget = VisualizationWidget()
    
    # First update
    widget.set_content('NFG 1 R "Game1" { "P1" "P2" } { 2 2 } 1 2 3 4')
    assert widget._game_type == "NFG"
    
    # Second update
    widget.set_content('NFG 1 R "Game2" { "P1" "P2" } { 3 3 } 1 2 3 4 5 6 7 8 9')
    assert widget._content == 'NFG 1 R "Game2" { "P1" "P2" } { 3 3 } 1 2 3 4 5 6 7 8 9'
    
    # Switch to EFG
    efg_content = '''EFG 2 R "Game3" { "P1" "P2" }
p "" 1 1 "" { "A" "B" } 0
t "" 1 { 1 2 }
t "" 2 { 3 4 }'''
    widget.set_content(efg_content)
    assert widget._game_type == "EFG"

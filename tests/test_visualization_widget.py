"""Tests for visualization widget."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from game_ai.ui.visualization_widget import VisualizationWidget
from rich.text import Text


@pytest.mark.ui
class TestVisualizationWidget:
    """Tests for VisualizationWidget class."""
    
    def test_initialization(self):
        """Test widget initialization."""
        widget = VisualizationWidget()
        assert widget._content == ""
        assert widget._game_type is None
        assert widget._content_widget is None
    
    def test_set_content_nfg(self, sample_nfg):
        """Test setting NFG content."""
        widget = VisualizationWidget()
        # Simulate compose being called
        widget._content_widget = Mock()
        
        widget.set_content(sample_nfg)
        
        assert widget._content == sample_nfg
        assert widget._game_type == "NFG"
        # Widget should attempt to update display
        assert widget._content_widget.update.called
    
    def test_set_content_efg(self, sample_efg):
        """Test setting EFG content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content(sample_efg)
        
        assert widget._content == sample_efg
        assert widget._game_type == "EFG"
        assert widget._content_widget.update.called
    
    def test_set_content_empty(self):
        """Test setting empty content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content("")
        
        assert widget._content == ""
        # Should display "No content" message
        assert widget._content_widget.update.called
    
    def test_set_content_invalid(self):
        """Test setting invalid content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content("INVALID GAME FORMAT")
        
        # Should handle gracefully
        assert widget._content_widget.update.called
    
    def test_clear_visualization(self):
        """Test clearing visualization."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        widget.set_content("some content")
        
        widget.clear()
        
        assert widget._content == ""
        assert widget._game_type is None
    
    def test_get_player_color(self):
        """Test player color assignment."""
        widget = VisualizationWidget()
        
        # Test first few players
        assert widget._get_player_color(0) == "cyan"
        assert widget._get_player_color(1) == "magenta"
        assert widget._get_player_color(2) == "green"
        
        # Test overflow
        assert widget._get_player_color(100) == "white"
    
    def test_detect_game_type_nfg(self, sample_nfg):
        """Test game type detection for NFG."""
        widget = VisualizationWidget()
        game_type = widget._detect_game_type(sample_nfg)
        assert game_type == "NFG"
    
    def test_detect_game_type_efg(self, sample_efg):
        """Test game type detection for EFG."""
        widget = VisualizationWidget()
        game_type = widget._detect_game_type(sample_efg)
        assert game_type == "EFG"
    
    def test_detect_game_type_invalid(self):
        """Test game type detection for invalid content."""
        widget = VisualizationWidget()
        game_type = widget._detect_game_type("INVALID")
        assert game_type is None


@pytest.mark.ui
class TestVisualizationMethods:
    """Tests for visualization methods."""
    
    def test_update_visualization_nfg(self, sample_nfg):
        """Test NFG visualization update."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        # This should trigger _visualize_nfg internally
        widget.set_content(sample_nfg)
        
        # Verify update was called (actual visualization tested through integration)
        assert widget._content_widget.update.called
    
    def test_update_visualization_efg(self, sample_efg):
        """Test EFG visualization update."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content(sample_efg)
        
        assert widget._content_widget.update.called
    
    def test_update_visualization_empty(self):
        """Test visualization with empty content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content("")
        
        # Should show "No content" message
        call_args = widget._content_widget.update.call_args
        assert call_args is not None
        displayed_text = call_args[0][0]
        assert isinstance(displayed_text, Text)
    
    def test_update_visualization_invalid(self):
        """Test visualization with invalid content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content("INVALID FORMAT")
        
        # Should handle error gracefully
        assert widget._content_widget.update.called
    
    def test_consecutive_updates(self, sample_nfg, sample_efg):
        """Test consecutive content updates."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content(sample_nfg)
        assert widget._game_type == "NFG"
        
        widget.set_content(sample_efg)
        assert widget._game_type == "EFG"
        
        # Should have been called twice
        assert widget._content_widget.update.call_count >= 2
    
    def test_visualization_handles_pygambit_errors(self):
        """Test that visualization handles pygambit parsing errors."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        # Malformed game that pygambit can't parse
        bad_content = """NFG 1 R "Bad Game"
{ "Player 1" }
{ 2 }
1"""  # Missing payoffs
        
        # Should not raise exception
        widget.set_content(bad_content)
        
        # Should display error
        assert widget._content_widget.update.called

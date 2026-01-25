"""Tests for editor widget."""

import pytest
from unittest.mock import Mock, MagicMock
from game_ai.ui.editor_widget import EditorWidget


@pytest.mark.ui
class TestEditorWidget:
    """Tests for EditorWidget class."""
    
    def test_initialization(self):
        """Test widget initialization."""
        widget = EditorWidget()
        assert widget.chat_widget is None
        assert widget.visualization_widget is None
    
    def test_set_app_context(self):
        """Test setting application context."""
        widget = EditorWidget()
        chat_widget = Mock()
        viz_widget = Mock()
        
        widget.set_app_context(chat_widget, viz_widget)
        
        assert widget.chat_widget == chat_widget
        assert widget.visualization_widget == viz_widget
    
    def test_set_content(self):
        """Test setting content."""
        widget = EditorWidget()
        # Mock the query_one to return a mock TextArea
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        widget.set_content("Test content")
        
        # Should set text on the editor
        assert mock_text_area.text == "Test content"
    
    def test_get_content(self):
        """Test getting content."""
        widget = EditorWidget()
        mock_text_area = Mock()
        mock_text_area.text = "Current content"
        widget.query_one = Mock(return_value=mock_text_area)
        
        content = widget.get_content()
        
        assert content == "Current content"
    
    def test_clear_content(self):
        """Test clearing content."""
        widget = EditorWidget()
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        widget.clear()
        
        # Should set empty text
        assert mock_text_area.text == ""
    
    def test_set_content_empty(self):
        """Test setting empty content."""
        widget = EditorWidget()
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        widget.set_content("")
        
        assert mock_text_area.text == ""
    
    def test_set_content_multiline(self):
        """Test setting multiline content."""
        widget = EditorWidget()
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        content = "Line 1\nLine 2\nLine 3"
        widget.set_content(content)
        
        assert mock_text_area.text == content
    
    def test_get_content_empty(self):
        """Test getting empty content."""
        widget = EditorWidget()
        mock_text_area = Mock()
        mock_text_area.text = ""
        widget.query_one = Mock(return_value=mock_text_area)
        
        content = widget.get_content()
        
        assert content == ""
    
    def test_get_content_with_text(self):
        """Test getting content with text."""
        widget = EditorWidget()
        mock_text_area = Mock()
        mock_text_area.text = "Some game content"
        widget.query_one = Mock(return_value=mock_text_area)
        
        content = widget.get_content()
        
        assert content == "Some game content"
    
    def test_get_set_content_roundtrip(self):
        """Test setting and getting content."""
        widget = EditorWidget()
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        test_content = "NFG 1 R \"Test\"\n{ \"P1\" }\n{ 2 }\n\n1 2"
        widget.set_content(test_content)
        
        # Simulate the text area storing the content
        mock_text_area.text = test_content
        
        retrieved = widget.get_content()
        assert retrieved == test_content
    
    def test_multiple_content_updates(self):
        """Test multiple content updates."""
        widget = EditorWidget()
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        widget.set_content("First content")
        assert mock_text_area.text == "First content"
        
        widget.set_content("Second content")
        assert mock_text_area.text == "Second content"
        
        widget.set_content("Third content")
        assert mock_text_area.text == "Third content"
    
    def test_content_with_special_characters(self):
        """Test content with special characters."""
        widget = EditorWidget()
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        content = "Game with special chars: @#$%^&*()_+-=[]{}|;':\",./<>?"
        widget.set_content(content)
        
        assert mock_text_area.text == content
    
    def test_content_with_unicode(self):
        """Test content with unicode characters."""
        widget = EditorWidget()
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        content = "Game with unicode: 你好 مرحبا שלום"
        widget.set_content(content)
        
        assert mock_text_area.text == content
    
    def test_large_content(self):
        """Test handling of large content."""
        widget = EditorWidget()
        mock_text_area = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        
        # Create large content (10000 lines)
        large_content = "\n".join([f"Line {i}" for i in range(10000)])
        widget.set_content(large_content)
        
        assert mock_text_area.text == large_content


@pytest.mark.ui
class TestEditorWidgetIntegration:
    """Integration tests for EditorWidget with other components."""
    
    def test_set_content_updates_visualization(self, sample_nfg):
        """Test that setting content updates visualization widget."""
        widget = EditorWidget()
        mock_text_area = Mock()
        mock_viz = Mock()
        widget.query_one = Mock(return_value=mock_text_area)
        widget.visualization_widget = mock_viz
        
        widget.set_content(sample_nfg)
        
        # Should call visualization widget's set_content
        mock_viz.set_content.assert_called_once_with(sample_nfg)
    
    def test_set_content_updates_title_nfg(self, sample_nfg):
        """Test that setting NFG content updates title."""
        widget = EditorWidget()
        mock_text_area = Mock()
        mock_title = Mock()
        
        def query_side_effect(selector, widget_type=None):
            if selector == "#editor-area":
                return mock_text_area
            elif selector == "#editor-title":
                return mock_title
            return Mock()
        
        widget.query_one = Mock(side_effect=query_side_effect)
        
        widget.set_content(sample_nfg)
        
        # Should update title
        mock_title.update.assert_called()
        call_args = mock_title.update.call_args[0][0]
        assert "Strategic Form" in call_args or ".nfg" in call_args
    
    def test_set_content_updates_title_efg(self, sample_efg):
        """Test that setting EFG content updates title."""
        widget = EditorWidget()
        mock_text_area = Mock()
        mock_title = Mock()
        
        def query_side_effect(selector, widget_type=None):
            if selector == "#editor-area":
                return mock_text_area
            elif selector == "#editor-title":
                return mock_title
            return Mock()
        
        widget.query_one = Mock(side_effect=query_side_effect)
        
        widget.set_content(sample_efg)
        
        # Should update title
        mock_title.update.assert_called()
        call_args = mock_title.update.call_args[0][0]
        assert "Extensive Form" in call_args or ".efg" in call_args

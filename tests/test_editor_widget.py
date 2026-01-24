"""Tests for EditorWidget."""
import pytest
from unittest.mock import Mock, MagicMock
from textual.widgets import TextArea
from src.game_ai.ui.editor_widget import EditorWidget


@pytest.fixture
def mock_textarea():
    """Create a mock TextArea."""
    textarea = Mock(spec=TextArea)
    textarea.text = ""
    return textarea


@pytest.fixture
def mock_title():
    """Create a mock Static title widget."""
    title = Mock()
    title.update = Mock()
    return title


@pytest.fixture
def editor_widget(mock_textarea, mock_title, monkeypatch):
    """Create an EditorWidget with mocked TextArea."""
    widget = EditorWidget()
    # Mock the query_one method to return appropriate mocks
    def mock_query_one(selector, *args, **kwargs):
        if selector == "#editor-area":
            return mock_textarea
        elif selector == "#editor-title":
            return mock_title
        return Mock()
    
    monkeypatch.setattr(widget, 'query_one', mock_query_one)
    return widget


def test_initialization():
    """Test widget initialization."""
    widget = EditorWidget()
    assert widget.chat_widget is None
    assert widget.visualization_widget is None


def test_set_app_context(editor_widget):
    """Test setting app context."""
    mock_chat = Mock()
    mock_viz = Mock()
    
    editor_widget.set_app_context(mock_chat, mock_viz)
    
    assert editor_widget.chat_widget == mock_chat
    assert editor_widget.visualization_widget == mock_viz


def test_get_content_empty(editor_widget, mock_textarea):
    """Test getting empty content."""
    mock_textarea.text = ""
    
    content = editor_widget.get_content()
    
    assert content == ""


def test_get_content_with_text(editor_widget, mock_textarea):
    """Test getting content with text."""
    test_content = 'NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3 4'
    mock_textarea.text = test_content
    
    content = editor_widget.get_content()
    
    assert content == test_content


def test_set_content(editor_widget, mock_textarea):
    """Test setting content."""
    test_content = 'NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3 4'
    
    editor_widget.set_content(test_content)
    
    assert mock_textarea.text == test_content


def test_set_content_empty(editor_widget, mock_textarea):
    """Test setting empty content."""
    editor_widget.set_content("")
    
    assert mock_textarea.text == ""


def test_set_content_multiline(editor_widget, mock_textarea):
    """Test setting multiline content."""
    test_content = '''EFG 2 R "Test" { "P1" "P2" }
p "" 1 1 "" { "L" "R" } 0
t "" 1 { 1 2 }
t "" 2 { 3 4 }'''
    
    editor_widget.set_content(test_content)
    
    assert mock_textarea.text == test_content


def test_get_set_content_roundtrip(editor_widget, mock_textarea):
    """Test setting and getting content."""
    test_content = 'NFG 1 R "Roundtrip" { "A" "B" } { 2 2 } 5 5 0 10 10 0 5 5'
    
    editor_widget.set_content(test_content)
    mock_textarea.text = test_content  # Simulate the set
    retrieved_content = editor_widget.get_content()
    
    assert retrieved_content == test_content


def test_multiple_content_updates(editor_widget, mock_textarea):
    """Test multiple consecutive content updates."""
    content1 = "First content"
    content2 = "Second content"
    content3 = "Third content"
    
    editor_widget.set_content(content1)
    assert mock_textarea.text == content1
    
    editor_widget.set_content(content2)
    assert mock_textarea.text == content2
    
    editor_widget.set_content(content3)
    assert mock_textarea.text == content3


def test_clear_content(editor_widget, mock_textarea):
    """Test clearing content."""
    editor_widget.set_content("Some content")
    mock_textarea.text = "Some content"
    
    editor_widget.set_content("")
    
    assert mock_textarea.text == ""


def test_content_with_special_characters(editor_widget, mock_textarea):
    """Test content with special characters."""
    test_content = 'NFG 1 R "Test\'s Game" { "P1" "P2" } { 2 2 } 1.5 2.7 3.2 4.8'
    
    editor_widget.set_content(test_content)
    
    assert mock_textarea.text == test_content

"""Tests for chat widget."""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from game_ai.ui.chat_widget import ChatWidget


@pytest.mark.ui
class TestChatWidget:
    """Tests for ChatWidget class."""
    
    def test_initialization(self):
        """Test widget initialization."""
        widget = ChatWidget()
        assert widget.game_builder is None
        assert widget.command_handler is None
        assert widget.editor_widget is None
        assert widget.visualization_widget is None
        assert widget.last_editor_content == ""
    
    def test_set_app_context(self):
        """Test setting application context."""
        widget = ChatWidget()
        game_builder = Mock()
        command_handler = Mock()
        editor_widget = Mock()
        viz_widget = Mock()
        
        widget.set_app_context(game_builder, command_handler, editor_widget, viz_widget)
        
        assert widget.game_builder == game_builder
        assert widget.command_handler == command_handler
        assert widget.editor_widget == editor_widget
        assert widget.visualization_widget == viz_widget
    
    def test_start_conversation(self):
        """Test starting conversation."""
        widget = ChatWidget()
        mock_game_builder = Mock()
        mock_game_builder.start_conversation.return_value = {
            'text': 'Welcome!',
            'sources': []
        }
        widget.game_builder = mock_game_builder
        
        # Mock the display method
        widget.display_assistant_message = Mock()
        
        widget.start_conversation()
        
        mock_game_builder.start_conversation.assert_called_once()
        widget.display_assistant_message.assert_called_once()
    
    def test_display_user_message(self):
        """Test displaying user message."""
        widget = ChatWidget()
        mock_log = Mock()
        widget.query_one = Mock(return_value=mock_log)
        
        widget.display_user_message("Hello")
        
        mock_log.write.assert_called_once()
    
    def test_display_assistant_message(self):
        """Test displaying assistant message."""
        widget = ChatWidget()
        mock_log = Mock()
        widget.query_one = Mock(return_value=mock_log)
        
        widget.display_assistant_message("Hi there", sources=[])
        
        mock_log.write.assert_called_once()
    
    def test_display_system_message(self):
        """Test displaying system message."""
        widget = ChatWidget()
        mock_log = Mock()
        widget.query_one = Mock(return_value=mock_log)
        
        widget.display_system_message("System notification")
        
        mock_log.write.assert_called_once()
    
    def test_display_error_message(self):
        """Test displaying error message."""
        widget = ChatWidget()
        mock_log = Mock()
        widget.query_one = Mock(return_value=mock_log)
        
        widget.display_error_message("Error occurred")
        
        mock_log.write.assert_called_once()
    
    def test_handle_command_help(self):
        """Test handling /help command."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        mock_command_handler.handle_command.return_value = {
            'success': True,
            'message': 'Help message'
        }
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = ""
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        widget.display_system_message = Mock()
        
        widget.handle_command("/help")
        
        widget.display_system_message.assert_called_once()
    
    def test_handle_command_save(self):
        """Test handling /save command."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        mock_command_handler.handle_command.return_value = {
            'success': True,
            'message': 'Session saved'
        }
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = "NFG content"
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        widget.display_system_message = Mock()
        
        widget.handle_command("/save test")
        
        widget.display_system_message.assert_called_once()
    
    def test_handle_command_error(self):
        """Test handling command that returns error."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        mock_command_handler.handle_command.return_value = {
            'success': False,
            'message': 'Error message'
        }
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = ""
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        widget.display_error_message = Mock()
        
        widget.handle_command("/invalid")
        
        widget.display_error_message.assert_called_once()
    
    def test_load_session(self):
        """Test loading a session."""
        widget = ChatWidget()
        mock_game_builder = Mock()
        mock_editor = Mock()
        mock_viz = Mock()
        mock_log = Mock()
        
        widget.game_builder = mock_game_builder
        widget.editor_widget = mock_editor
        widget.visualization_widget = mock_viz
        widget.query_one = Mock(return_value=mock_log)
        
        session_data = {
            'conversation_history': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'game_content': 'NFG content',
            'game_type': 'nfg'
        }
        
        widget.load_session(session_data)
        
        mock_game_builder.load_conversation.assert_called_once()
        mock_editor.set_content.assert_called_once_with('NFG content')
        mock_viz.set_content.assert_called_once_with('NFG content')
    
    def test_clear_session(self):
        """Test clearing a session."""
        widget = ChatWidget()
        mock_game_builder = Mock()
        mock_game_builder.start_conversation.return_value = {
            'text': 'Welcome',
            'sources': []
        }
        mock_editor = Mock()
        mock_viz = Mock()
        mock_log = Mock()
        
        widget.game_builder = mock_game_builder
        widget.editor_widget = mock_editor
        widget.visualization_widget = mock_viz
        widget.query_one = Mock(return_value=mock_log)
        widget.display_assistant_message = Mock()
        
        widget.clear_session()
        
        mock_log.clear.assert_called_once()
        mock_editor.set_content.assert_called_once_with("")
        mock_viz.clear.assert_called_once()
    
    def test_send_command(self):
        """Test programmatic command sending."""
        widget = ChatWidget()
        widget.display_user_message = Mock()
        widget.handle_command = Mock()
        
        widget.send_command("/help")
        
        widget.display_user_message.assert_called_once_with("/help")
        widget.handle_command.assert_called_once_with("/help")


@pytest.mark.ui
class TestChatWidgetContextHandling:
    """Tests for context handling in chat widget."""
    
    def test_handle_user_message_with_file_diff(self):
        """Test handling user message with file changes."""
        widget = ChatWidget()
        mock_game_builder = Mock()
        mock_editor = Mock()
        mock_editor.get_content.return_value = "New content"
        
        widget.game_builder = mock_game_builder
        widget.editor_widget = mock_editor
        widget.last_editor_content = "Old content"
        
        widget.process_ai_response = Mock()
        
        widget.handle_user_message("Update the game")
        
        # Should detect file change and include in context
        widget.process_ai_response.assert_called_once()
    
    def test_handle_user_message_without_file_diff(self):
        """Test handling user message without file changes."""
        widget = ChatWidget()
        mock_game_builder = Mock()
        mock_editor = Mock()
        mock_editor.get_content.return_value = "Same content"
        
        widget.game_builder = mock_game_builder
        widget.editor_widget = mock_editor
        widget.last_editor_content = "Same content"
        
        widget.process_ai_response = Mock()
        
        widget.handle_user_message("Tell me more")
        
        # Should not include file diff
        widget.process_ai_response.assert_called_once()
        args = widget.process_ai_response.call_args[0]
        assert args[1] is None  # file_diff should be None
    
    def test_command_context_includes_game_content(self):
        """Test that command context includes current game content."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        mock_editor = Mock()
        mock_editor.get_content.return_value = "NFG 1 R \"Test\" { \"P1\" } { 2 }\n1 2"
        mock_game_builder = Mock()
        mock_game_builder.get_conversation_history.return_value = []
        
        widget.command_handler = mock_command_handler
        widget.editor_widget = mock_editor
        widget.game_builder = mock_game_builder
        widget.display_system_message = Mock()
        
        mock_command_handler.handle_command.return_value = {
            'success': True,
            'message': 'Done'
        }
        
        widget.handle_command("/validate")
        
        # Check that context was passed with game content
        call_args = mock_command_handler.handle_command.call_args
        context = call_args[0][1]
        assert 'game_content' in context
        assert context['game_content'].startswith("NFG")

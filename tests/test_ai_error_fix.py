"""Tests for automatic AI fix request on command errors."""

import pytest
from unittest.mock import Mock, patch
from game_ai.ui.chat_widget import ChatWidget

@pytest.mark.ui
class TestAIErrorFix:
    """Tests for automatic AI fix requests."""
    
    def test_validate_error_triggers_ai_fix(self):
        """Test that /validate error automatically triggers AI fix request."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        mock_command_handler.handle_command.return_value = {
            'success': False,
            'message': 'Syntax error at line 1'
        }
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = "NFG invalid content"
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        # Mock process_ai_response since it's a @work method
        widget.process_ai_response = Mock()
        widget.display_error_message = Mock()
        widget.display_system_message = Mock()
        
        widget.handle_command("/validate")
        
        # Should display error message
        widget.display_error_message.assert_called_with('Syntax error at line 1')
        
        # Should also trigger AI fix request
        widget.process_ai_response.assert_called_once()
        args, _ = widget.process_ai_response.call_args
        assert "Executing /validate failed" in args[0]
        assert "Syntax error at line 1" in args[0]

    def test_solve_error_triggers_ai_fix(self):
        """Test that /solve error automatically triggers AI fix request."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        mock_command_handler.handle_command.return_value = {
            'success': False,
            'message': 'Solver error: inconsistent data'
        }
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = "NFG solve fail content"
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        # Mock process_ai_response
        widget.process_ai_response = Mock()
        widget.display_error_message = Mock()
        widget.display_system_message = Mock()
        
        widget.handle_command("/solve")
        
        # Should display error message
        widget.display_error_message.assert_called_with('Solver error: inconsistent data')
        
        # Should also trigger AI fix request
        widget.process_ai_response.assert_called_once()
        args, _ = widget.process_ai_response.call_args
        assert "Executing /solve failed" in args[0]
        assert "Solver error: inconsistent data" in args[0]

    def test_other_command_error_does_not_trigger_ai_fix(self):
        """Test that errors from other commands do NOT trigger AI fix request."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        mock_command_handler.handle_command.return_value = {
            'success': False,
            'message': 'Failed to save session'
        }
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = "NFG content"
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        # Mock process_ai_response
        widget.process_ai_response = Mock()
        widget.display_error_message = Mock()
        
        widget.handle_command("/save")
        
        # Should display error message
        widget.display_error_message.assert_called_with('Failed to save session')
        
        # Should NOT trigger AI fix request
        widget.process_ai_response.assert_not_called()

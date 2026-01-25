"""Tests for automatic AI summary after /solve command."""

import pytest
from unittest.mock import Mock, patch
from game_ai.ui.chat_widget import ChatWidget

@pytest.mark.ui
class TestAISolveSummary:
    """Tests for automatic AI solution summaries."""
    
    def test_solve_success_triggers_ai_summary(self):
        """Test that successful /solve automatically triggers AI summary request."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        
        # Mock a successful solve result with summary requested
        solve_message = "## 🎯 Nash Equilibria Found\n\nEquilibrium #1: Alice: Cooperate, Bob: Cooperate"
        mock_command_handler.handle_command.return_value = {
            'success': True,
            'message': solve_message,
            'data': {
                'result': Mock(),
                'request_summary': True
            }
        }
        
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = "NFG content"
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        # Mock process_ai_response
        widget.process_ai_response = Mock()
        widget.display_system_message = Mock()
        
        widget.handle_command("/solve summary")
        
        # Should display the solve result message
        widget.display_system_message.assert_any_call(solve_message)
        
        # Should also trigger AI summary request
        widget.process_ai_response.assert_called_once()
        args, _ = widget.process_ai_response.call_args
        assert "summarize each nash equilibria found" in args[0].lower()
        assert solve_message in args[0]

    def test_solve_success_without_summary_does_not_trigger_ai_summary(self):
        """Test that /solve without summary does NOT trigger AI summary request."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        
        # Mock a successful solve result without summary requested
        solve_message = "## 🎯 Nash Equilibria Found"
        mock_command_handler.handle_command.return_value = {
            'success': True,
            'message': solve_message,
            'data': {
                'result': Mock(),
                'request_summary': False
            }
        }
        
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = "NFG content"
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        # Mock process_ai_response
        widget.process_ai_response = Mock()
        widget.display_system_message = Mock()
        
        widget.handle_command("/solve")
        
        # Should display the solve result message
        widget.display_system_message.assert_called_with(solve_message)
        
        # Should NOT trigger AI summary request
        widget.process_ai_response.assert_not_called()
        """Test that failed /solve does NOT trigger AI summary request."""
        widget = ChatWidget()
        mock_command_handler = Mock()
        mock_command_handler.handle_command.return_value = {
            'success': False,
            'message': 'Solver error'
        }
        widget.command_handler = mock_command_handler
        widget.editor_widget = Mock()
        widget.editor_widget.get_content.return_value = "NFG content"
        widget.game_builder = Mock()
        widget.game_builder.get_conversation_history.return_value = []
        
        # Mock process_ai_response
        widget.process_ai_response = Mock()
        widget.display_error_message = Mock()
        
        widget.handle_command("/solve")
        
        # Should display error message
        widget.display_error_message.assert_called_once()
        
        # Should NOT trigger AI summary request (since it failed)
        # Note: In our current implementation, failures don't trigger follow-ups for /solve, only for /fix
        widget.process_ai_response.assert_not_called()

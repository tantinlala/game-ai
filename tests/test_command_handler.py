"""Tests for command handler."""

import pytest
from unittest.mock import Mock, MagicMock
from game_ai.chat.command_handler import CommandHandler
from game_ai.chat.session_manager import SessionManager


@pytest.mark.unit
class TestCommandHandler:
    """Tests for CommandHandler class."""
    
    @pytest.fixture
    def command_handler(self, mock_session_manager):
        """Create CommandHandler instance."""
        return CommandHandler(mock_session_manager)
    
    @pytest.fixture
    def sample_context(self, sample_nfg):
        """Create sample command context."""
        return {
            'conversation_history': [
                {"role": "user", "content": "Create a game"},
                {"role": "assistant", "content": "Here's your game"}
            ],
            'game_content': sample_nfg,
            'game_type': 'nfg'
        }
    
    def test_cmd_help(self, command_handler, sample_context):
        """Test /help command."""
        result = command_handler.handle_command("/help", sample_context)
        
        assert result['success'] is True
        assert 'Available Commands' in result['message']
        assert '/solve' in result['message']
        assert '/save' in result['message']
    
    def test_cmd_save(self, command_handler, sample_context):
        """Test /save command."""
        result = command_handler.handle_command("/save test_game", sample_context)
        
        assert result['success'] is True
        assert "saved as 'test_game'" in result['message']
    
    def test_cmd_save_no_name(self, command_handler, sample_context):
        """Test /save without name."""
        result = command_handler.handle_command("/save", sample_context)
        
        assert result['success'] is False
        assert "provide a session name" in result['message']
    
    def test_cmd_load(self, command_handler, sample_context):
        """Test /load command."""
        # First save a session
        command_handler.handle_command("/save load_test", sample_context)
        
        # Then load it
        result = command_handler.handle_command("/load load_test", sample_context)
        
        assert result['success'] is True
        assert "loaded successfully" in result['message']
        assert 'data' in result
        assert result['data']['name'] == "load_test"
    
    def test_cmd_load_nonexistent(self, command_handler, sample_context):
        """Test /load with nonexistent session."""
        result = command_handler.handle_command("/load nonexistent", sample_context)
        
        assert result['success'] is False
        assert "not found" in result['message']
    
    def test_cmd_list(self, command_handler, sample_context):
        """Test /list command."""
        # Save some sessions
        command_handler.handle_command("/save session1", sample_context)
        command_handler.handle_command("/save session2", sample_context)
        
        result = command_handler.handle_command("/list", sample_context)
        
        assert result['success'] is True
        assert 'Saved Sessions' in result['message']
        assert 'session1' in result['message'] or 'session2' in result['message']
    
    def test_cmd_list_empty(self, command_handler, sample_context):
        """Test /list when no sessions exist."""
        result = command_handler.handle_command("/list", sample_context)
        
        assert result['success'] is True
        # May be empty or have sessions from other tests
    
    def test_cmd_fix_valid(self, command_handler, sample_context):
        """Test /fix with valid game."""
        result = command_handler.handle_command("/fix", sample_context)
        
        assert result['success'] is True
        assert "valid" in result['message'].lower()
    
    def test_cmd_fix_invalid(self, command_handler, invalid_nfg):
        """Test /fix with invalid game."""
        context = {
            'conversation_history': [],
            'game_content': invalid_nfg,
            'game_type': 'nfg'
        }
        
        result = command_handler.handle_command("/fix", context)
        
        assert result['success'] is False
        assert "Fix Errors" in result['message']
    
    def test_cmd_fix_no_content(self, command_handler):
        """Test /fix without game content."""
        context = {
            'conversation_history': [],
            'game_content': '',
            'game_type': None
        }
        
        result = command_handler.handle_command("/fix", context)
        
        assert result['success'] is False
        assert "No game file" in result['message']
    
    def test_cmd_solve_valid(self, command_handler, sample_context):
        """Test /solve with valid game."""
        result = command_handler.handle_command("/solve", sample_context)
        
        assert result['success'] is True
        assert "Nash Equilibria" in result['message']
    
    def test_cmd_solve_no_content(self, command_handler):
        """Test /solve without game content."""
        context = {
            'conversation_history': [],
            'game_content': '',
            'game_type': None
        }
        
        result = command_handler.handle_command("/solve", context)
        
        assert result['success'] is False
        assert "No game file" in result['message']
    
    def test_cmd_solve_with_solver_arg(self, command_handler, sample_context):
        """Test /solve with specific solver."""
        result = command_handler.handle_command("/solve enumpure", sample_context)
        
        assert result['success'] is True
    
    def test_cmd_export(self, command_handler, sample_context, temp_dir):
        """Test /export command."""
        export_path = str(temp_dir / "exported.nfg")
        result = command_handler.handle_command(f"/export {export_path}", sample_context)
        
        assert result['success'] is True
        assert "exported" in result['message'].lower()
    
    def test_cmd_export_no_path(self, command_handler, sample_context):
        """Test /export without path."""
        result = command_handler.handle_command("/export", sample_context)
        
        assert result['success'] is False
        assert "provide a file path" in result['message']
    
    def test_cmd_clear(self, command_handler, sample_context):
        """Test /clear command."""
        result = command_handler.handle_command("/clear", sample_context)
        
        assert result['success'] is True
        assert "cleared" in result['message'].lower()
        assert result['data']['action'] == 'clear'
    
    def test_unknown_command(self, command_handler, sample_context):
        """Test unknown command."""
        result = command_handler.handle_command("/unknown", sample_context)
        
        assert result['success'] is False
        assert "Unknown command" in result['message']


@pytest.mark.unit
class TestCommandParsing:
    """Tests for command parsing."""
    
    @pytest.fixture
    def command_handler(self, mock_session_manager):
        """Create CommandHandler instance."""
        return CommandHandler(mock_session_manager)
    
    @pytest.fixture
    def sample_context(self, sample_nfg):
        """Create sample command context."""
        return {
            'conversation_history': [
                {"role": "user", "content": "Create a game"},
                {"role": "assistant", "content": "Here's your game"}
            ],
            'game_content': sample_nfg,
            'game_type': 'nfg'
        }
    
    def test_command_with_args(self, command_handler, sample_context):
        """Test command with arguments."""
        result = command_handler.handle_command("/save my game name", sample_context)
        # Should parse "my game name" as single argument
        assert result['success'] is True
    
    def test_command_case_insensitive(self, command_handler, sample_context):
        """Test that commands are case insensitive."""
        result = command_handler.handle_command("/HELP", sample_context)
        assert result['success'] is True
        
        result = command_handler.handle_command("/Help", sample_context)
        assert result['success'] is True

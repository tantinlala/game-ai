"""Tests for session manager."""

import pytest
import json
from pathlib import Path
from game_ai.chat.session_manager import SessionManager


@pytest.mark.unit
class TestSessionManager:
    """Tests for SessionManager class."""
    
    def test_save_session(self, mock_session_manager):
        """Test saving a session."""
        history = [
            {"role": "user", "content": "Create a game"},
            {"role": "assistant", "content": "Sure!"}
        ]
        game_content = "NFG 1 R \"Test\" { \"P1\" }\n\n{\n{ \"A\" \"B\" }\n}\n\n{\n{ \"Outcome A\" 1 }\n{ \"Outcome B\" 2 }\n}\n1 2"
        
        success = mock_session_manager.save_session(
            name="test_session",
            conversation_history=history,
            game_content=game_content,
            game_type="nfg"
        )
        
        assert success is True
    
    def test_load_session(self, mock_session_manager):
        """Test loading a saved session."""
        # First save a session
        history = [{"role": "user", "content": "Hello"}]
        game_content = "NFG 1 R \"Test\" { \"P1\" }\n\n{\n{ \"A\" \"B\" }\n}\n\n{\n{ \"Outcome A\" 1 }\n{ \"Outcome B\" 2 }\n}\n1 2"
        
        mock_session_manager.save_session(
            name="load_test",
            conversation_history=history,
            game_content=game_content,
            game_type="nfg"
        )
        
        # Then load it
        session_data = mock_session_manager.load_session("load_test")
        
        assert session_data is not None
        assert session_data['name'] == "load_test"
        assert session_data['conversation_history'] == history
        assert session_data['game_content'] == game_content
        assert session_data['game_type'] == "nfg"
    
    def test_load_nonexistent_session(self, mock_session_manager):
        """Test loading a session that doesn't exist."""
        session_data = mock_session_manager.load_session("nonexistent")
        assert session_data is None
    
    def test_list_sessions(self, mock_session_manager):
        """Test listing all sessions."""
        # Save multiple sessions
        for i in range(3):
            mock_session_manager.save_session(
                name=f"session_{i}",
                conversation_history=[],
                game_content="",
                game_type="nfg"
            )
        
        sessions = mock_session_manager.list_sessions()
        assert len(sessions) >= 3
        
        # Check session structure
        if sessions:
            session = sessions[0]
            assert 'name' in session
            assert 'saved_at' in session
            assert 'game_type' in session
    
    def test_save_session_overwrites_existing(self, mock_session_manager):
        """Test that saving with same name overwrites."""
        mock_session_manager.save_session(
            name="overwrite_test",
            conversation_history=[{"role": "user", "content": "First"}],
            game_content="old content",
            game_type="nfg"
        )
        
        mock_session_manager.save_session(
            name="overwrite_test",
            conversation_history=[{"role": "user", "content": "Second"}],
            game_content="new content",
            game_type="efg"
        )
        
        session_data = mock_session_manager.load_session("overwrite_test")
        assert session_data['game_content'] == "new content"
        assert session_data['game_type'] == "efg"
    
    def test_save_empty_session(self, mock_session_manager):
        """Test saving session with empty content."""
        success = mock_session_manager.save_session(
            name="empty",
            conversation_history=[],
            game_content="",
            game_type=None
        )
        assert success is True
        
        session_data = mock_session_manager.load_session("empty")
        assert session_data is not None
        assert session_data['conversation_history'] == []
        assert session_data['game_content'] == ""
    
    def test_session_file_format(self, mock_session_manager):
        """Test that session files are valid JSON."""
        mock_session_manager.save_session(
            name="format_test",
            conversation_history=[{"role": "user", "content": "Test"}],
            game_content="test content",
            game_type="nfg"
        )
        
        # Read the file directly
        session_dir = Path(mock_session_manager.session_dir)
        session_file = session_dir / "format_test.json"
        
        assert session_file.exists()
        
        with open(session_file, 'r') as f:
            data = json.load(f)
        
        assert 'name' in data
        assert 'saved_at' in data
        assert 'conversation_history' in data
        assert 'game_content' in data
        assert 'game_type' in data
    
    def test_list_sessions_with_metadata(self, mock_session_manager):
        """Test that list_sessions returns proper metadata."""
        mock_session_manager.save_session(
            name="metadata_test",
            conversation_history=[],
            game_content="",
            game_type="nfg"
        )
        
        sessions = mock_session_manager.list_sessions()
        
        # Find our session
        our_session = next((s for s in sessions if s['name'] == "metadata_test"), None)
        assert our_session is not None
        assert our_session['game_type'] == "nfg"
        assert 'saved_at' in our_session
        # saved_at should be an ISO format timestamp
        assert len(our_session['saved_at']) > 0


@pytest.mark.unit
class TestExportFunction:
    """Tests for export_game_file functionality."""
    
    def test_export_game_file(self, mock_session_manager, temp_dir):
        """Test exporting a game file."""
        content = "NFG 1 R \"Test\" { \"P1\" }\n\n{\n{ \"A\" \"B\" }\n}\n\n{\n{ \"Outcome A\" 1 }\n{ \"Outcome B\" 2 }\n}\n1 2"
        export_path = temp_dir / "exported_game.nfg"
        
        success = mock_session_manager.export_game_file(
            content=content,
            filepath=str(export_path)
        )
        
        assert success is True
        assert export_path.exists()
        assert export_path.read_text() == content
    
    def test_export_creates_directories(self, mock_session_manager, temp_dir):
        """Test that export creates parent directories."""
        content = "NFG 1 R \"Test\" { \"P1\" }\n\n{\n{ \"A\" \"B\" }\n}\n\n{\n{ \"Outcome A\" 1 }\n{ \"Outcome B\" 2 }\n}\n1 2"
        export_path = temp_dir / "subdir" / "nested" / "game.nfg"
        
        success = mock_session_manager.export_game_file(
            content=content,
            filepath=str(export_path)
        )
        
        assert success is True
        assert export_path.exists()

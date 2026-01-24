"""Tests for SessionManager."""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock
from src.game_ai.chat.session_manager import SessionManager


@pytest.fixture
def temp_session_dir():
    """Create a temporary session directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def session_manager(temp_session_dir):
    """Create a SessionManager with temp directory."""
    return SessionManager(session_dir=temp_session_dir)


def test_save_session(session_manager, temp_session_dir):
    """Test saving a session."""
    conversation_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"}
    ]
    game_content = 'NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3 4'
    
    result = session_manager.save_session(
        name="test_session",
        conversation_history=conversation_history,
        game_content=game_content,
        game_type="nfg"
    )
    
    assert result == True
    # Check that the file was created
    session_file = Path(temp_session_dir) / "test_session.json"
    assert session_file.exists()


def test_load_session(session_manager):
    """Test loading a saved session."""
    # First save a session
    conversation_history = [
        {"role": "user", "content": "Test message"}
    ]
    game_content = 'NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3 4'
    
    save_result = session_manager.save_session(
        name="load_test",
        conversation_history=conversation_history,
        game_content=game_content,
        game_type="nfg"
    )
    
    # Now load it
    load_result = session_manager.load_session("load_test")
    
    assert load_result is not None
    assert load_result["conversation_history"] == conversation_history
    assert load_result["game_content"] == game_content
    assert load_result["game_type"] == "nfg"


def test_list_sessions(session_manager):
    """Test listing all sessions."""
    # Save a few sessions
    for i in range(3):
        session_manager.save_session(
            name=f"session_{i}",
            conversation_history=[],
            game_content="",
            game_type=None
        )
    
    result = session_manager.list_sessions()
    
    assert len(result) >= 3


def test_load_nonexistent_session(session_manager):
    """Test loading a session that doesn't exist."""
    result = session_manager.load_session("nonexistent_session")
    
    assert result is None


def test_save_empty_session(session_manager):
    """Test saving an empty session."""
    result = session_manager.save_session(
        name="empty",
        conversation_history=[],
        game_content="",
        game_type=None
    )
    
    assert result == True


def test_session_file_format(session_manager, temp_session_dir):
    """Test that session files are saved in JSON format."""
    session_manager.save_session(
        name="format_test",
        conversation_history=[{"role": "user", "content": "test"}],
        game_content="test content",
        game_type="nfg"
    )
    
    session_file = Path(temp_session_dir) / "format_test.json"
    assert session_file.exists()
    
    import json
    with open(session_file) as f:
        data = json.load(f)
    
    assert "conversation_history" in data
    assert "game_content" in data
    assert "game_type" in data
    assert "saved_at" in data


def test_save_session_overwrites_existing(session_manager):
    """Test that saving with same name overwrites existing session."""
    session_name = "overwrite_test"
    
    # Save first version
    session_manager.save_session(
        name=session_name,
        conversation_history=[{"role": "user", "content": "first"}],
        game_content="first content",
        game_type="nfg"
    )
    
    # Save second version with same name
    session_manager.save_session(
        name=session_name,
        conversation_history=[{"role": "user", "content": "second"}],
        game_content="second content",
        game_type="efg"
    )
    
    # Load and verify it's the second version
    result = session_manager.load_session(session_name)
    assert result["conversation_history"][0]["content"] == "second"
    assert result["game_content"] == "second content"
    assert result["game_type"] == "efg"


def test_list_sessions_with_metadata(session_manager):
    """Test that list_sessions includes metadata."""
    session_manager.save_session(
        name="metadata_test",
        conversation_history=[{"role": "user", "content": "test"}],
        game_content='NFG 1 R "Test" { "P1" "P2" } { 2 2 } 1 2 3 4',
        game_type="nfg"
    )
    
    result = session_manager.list_sessions()
    
    assert len(result) > 0
    
    # Find our session
    test_session = next((s for s in result if s["name"] == "metadata_test"), None)
    assert test_session is not None
    assert "saved_at" in test_session

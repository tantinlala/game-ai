"""Tests for CommandHandler."""
import pytest
from unittest.mock import Mock
from src.game_ai.chat.command_handler import CommandHandler
from src.game_ai.chat.session_manager import SessionManager


@pytest.fixture
def session_manager():
    """Create a mock SessionManager."""
    return Mock(spec=SessionManager)


@pytest.fixture
def command_handler(session_manager):
    """Create a CommandHandler."""
    return CommandHandler(session_manager)


def test_cmd_generate_with_no_args(command_handler):
    """Test /generate command with no arguments."""
    context = {
        "conversation_history": [],
        "game_content": "",
        "game_type": None
    }
    
    result = command_handler.cmd_generate("", context)
    
    print(f"[TEST] Result: {result}")
    
    assert result["success"] == True
    assert "data" in result
    assert result["data"]["action"] == "generate"
    assert "generate the complete game file" in result["data"]["prompt"].lower()


def test_cmd_generate_with_custom_prompt(command_handler):
    """Test /generate command with custom prompt."""
    context = {
        "conversation_history": [],
        "game_content": "",
        "game_type": None
    }
    
    custom_prompt = "Make the game more balanced"
    result = command_handler.cmd_generate(custom_prompt, context)
    
    print(f"[TEST] Result with custom prompt: {result}")
    
    assert result["success"] == True
    assert result["data"]["prompt"] == custom_prompt


def test_handle_command_generate(command_handler):
    """Test handling /generate command through handle_command."""
    context = {
        "conversation_history": [
            {"role": "user", "content": "Create a prisoner's dilemma game"}
        ],
        "game_content": "",
        "game_type": None
    }
    
    result = command_handler.handle_command("/generate", context)
    
    print(f"[TEST] handle_command result: {result}")
    
    assert result["success"] == True
    assert result["data"]["action"] == "generate"

"""Tests for GameBuilder."""
import pytest
from unittest.mock import Mock, patch
from src.game_ai.ai.game_builder import GameBuilder


@pytest.fixture
def mock_client():
    """Create a mock GeminiClient."""
    return Mock()


@pytest.fixture
def game_builder(mock_client):
    """Create a GameBuilder with mocked client."""
    with patch('src.game_ai.ai.game_builder.GeminiClient', return_value=mock_client):
        return GameBuilder(api_key="test_key")


def test_send_message_with_generate_game_file(game_builder, mock_client):
    """Test send_message with generate_game_file=True."""
    # Setup mock response from client
    mock_client.generate_response.return_value = {
        "text": "Here is your game",
        "game_file": "NFG 1 R \"Prisoner's Dilemma\" { \"P1\" \"P2\" } { 2 2 } 3 0 5 1 5 1 3 0",
        "sources": [],
        "grounding_metadata": None
    }
    
    # Add initial message to conversation history
    game_builder.conversation_history = [
        {"role": "user", "content": "Create a prisoner's dilemma game"}
    ]
    
    # Call send_message with generate_game_file=True
    response = game_builder.send_message(
        user_message="Generate or update the game file based on our conversation.",
        generate_game_file=True,
        use_temp_history=False
    )
    
    print(f"[TEST] Response: {response}")
    print(f"[TEST] Response keys: {list(response.keys())}")
    print(f"[TEST] file_content: {response.get('file_content', 'NOT PRESENT')}")
    print(f"[TEST] current_game_content: {game_builder.current_game_content}")
    
    # Verify the response
    assert "file_content" in response
    assert response["file_content"].startswith("NFG")
    assert len(response["file_content"]) > 0
    
    # Verify game_builder state
    assert game_builder.current_game_content.startswith("NFG")
    assert game_builder.game_type == "nfg"
    
    # Verify client was called with correct parameters
    mock_client.generate_response.assert_called_once()
    call_args = mock_client.generate_response.call_args
    assert call_args.kwargs["use_structured_output"] == True
    assert call_args.kwargs["use_grounding"] == False


def test_send_message_without_generate_game_file(game_builder, mock_client):
    """Test send_message with generate_game_file=False (chat mode)."""
    # Setup mock response from client
    mock_client.generate_response.return_value = {
        "text": "Game theory studies strategic interactions",
        "sources": [{"url": "example.com"}]
    }
    
    # Call send_message with generate_game_file=False
    response = game_builder.send_message(
        user_message="What is game theory?",
        generate_game_file=False
    )
    
    print(f"[TEST] Chat response: {response}")
    
    # Verify the response
    assert "text" in response
    assert response["text"] == "Game theory studies strategic interactions"
    
    # Verify client was called with correct parameters
    mock_client.generate_response.assert_called_once()
    call_args = mock_client.generate_response.call_args
    assert call_args.kwargs["use_structured_output"] == False
    assert call_args.kwargs["use_grounding"] == True


def test_send_message_with_empty_game_file(game_builder, mock_client):
    """Test handling when API returns empty game_file."""
    # Setup mock response with empty game_file
    mock_client.generate_response.return_value = {
        "text": "I need more details",
        "game_file": "",
        "sources": [],
        "grounding_metadata": None
    }
    
    game_builder.conversation_history = [
        {"role": "user", "content": "Generate a game"}
    ]
    
    # Call send_message
    response = game_builder.send_message(
        user_message="Generate or update the game file based on our conversation.",
        generate_game_file=True
    )
    
    print(f"[TEST] Response with empty game_file: {response}")
    print(f"[TEST] file_content present: {'file_content' in response}")
    print(f"[TEST] file_content value: '{response.get('file_content', 'NOT PRESENT')}'")
    
    # Verify the response - file_content should be empty or not updated
    assert "file_content" in response
    # Current implementation doesn't update current_game_content if game_file is empty
    assert game_builder.current_game_content == ""


def test_send_message_with_temp_history(game_builder, mock_client):
    """Test send_message using temporary history."""
    # Setup mock response
    mock_client.generate_response.return_value = {
        "text": "Fixed game",
        "game_file": "NFG 1 R \"Fixed\" { \"P1\" \"P2\" } { 2 2 } 1 2 3 4",
        "sources": [],
        "grounding_metadata": None
    }
    
    # Add some context to main history
    game_builder.conversation_history = [
        {"role": "user", "content": "Create a game about competition"},
        {"role": "assistant", "content": "I'll create a game"},
    ]
    
    # Call with temp history
    response = game_builder.send_message(
        user_message="Fix the validation errors",
        generate_game_file=True,
        use_temp_history=True
    )
    
    print(f"[TEST] Response with temp history: {response}")
    print(f"[TEST] Main history length: {len(game_builder.conversation_history)}")
    print(f"[TEST] Temp history length: {len(game_builder.temp_conversation_history)}")
    
    # Verify temp history was initialized and used
    assert len(game_builder.temp_conversation_history) > 0
    # Main history should not be modified
    assert len(game_builder.conversation_history) == 2


def test_conversation_history_structure(game_builder, mock_client):
    """Test that conversation history is properly maintained."""
    # Setup mock responses
    mock_client.generate_response.return_value = {
        "text": "Here is your game",
        "game_file": "NFG 1 R \"Test\" { \"P1\" \"P2\" } { 2 2 } 1 2 3 4",
        "sources": [],
        "grounding_metadata": None
    }
    
    # Initial message
    game_builder.send_message("Create a 2x2 game", generate_game_file=True)
    
    print(f"[TEST] History after message: {game_builder.conversation_history}")
    print(f"[TEST] History length: {len(game_builder.conversation_history)}")
    
    # Verify history structure
    assert len(game_builder.conversation_history) == 2  # user + assistant
    assert game_builder.conversation_history[0]["role"] == "user"
    assert game_builder.conversation_history[1]["role"] == "assistant"


def test_game_builder_handles_none_game_file(game_builder, mock_client):
    """Test that GameBuilder handles None game_file values without crashing."""
    # Mock response with None game_file
    mock_client.generate_response.return_value = {
        "text": "Here's your game",
        "game_file": None,  # This should not cause len() to crash
        "sources": []
    }
    
    # This should not raise an error
    result = game_builder.send_message("Create a game", generate_game_file=True)
    
    assert result["text"] == "Here's your game"
    assert result["file_content"] == ""


def test_game_builder_handles_empty_game_file(game_builder, mock_client):
    """Test that GameBuilder handles empty string game_file."""
    # Mock response with empty game_file
    mock_client.generate_response.return_value = {
        "text": "Here's your game",
        "game_file": "",
        "sources": []
    }
    
    result = game_builder.send_message("Create a game", generate_game_file=True)
    
    assert result["text"] == "Here's your game"
    assert result["file_content"] == ""


def test_game_builder_handles_whitespace_only_game_file(game_builder, mock_client):
    """Test that GameBuilder handles whitespace-only game_file."""
    # Mock response with whitespace-only game_file
    mock_client.generate_response.return_value = {
        "text": "Here's your game",
        "game_file": "   \n\t   ",
        "sources": []
    }
    
    result = game_builder.send_message("Create a game", generate_game_file=True)
    
    # Should not update file_content with whitespace-only content
    assert result["text"] == "Here's your game"
    assert result["file_content"] == ""

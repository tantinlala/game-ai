"""Tests for GeminiClient."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.game_ai.ai.gemini_client import GeminiClient


@pytest.fixture
def mock_genai():
    """Mock the google.genai module."""
    with patch('src.game_ai.ai.gemini_client.genai') as mock:
        # Mock the client.models.generate_content call chain
        mock_client_instance = Mock()
        mock_models = Mock()
        mock_client_instance.models = mock_models
        mock.Client.return_value = mock_client_instance
        yield mock


@pytest.fixture
def client(mock_genai):
    """Create a GeminiClient with mocked API."""
    return GeminiClient(api_key="test_key")


def test_generate_response_with_structured_output(client, mock_genai):
    """Test that structured output returns game_file field."""
    # Mock the API response with proper text attribute
    mock_response = Mock()
    mock_response.text = '{"message": "Here is your game", "game_file": "NFG 1 R \\"Test\\" { \\"P1\\" \\"P2\\" } { 2 2 } 1 2 3 4"}'
    mock_response.candidates = []
    
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response
    
    # Call with structured output enabled
    messages = [{"role": "user", "content": "Generate a 2x2 game"}]
    response = client.generate_response(
        messages=messages,
        system_prompt="You are a game theory assistant",
        use_structured_output=True
    )
    
    print(f"[TEST] Response: {response}")
    
    # Verify response structure
    assert "text" in response
    assert "game_file" in response
    assert response["game_file"].startswith("NFG")
    assert len(response["game_file"]) > 0


def test_generate_response_without_structured_output(client, mock_genai):
    """Test normal chat response without structured output."""
    # Mock the API response
    mock_response = Mock()
    mock_response.text = "This is a normal chat response"
    mock_response.candidates = []
    
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response
    
    # Call with grounding enabled
    messages = [{"role": "user", "content": "Tell me about game theory"}]
    response = client.generate_response(
        messages=messages,
        system_prompt="You are a game theory assistant",
        use_grounding=True
    )
    
    print(f"[TEST] Response: {response}")
    
    # Verify response structure
    assert "text" in response
    assert "sources" in response
    assert response["text"] == "This is a normal chat response"


def test_structured_output_with_empty_game_file(client, mock_genai):
    """Test handling of empty game_file in structured output."""
    # Mock the API response with empty game_file
    mock_response = Mock()
    mock_response.text = '{"message": "I need more information", "game_file": ""}'
    mock_response.candidates = []
    
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response
    
    # Call with structured output enabled
    messages = [{"role": "user", "content": "Generate a game"}]
    response = client.generate_response(
        messages=messages,
        system_prompt="You are a game theory assistant",
        use_structured_output=True
    )
    
    print(f"[TEST] Response with empty game_file: {response}")
    
    # Verify response structure
    assert "text" in response
    assert "game_file" in response
    assert response["game_file"] == ""


def test_structured_output_with_null_game_file(client, mock_genai):
    """Test handling of null game_file in structured output."""
    # Mock the API response with null game_file
    mock_response = Mock()
    mock_response.text = '{"message": "I need more information", "game_file": null}'
    mock_response.candidates = []
    
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response
    
    # Call with structured output enabled
    messages = [{"role": "user", "content": "Generate a game"}]
    response = client.generate_response(
        messages=messages,
        system_prompt="You are a game theory assistant",
        use_structured_output=True
    )
    
    print(f"[TEST] Response with null game_file: {response}")
    
    # Verify response structure
    assert "text" in response
    assert "game_file" in response
    assert response["game_file"] is None or response["game_file"] == ""


def test_gemini_client_handles_none_grounding_chunks(client, mock_genai):
    """Test that GeminiClient handles None grounding_chunks without crashing."""
    # Create a mock response with None grounding_chunks
    mock_response = Mock()
    mock_response.text = "Test response"
    mock_response.candidates = [Mock()]
    
    mock_metadata = Mock()
    mock_metadata.grounding_chunks = None  # This should not cause iteration error
    
    mock_response.candidates[0].grounding_metadata = mock_metadata
    
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response
    
    result = client.generate_response(
        messages=[{"role": "user", "content": "test"}],
        use_grounding=True
    )
    
    # Should not crash and should return empty sources
    assert result["text"] == "Test response"
    assert result["sources"] == []


def test_gemini_client_handles_empty_grounding_chunks(client, mock_genai):
    """Test that GeminiClient handles empty list grounding_chunks."""
    # Create a mock response with empty grounding_chunks list
    mock_response = Mock()
    mock_response.text = "Test response"
    mock_response.candidates = [Mock()]
    
    mock_metadata = Mock()
    mock_metadata.grounding_chunks = []  # Empty list
    
    mock_response.candidates[0].grounding_metadata = mock_metadata
    
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response
    
    result = client.generate_response(
        messages=[{"role": "user", "content": "test"}],
        use_grounding=True
    )
    
    assert result["text"] == "Test response"
    assert result["sources"] == []


def test_gemini_client_handles_valid_grounding_chunks(client, mock_genai):
    """Test that GeminiClient properly extracts sources from grounding_chunks."""
    # Create a mock response with valid grounding_chunks
    mock_response = Mock()
    mock_response.text = "Test response"
    mock_response.candidates = [Mock()]
    
    mock_web = Mock()
    mock_web.title = "Test Article"
    mock_web.uri = "https://example.com"
    
    mock_chunk = Mock()
    mock_chunk.web = mock_web
    
    mock_metadata = Mock()
    mock_metadata.grounding_chunks = [mock_chunk]
    
    mock_response.candidates[0].grounding_metadata = mock_metadata
    
    mock_genai.Client.return_value.models.generate_content.return_value = mock_response
    
    result = client.generate_response(
        messages=[{"role": "user", "content": "test"}],
        use_grounding=True
    )
    
    assert result["text"] == "Test response"
    assert len(result["sources"]) == 1
    assert result["sources"][0]["title"] == "Test Article"
    assert result["sources"][0]["uri"] == "https://example.com"

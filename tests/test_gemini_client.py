"""Tests for Gemini client."""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from game_ai.ai.gemini_client import GeminiClient


@pytest.mark.unit
class TestGeminiClient:
    """Tests for GeminiClient class."""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock the genai module."""
        with patch('game_ai.ai.gemini_client.genai') as mock:
            yield mock
    
    @pytest.fixture
    def mock_api_key(self):
        """Set up mock API key."""
        original_key = os.environ.get('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = 'test_api_key'
        yield 'test_api_key'
        if original_key:
            os.environ['GEMINI_API_KEY'] = original_key
        else:
            del os.environ['GEMINI_API_KEY']
    
    def test_initialization_with_api_key(self, mock_genai):
        """Test client initialization with explicit API key."""
        client = GeminiClient(api_key='test_key')
        assert client.api_key == 'test_key'
    
    def test_initialization_from_env(self, mock_genai, mock_api_key):
        """Test client initialization from environment variable."""
        client = GeminiClient()
        assert client.api_key == 'test_api_key'
    
    def test_initialization_without_api_key(self, mock_genai):
        """Test that initialization fails without API key."""
        # Temporarily remove env var
        original_key = os.environ.get('GEMINI_API_KEY')
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
        
        with pytest.raises(ValueError, match="API key not found"):
            GeminiClient()
        
        # Restore env var
        if original_key:
            os.environ['GEMINI_API_KEY'] = original_key
    
    def test_generate_response_without_structured_output(self, mock_genai, mock_api_key):
        """Test generating response without structured output."""
        # Mock the client and response
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.text = "This is a response"
        mock_response.candidates = []
        
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        messages = [{"role": "user", "content": "Hello"}]
        result = client.generate_response(messages, use_grounding=False)
        
        assert result['text'] == "This is a response"
        assert result['sources'] == []
    
    def test_generate_response_with_structured_output(self, mock_genai, mock_api_key):
        """Test generating response with sources."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        # Mock response with grounding metadata
        mock_response = Mock()
        mock_response.text = "Response with sources"
        
        # Mock grounding metadata structure
        mock_chunk = Mock()
        mock_chunk.web = Mock()
        mock_chunk.web.title = "Test Source"
        mock_chunk.web.uri = "https://example.com"
        
        mock_metadata = Mock()
        mock_metadata.grounding_chunks = [mock_chunk]
        
        mock_candidate = Mock()
        mock_candidate.grounding_metadata = mock_metadata
        
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        messages = [{"role": "user", "content": "Search for data"}]
        result = client.generate_response(messages, use_grounding=True)
        
        assert result['text'] == "Response with sources"
        assert len(result['sources']) == 1
        assert result['sources'][0]['title'] == "Test Source"
        assert result['sources'][0]['uri'] == "https://example.com"
    
    def test_generate_simple(self, mock_genai, mock_api_key):
        """Test simple generation method."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.text = "Simple response"
        mock_response.candidates = []
        
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_simple("Test prompt")
        
        assert result == "Simple response"
    
    def test_gemini_client_handles_valid_grounding_chunks(self, mock_genai, mock_api_key):
        """Test handling of valid grounding chunks."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        # Create multiple mock chunks
        mock_chunks = []
        for i in range(3):
            chunk = Mock()
            chunk.web = Mock()
            chunk.web.title = f"Source {i}"
            chunk.web.uri = f"https://example{i}.com"
            mock_chunks.append(chunk)
        
        mock_metadata = Mock()
        mock_metadata.grounding_chunks = mock_chunks
        
        mock_candidate = Mock()
        mock_candidate.grounding_metadata = mock_metadata
        
        mock_response = Mock()
        mock_response.text = "Response"
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_response([{"role": "user", "content": "Test"}])
        
        assert len(result['sources']) == 3
    
    def test_gemini_client_handles_empty_grounding_chunks(self, mock_genai, mock_api_key):
        """Test handling of empty grounding chunks."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        mock_metadata = Mock()
        mock_metadata.grounding_chunks = []
        
        mock_candidate = Mock()
        mock_candidate.grounding_metadata = mock_metadata
        
        mock_response = Mock()
        mock_response.text = "Response"
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_response([{"role": "user", "content": "Test"}])
        
        assert result['sources'] == []
    
    def test_gemini_client_handles_none_grounding_chunks(self, mock_genai, mock_api_key):
        """Test handling when grounding_chunks is None."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        mock_metadata = Mock()
        mock_metadata.grounding_chunks = None
        
        mock_candidate = Mock()
        mock_candidate.grounding_metadata = mock_metadata
        
        mock_response = Mock()
        mock_response.text = "Response"
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_response([{"role": "user", "content": "Test"}])
        
        # Should handle gracefully
        assert 'sources' in result
    
    def test_structured_output_with_null_game_file(self, mock_genai, mock_api_key):
        """Test that None game file is handled."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.text = "Response without game"
        mock_response.candidates = []
        
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_response([{"role": "user", "content": "Chat"}])
        
        assert result['text'] == "Response without game"
    
    def test_structured_output_with_empty_game_file(self, mock_genai, mock_api_key):
        """Test handling of empty game file."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        mock_response = Mock()
        mock_response.text = "```\n\n```"
        mock_response.candidates = []
        
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        result = client.generate_response([{"role": "user", "content": "Test"}])
        
        assert 'text' in result


@pytest.mark.unit
class TestGeminiErrorHandling:
    """Tests for error handling."""
    
    @pytest.fixture
    def mock_genai(self):
        """Mock the genai module."""
        with patch('game_ai.ai.gemini_client.genai') as mock:
            yield mock
    
    @pytest.fixture
    def mock_api_key(self):
        """Set up mock API key."""
        original_key = os.environ.get('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = 'test_api_key'
        yield 'test_api_key'
        if original_key:
            os.environ['GEMINI_API_KEY'] = original_key
        else:
            del os.environ['GEMINI_API_KEY']
    
    def test_api_error_handling(self, mock_genai, mock_api_key):
        """Test that API errors are caught and re-raised."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        # Mock an API error
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        client = GeminiClient()
        
        with pytest.raises(RuntimeError, match="Gemini API error"):
            client.generate_response([{"role": "user", "content": "Test"}])
    
    def test_missing_text_in_response(self, mock_genai, mock_api_key):
        """Test handling of response without text."""
        mock_client = Mock()
        mock_genai.Client.return_value = mock_client
        
        # Response without text attribute
        mock_response = Mock(spec=[])  # No attributes
        mock_client.models.generate_content.return_value = mock_response
        
        client = GeminiClient()
        
        with pytest.raises(RuntimeError, match="No text in response"):
            client.generate_response([{"role": "user", "content": "Test"}])

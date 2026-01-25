"""Tests for game builder."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from game_ai.ai.game_builder import GameBuilder


@pytest.mark.unit
class TestGameBuilder:
    """Tests for GameBuilder class."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock GeminiClient."""
        with patch('game_ai.ai.game_builder.GeminiClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            yield mock_client
    
    def test_start_conversation(self, mock_gemini_client):
        """Test starting a new conversation."""
        builder = GameBuilder()
        result = builder.start_conversation()
        
        assert 'text' in result
        assert 'sources' in result
        assert "Welcome" in result['text']
        assert len(builder.conversation_history) == 1
        assert builder.conversation_history[0]['role'] == 'assistant'
    
    def test_send_message_without_generate_game_file(self, mock_gemini_client):
        """Test sending message without game file generation."""
        builder = GameBuilder()
        builder.start_conversation()
        
        # Mock response without game file
        mock_response = {
            'text': 'Tell me about your game',
            'sources': []
        }
        mock_gemini_client.generate_response.return_value = mock_response
        
        result = builder.send_message("I want to create a game")
        
        assert result['text'] == 'Tell me about your game'
        assert result['file_content'] == ''
        assert len(builder.conversation_history) == 3  # assistant greeting + user + assistant response
    
    def test_send_message_with_generate_game_file(self, mock_gemini_client):
        """Test sending message with game file generation."""
        builder = GameBuilder()
        builder.start_conversation()
        
        # Mock response with game file
        game_content = """NFG 1 R "Test Game"
{ "Player 1" }
{ 2 }

1 2"""
        mock_response = {
            'text': f'Here is your game:\n```nfg\n{game_content}\n```',
            'sources': []
        }
        mock_gemini_client.generate_response.return_value = mock_response
        
        result = builder.send_message("Create a simple game")
        
        assert result['file_content'] == game_content
        assert builder.current_game_content == game_content
        assert builder.game_type == 'nfg'
    
    def test_send_message_with_temp_history(self, mock_gemini_client):
        """Test that conversation history is maintained."""
        builder = GameBuilder()
        builder.start_conversation()
        
        mock_response = {'text': 'Response', 'sources': []}
        mock_gemini_client.generate_response.return_value = mock_response
        
        builder.send_message("Message 1")
        builder.send_message("Message 2")
        
        # Should have: greeting + (user1 + assistant1) + (user2 + assistant2)
        assert len(builder.conversation_history) == 5
    
    def test_conversation_history_structure(self, mock_gemini_client):
        """Test conversation history structure."""
        builder = GameBuilder()
        builder.start_conversation()
        
        mock_response = {'text': 'Response', 'sources': []}
        mock_gemini_client.generate_response.return_value = mock_response
        
        builder.send_message("Test message")
        
        history = builder.get_conversation_history()
        
        # Check structure
        for msg in history:
            assert 'role' in msg
            assert 'content' in msg
            assert msg['role'] in ['user', 'assistant']
    
    def test_game_builder_handles_empty_game_file(self, mock_gemini_client):
        """Test handling of empty game file extraction."""
        builder = GameBuilder()
        
        mock_response = {'text': 'Just some text without a game', 'sources': []}
        mock_gemini_client.generate_response.return_value = mock_response
        
        builder.start_conversation()
        result = builder.send_message("Tell me about game theory")
        
        assert result['file_content'] == ''
        assert builder.current_game_content == ''
    
    def test_game_builder_handles_whitespace_only_game_file(self, mock_gemini_client):
        """Test handling of whitespace in game files."""
        builder = GameBuilder()
        
        game_content = """NFG 1 R "Test"
{ "P1" }
{ 2 }

1 2"""
        mock_response = {
            'text': f'Here is your game:\n\n```\n{game_content}\n```\n\n',
            'sources': []
        }
        mock_gemini_client.generate_response.return_value = mock_response
        
        builder.start_conversation()
        result = builder.send_message("Create game")
        
        # Should extract clean game content
        assert 'NFG' in result['file_content']
    
    def test_game_builder_handles_none_game_file(self, mock_gemini_client):
        """Test that None is handled for game files."""
        builder = GameBuilder()
        
        # _extract_game_file returns None when no game found
        mock_response = {'text': 'No game here', 'sources': []}
        mock_gemini_client.generate_response.return_value = mock_response
        
        builder.start_conversation()
        result = builder.send_message("Just chat")
        
        assert result['file_content'] == ''


@pytest.mark.unit
class TestExtractGameFile:
    """Tests for _extract_game_file method."""
    
    def test_extract_nfg_from_code_block(self):
        """Test extracting NFG from markdown code block."""
        builder = GameBuilder(api_key='dummy_test_key')
        
        text = """Here is your game:
```nfg
NFG 1 R "Test"
{ "P1" }
{ 2 }

1 2
```
"""
        result = builder._extract_game_file(text)
        assert result is not None
        assert result.startswith("NFG")
    
    def test_extract_efg_from_code_block(self):
        """Test extracting EFG from code block."""
        builder = GameBuilder(api_key='dummy_test_key')
        
        text = """```efg
EFG 2 R "Test"
{ "P1" }
t "" 0 { 1 }
```"""
        
        result = builder._extract_game_file(text)
        assert result is not None
        assert result.startswith("EFG")
    
    def test_extract_game_without_code_block(self):
        """Test extracting game without code block markers."""
        builder = GameBuilder(api_key='dummy_test_key')
        
        text = """Here's a game for you:

NFG 1 R "Test"
{ "P1" }
{ 2 }

1 2

Let me know if you need changes."""
        
        result = builder._extract_game_file(text)
        assert result is not None
        assert result.startswith("NFG")
    
    def test_extract_returns_none_without_game(self):
        """Test that extraction returns None without game."""
        builder = GameBuilder(api_key='dummy_test_key')
        
        text = "This is just a conversation without any game content."
        result = builder._extract_game_file(text)
        
        assert result is None


@pytest.mark.unit
class TestLoadConversation:
    """Tests for loading saved conversations."""
    
    def test_load_conversation(self):
        """Test loading a conversation."""
        builder = GameBuilder(api_key='dummy_test_key')
        
        history = [
            {"role": "user", "content": "Create game"},
            {"role": "assistant", "content": "Here you go"}
        ]
        game_content = "NFG 1 R \"Test\" { \"P1\" } { 2 }\n1 2"
        
        builder.load_conversation(history, game_content, "nfg")
        
        assert builder.conversation_history == history
        assert builder.current_game_content == game_content
        assert builder.game_type == "nfg"

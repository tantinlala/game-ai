"""Tests for ChatWidget validation loop functionality."""

import pytest
from game_ai.ui.chat_widget import ChatWidget
from game_ai.game.validator import ValidationError


def test_handle_validation_result_no_errors():
    """Test that handle_validation_result returns correct result when no errors."""
    widget = ChatWidget()
    
    result = widget.handle_validation_result('valid content', [], max_validation_attempts=3)
    
    assert result['should_retry'] is False
    assert result['error_text'] == ''
    assert result['fix_prompt'] == ''
    assert result['attempt_number'] == 0


def test_handle_validation_result_with_retry():
    """Test that handle_validation_result returns retry when errors and attempts remain."""
    widget = ChatWidget()
    errors = [ValidationError("Test error")]
    
    result = widget.handle_validation_result('invalid content', errors, max_validation_attempts=3)
    
    assert result['should_retry'] is True
    assert 'Test error' in result['error_text']
    assert 'validation errors' in result['fix_prompt']
    assert 'invalid content' in result['fix_prompt']
    assert result['attempt_number'] == 1  # First attempt (4 - 3 = 1)


def test_handle_validation_result_max_attempts_reached():
    """Test that handle_validation_result doesn't retry when max attempts reached."""
    widget = ChatWidget()
    errors = [ValidationError("Persistent error")]
    
    result = widget.handle_validation_result('invalid content', errors, max_validation_attempts=0)
    
    assert result['should_retry'] is False
    assert 'max attempts reached' in result['error_text']
    assert 'Persistent error' in result['error_text']
    assert result['fix_prompt'] == ''
    # When max_validation_attempts=0, we've already tried 3 times, so attempt_number=4
    assert result['attempt_number'] == 4


def test_handle_validation_result_attempt_number_calculation():
    """Test that attempt numbers are correctly calculated."""
    widget = ChatWidget()
    errors = [ValidationError("Error")]
    
    # Attempt 1: max_validation_attempts=3 -> attempt 1/3
    result = widget.handle_validation_result('content', errors, max_validation_attempts=3)
    assert result['attempt_number'] == 1
    
    # Attempt 2: max_validation_attempts=2 -> attempt 2/3
    result = widget.handle_validation_result('content', errors, max_validation_attempts=2)
    assert result['attempt_number'] == 2
    
    # Attempt 3: max_validation_attempts=1 -> attempt 3/3
    result = widget.handle_validation_result('content', errors, max_validation_attempts=1)
    assert result['attempt_number'] == 3


def test_handle_validation_result_multiple_errors():
    """Test that handle_validation_result formats multiple errors correctly."""
    widget = ChatWidget()
    errors = [
        ValidationError("First error"),
        ValidationError("Second error"),
        ValidationError("Third error")
    ]
    
    result = widget.handle_validation_result('invalid', errors, max_validation_attempts=3)
    
    assert result['should_retry'] is True
    # All errors should be in error_text
    assert 'First error' in result['error_text']
    assert 'Second error' in result['error_text']
    assert 'Third error' in result['error_text']
    # All errors should be in fix_prompt
    assert 'First error' in result['fix_prompt']
    assert 'Second error' in result['fix_prompt']
    assert 'Third error' in result['fix_prompt']


def test_handle_validation_result_error_text_format():
    """Test that error text is properly formatted with bullets."""
    widget = ChatWidget()
    errors = [
        ValidationError("Error one"),
        ValidationError("Error two")
    ]
    
    result = widget.handle_validation_result('content', errors, max_validation_attempts=3)
    
    # Should have header
    assert 'Validation Errors Found' in result['error_text']
    # Should have bullet points
    assert '•' in result['error_text']


def test_handle_validation_result_fix_prompt_format():
    """Test that fix prompt has correct structure."""
    widget = ChatWidget()
    errors = [ValidationError("Syntax error")]
    file_content = 'NFG 1 R "Test"\n{ "P1" "P2" }\n'
    
    result = widget.handle_validation_result(file_content, errors, max_validation_attempts=2)
    
    fix_prompt = result['fix_prompt']
    # Should mention validation errors
    assert 'validation errors' in fix_prompt.lower()
    # Should include the error details
    assert 'Syntax error' in fix_prompt
    # Should include the file content
    assert file_content in fix_prompt
    # Should ask for corrected version
    assert 'corrected' in fix_prompt.lower() or 'fix' in fix_prompt.lower()

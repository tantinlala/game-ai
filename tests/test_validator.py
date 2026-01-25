"""Tests for game file validator."""

import pytest
from game_ai.game.validator import GameValidator, ValidationError


@pytest.mark.unit
class TestGameValidator:
    """Tests for GameValidator class."""
    
    def test_validate_valid_nfg(self, sample_nfg):
        """Test validation of valid NFG file."""
        errors = GameValidator.validate(sample_nfg)
        assert len(errors) == 0, "Valid NFG should have no errors"
    
    def test_validate_valid_efg(self, sample_efg):
        """Test validation of valid EFG file."""
        errors = GameValidator.validate(sample_efg)
        assert len(errors) == 0, "Valid EFG should have no errors"
    
    def test_validate_empty_file(self):
        """Test validation of empty file."""
        errors = GameValidator.validate("")
        assert len(errors) == 1
        assert "Empty file" in str(errors[0])
    
    def test_validate_whitespace_only(self):
        """Test validation of whitespace-only file."""
        errors = GameValidator.validate("   \n  \t  ")
        assert len(errors) == 1
        assert "Empty file" in str(errors[0])
    
    def test_validate_invalid_format(self):
        """Test validation of file with unknown format."""
        content = "INVALID GAME FORMAT\n{ }"
        errors = GameValidator.validate(content)
        assert len(errors) == 1
        assert "Unknown file format" in str(errors[0])
    
    def test_validate_malformed_nfg(self, invalid_nfg):
        """Test validation of malformed NFG file."""
        errors = GameValidator.validate(invalid_nfg)
        assert len(errors) > 0, "Invalid NFG should have errors"
    
    def test_validate_nfg_missing_payoffs(self):
        """Test NFG with missing payoffs."""
        content = """NFG 1 R "Incomplete Game"
{ "Player 1" "Player 2" }
{ 2 2 }

1 1 0"""  # Missing payoffs
        errors = GameValidator.validate(content)
        assert len(errors) > 0
    
    def test_validation_error_string_representation(self):
        """Test ValidationError string representation."""
        error = ValidationError("Test error message")
        assert str(error) == "Test error message"


@pytest.mark.unit
class TestLegacyMethods:
    """Tests for legacy validation methods."""
    
    def test_validate_nfg_method(self, sample_nfg):
        """Test validate_nfg legacy method."""
        errors = GameValidator.validate_nfg(sample_nfg)
        assert len(errors) == 0
    
    def test_validate_efg_method(self, sample_efg):
        """Test validate_efg legacy method."""
        errors = GameValidator.validate_efg(sample_efg)
        assert len(errors) == 0

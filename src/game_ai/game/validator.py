"""Game file validator."""

import tempfile
import os
from typing import List, Optional


class ValidationError:
    """Represents a validation error."""
    
    def __init__(self, message: str):
        """Initialize validation error.
        
        Args:
            message: Error message.
        """
        self.message = message
    
    def __str__(self) -> str:
        """String representation."""
        return self.message


class GameValidator:
    """Validator for game files using PyGambit's built-in parser."""
    
    @staticmethod
    def validate(content: str) -> List[ValidationError]:
        """Validate game file using PyGambit's parser.
        
        Args:
            content: Game file content (NFG or EFG format).
            
        Returns:
            List of validation errors (empty if valid).
        """
        content = content.strip()
        
        if not content:
            return [ValidationError("Empty file")]
        
        # Detect format
        if content.startswith("NFG"):
            return GameValidator._validate_with_pygambit(content, is_nfg=True)
        elif content.startswith("EFG"):
            return GameValidator._validate_with_pygambit(content, is_nfg=False)
        else:
            return [ValidationError("Unknown file format: File must start with 'NFG' or 'EFG'")]
    
    @staticmethod
    def _validate_with_pygambit(content: str, is_nfg: bool) -> List[ValidationError]:
        """Validate using PyGambit's parser.
        
        Args:
            content: Game file content.
            is_nfg: True for NFG format, False for EFG format.
            
        Returns:
            List of validation errors.
        """
        try:
            import pygambit as gbt
        except ImportError:
            return [ValidationError("PyGambit not installed. Run: pip install pygambit")]
        
        # Write to temporary file (PyGambit reads from files)
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.nfg' if is_nfg else '.efg',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Try to parse with PyGambit
                if is_nfg:
                    game = gbt.read_nfg(temp_path)  # type: ignore
                else:
                    game = gbt.read_efg(temp_path)  # type: ignore
                
                # If we get here, file is valid!
                return []
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            # PyGambit parsing failed - extract useful error message
            error_msg = str(e)
            
            return [ValidationError(f"{error_msg}")]
    
    # Keep legacy methods for backward compatibility
    @staticmethod
    def validate_nfg(content: str) -> List[ValidationError]:
        """Validate .nfg file content.
        
        Args:
            content: NFG file content.
            
        Returns:
            List of validation errors (empty if valid).
        """
        return GameValidator._validate_with_pygambit(content, is_nfg=True)
    
    @staticmethod
    def validate_efg(content: str) -> List[ValidationError]:
        """Validate .efg file content.
        
        Args:
            content: EFG file content.
            
        Returns:
            List of validation errors (empty if valid).
        """
        return GameValidator._validate_with_pygambit(content, is_nfg=False)

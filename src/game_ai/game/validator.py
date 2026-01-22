"""Game file validator."""

import re
from typing import List, Tuple, Optional


class ValidationError:
    """Represents a validation error."""
    
    def __init__(self, line_number: Optional[int], message: str, suggestion: str = ""):
        """Initialize validation error.
        
        Args:
            line_number: Line number where error occurred (1-indexed).
            message: Error message.
            suggestion: Optional suggestion for fixing the error.
        """
        self.line_number = line_number
        self.message = message
        self.suggestion = suggestion
    
    def __str__(self) -> str:
        """String representation."""
        location = f"Line {self.line_number}: " if self.line_number else ""
        suggestion = f"\n  Suggestion: {self.suggestion}" if self.suggestion else ""
        return f"{location}{self.message}{suggestion}"


class GameValidator:
    """Validator for game files."""
    
    @staticmethod
    def validate_nfg(content: str) -> List[ValidationError]:
        """Validate .nfg file content.
        
        Args:
            content: NFG file content.
            
        Returns:
            List of validation errors (empty if valid).
        """
        errors = []
        lines = content.strip().split('\n')
        
        if not lines:
            errors.append(ValidationError(None, "Empty file"))
            return errors
        
        # Check header
        header_pattern = r'NFG\s+\d+\s+\w+\s+"[^"]*"'
        if not re.match(header_pattern, lines[0]):
            errors.append(ValidationError(
                1,
                "Invalid NFG header",
                'Expected format: NFG 1 R "Game Title"'
            ))
        
        if len(lines) < 4:
            errors.append(ValidationError(
                None,
                "Incomplete NFG file",
                "NFG files need: header, players, strategy counts, and payoffs"
            ))
            return errors
        
        # Check players line
        player_pattern = r'\{[^}]+\}'
        if not re.search(player_pattern, lines[1]):
            errors.append(ValidationError(
                2,
                "Invalid players definition",
                'Expected format: { "Player 1" "Player 2" ... }'
            ))
        else:
            # Extract player count
            player_matches = re.findall(r'"([^"]+)"', lines[1])
            num_players = len(player_matches)
            
            # Check strategy counts line
            if not re.search(r'\{[^}]+\}', lines[2]):
                errors.append(ValidationError(
                    3,
                    "Invalid strategy counts",
                    'Expected format: { 3 2 4 }'
                ))
            else:
                # Extract strategy counts
                strat_match = re.search(r'\{([^}]+)\}', lines[2])
                if strat_match:
                    try:
                        strat_counts = [int(x) for x in strat_match.group(1).split()]
                        
                        if len(strat_counts) != num_players:
                            errors.append(ValidationError(
                                3,
                                f"Strategy count mismatch: {len(strat_counts)} counts for {num_players} players",
                                f"Provide {num_players} strategy counts"
                            ))
                        
                        # Calculate expected payoffs
                        total_outcomes = 1
                        for count in strat_counts:
                            total_outcomes *= count
                        expected_payoffs = total_outcomes * num_players
                        
                        # Check payoffs
                        payoff_lines = []
                        for i in range(3, len(lines)):
                            if lines[i].strip():
                                payoff_lines.append(lines[i].strip())
                        
                        if payoff_lines:
                            payoff_str = ' '.join(payoff_lines)
                            try:
                                payoffs = [float(x) for x in payoff_str.split()]
                                
                                if len(payoffs) != expected_payoffs:
                                    errors.append(ValidationError(
                                        4,
                                        f"Payoff count mismatch: expected {expected_payoffs}, got {len(payoffs)}",
                                        f"Need {total_outcomes} outcomes × {num_players} players = {expected_payoffs} values"
                                    ))
                            except ValueError as e:
                                errors.append(ValidationError(
                                    4,
                                    f"Invalid payoff values: {e}",
                                    "Payoffs must be numeric"
                                ))
                        else:
                            errors.append(ValidationError(
                                4,
                                "No payoffs found",
                                f"Add {expected_payoffs} payoff values"
                            ))
                    
                    except ValueError:
                        errors.append(ValidationError(
                            3,
                            "Strategy counts must be integers"
                        ))
        
        return errors
    
    @staticmethod
    def validate_efg(content: str) -> List[ValidationError]:
        """Validate .efg file content.
        
        Args:
            content: EFG file content.
            
        Returns:
            List of validation errors (empty if valid).
        """
        errors = []
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
        
        if not lines:
            errors.append(ValidationError(None, "Empty file"))
            return errors
        
        # Check header
        header_pattern = r'EFG\s+\d+\s+\w+\s+"[^"]*"'
        if not re.match(header_pattern, lines[0]):
            errors.append(ValidationError(
                1,
                "Invalid EFG header",
                'Expected format: EFG 2 R "Game Title"'
            ))
        
        if len(lines) < 3:
            errors.append(ValidationError(
                None,
                "Incomplete EFG file",
                "EFG files need: header, players, and at least one node"
            ))
            return errors
        
        # Check players line
        player_pattern = r'\{[^}]+\}'
        if not re.search(player_pattern, lines[1]):
            errors.append(ValidationError(
                2,
                "Invalid players definition",
                'Expected format: { "Player 1" "Player 2" ... }'
            ))
        else:
            player_matches = re.findall(r'"([^"]+)"', lines[1])
            num_players = len(player_matches)
            
            # Check nodes
            for i in range(2, len(lines)):
                line = lines[i]
                node_type = line[0] if line else ''
                
                if node_type not in ['c', 'p', 't']:
                    errors.append(ValidationError(
                        i + 1,
                        f"Invalid node type: '{node_type}'",
                        "Node must start with 'c' (chance), 'p' (player), or 't' (terminal)"
                    ))
                    continue
                
                # Basic syntax check for each node type
                if node_type == 't':
                    # Terminal node should have payoffs
                    payoff_match = re.search(r'\{([^}]+)\}', line)
                    if payoff_match:
                        try:
                            payoffs = [float(x) for x in payoff_match.group(1).split()]
                            if len(payoffs) != num_players:
                                errors.append(ValidationError(
                                    i + 1,
                                    f"Terminal node has {len(payoffs)} payoffs, expected {num_players}",
                                    f"Provide one payoff value per player"
                                ))
                        except ValueError:
                            errors.append(ValidationError(
                                i + 1,
                                "Invalid payoff values in terminal node",
                                "Payoffs must be numeric"
                            ))
                
                elif node_type == 'c':
                    # Chance node should have probabilities
                    if '{' not in line or '}' not in line:
                        errors.append(ValidationError(
                            i + 1,
                            "Chance node missing action/probability specification",
                            'Format: c "name" infoset "label" { "action1" prob1 "action2" prob2 } outcome'
                        ))
                
                elif node_type == 'p':
                    # Player node should have actions
                    if '{' not in line or '}' not in line:
                        errors.append(ValidationError(
                            i + 1,
                            "Player node missing action specification",
                            'Format: p "name" player infoset "label" { "action1" "action2" } outcome'
                        ))
        
        return errors
    
    @staticmethod
    def validate(content: str) -> List[ValidationError]:
        """Automatically detect format and validate.
        
        Args:
            content: Game file content.
            
        Returns:
            List of validation errors.
        """
        content = content.strip()
        
        if not content:
            return [ValidationError(None, "Empty file")]
        
        if content.startswith("NFG"):
            return GameValidator.validate_nfg(content)
        elif content.startswith("EFG"):
            return GameValidator.validate_efg(content)
        else:
            return [ValidationError(
                1,
                "Unknown file format",
                "File must start with 'NFG' or 'EFG'"
            )]

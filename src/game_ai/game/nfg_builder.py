"""Strategic form (.nfg) game file builder."""

from typing import List, Dict, Optional, Tuple


class NFGBuilder:
    """Builder for strategic form game files."""
    
    def __init__(self):
        """Initialize NFG builder."""
        self.title: str = "Untitled Game"
        self.players: List[str] = []
        self.num_strategies: List[int] = []
        self.payoffs: List[float] = []
    
    def set_title(self, title: str):
        """Set game title.
        
        Args:
            title: Game title.
        """
        self.title = title
    
    def set_players(self, players: List[str]):
        """Set player names.
        
        Args:
            players: List of player names.
        """
        self.players = players
    
    def set_strategies(self, num_strategies: List[int]):
        """Set number of strategies per player.
        
        Args:
            num_strategies: List of strategy counts per player.
        """
        if len(num_strategies) != len(self.players):
            raise ValueError(
                f"Number of strategy counts ({len(num_strategies)}) must match "
                f"number of players ({len(self.players)})"
            )
        self.num_strategies = num_strategies
    
    def set_payoffs(self, payoffs: List[float]):
        """Set payoff values.
        
        Payoffs should be in row-major order: first player's strategies vary fastest.
        For 2 players with m and n strategies, order is:
        (s1_1, s2_1), (s1_2, s2_1), ..., (s1_m, s2_1), (s1_1, s2_2), ...
        
        Each outcome needs len(players) payoff values.
        
        Args:
            payoffs: Flat list of payoff values.
        """
        expected_length = self._calculate_total_outcomes() * len(self.players)
        if len(payoffs) != expected_length:
            raise ValueError(
                f"Expected {expected_length} payoff values, got {len(payoffs)}"
            )
        self.payoffs = payoffs
    
    def _calculate_total_outcomes(self) -> int:
        """Calculate total number of strategy profiles."""
        if not self.num_strategies:
            return 0
        
        total = 1
        for num in self.num_strategies:
            total *= num
        return total
    
    def to_nfg_string(self) -> str:
        """Generate .nfg file content.
        
        Returns:
            NFG file content as string.
        """
        if not self.players:
            raise ValueError("No players defined")
        if not self.num_strategies:
            raise ValueError("No strategies defined")
        if not self.payoffs:
            raise ValueError("No payoffs defined")
        
        lines = []
        
        # Header
        lines.append(f'NFG 1 R "{self.title}"')
        
        # Players
        player_names = ' '.join(f'"{p}"' for p in self.players)
        lines.append(f'{{ {player_names} }}')
        
        # Number of strategies
        strat_counts = ' '.join(str(n) for n in self.num_strategies)
        lines.append(f'{{ {strat_counts} }}')
        
        # Empty line before payoffs
        lines.append('')
        
        # Payoffs (all on one line or multiple lines)
        payoff_str = ' '.join(str(p) for p in self.payoffs)
        lines.append(payoff_str)
        
        return '\n'.join(lines)
    
    @classmethod
    def from_nfg_string(cls, content: str) -> 'NFGBuilder':
        """Parse .nfg file content into builder.
        
        Args:
            content: NFG file content.
            
        Returns:
            NFGBuilder instance.
        """
        import re
        
        builder = cls()
        lines = content.strip().split('\n')
        
        # Parse header
        header_match = re.match(r'NFG\s+\d+\s+\w+\s+"([^"]*)"', lines[0])
        if header_match:
            builder.title = header_match.group(1)
        
        # Parse players and strategy counts - they can be on the same line or separate lines
        # Find all { ... } groups in lines 1 and 2
        braces_content = []
        for i in range(1, min(3, len(lines))):
            braces_content.extend(re.findall(r'\{([^}]+)\}', lines[i]))
        
        if len(braces_content) >= 2:
            # First braces: players
            player_str = braces_content[0]
            builder.players = [p.strip().strip('"') for p in re.findall(r'"([^"]+)"', player_str)]
            
            # Second braces: strategy counts
            strat_str = braces_content[1]
            builder.num_strategies = [int(x) for x in strat_str.split()]
        
        # Parse payoffs (can span multiple lines, skip empty lines)
        # Start searching after the header lines
        payoff_lines = []
        for i in range(1, len(lines)):
            line = lines[i].strip()
            # Skip lines with braces (metadata) and empty lines
            if line and not re.search(r'\{[^}]*\}', line):
                payoff_lines.append(line)
        
        payoff_str = ' '.join(payoff_lines)
        builder.payoffs = [float(x) for x in payoff_str.split()]
        
        return builder

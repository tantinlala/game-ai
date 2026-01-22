"""Extensive form (.efg) game file builder."""

from typing import List, Dict, Optional, Tuple
from enum import Enum


class NodeType(Enum):
    """Type of game tree node."""
    CHANCE = "c"
    PLAYER = "p"
    TERMINAL = "t"


class EFGNode:
    """Represents a node in an extensive form game."""
    
    def __init__(
        self,
        node_type: NodeType,
        name: str = "",
        player: Optional[int] = None,
        infoset: Optional[int] = None,
        actions: Optional[List[str]] = None,
        action_probs: Optional[List[float]] = None,
        payoffs: Optional[List[float]] = None,
        outcome: str = ""
    ):
        """Initialize EFG node.
        
        Args:
            node_type: Type of node (chance, player, terminal).
            name: Node name/label.
            player: Player number (for player nodes).
            infoset: Information set number (for player nodes).
            actions: List of action names.
            action_probs: List of action probabilities (for chance nodes).
            payoffs: List of payoffs (for terminal nodes).
            outcome: Outcome name (for terminal nodes).
        """
        self.node_type = node_type
        self.name = name
        self.player = player
        self.infoset = infoset
        self.actions = actions or []
        self.action_probs = action_probs or []
        self.payoffs = payoffs or []
        self.outcome = outcome
        self.children: List['EFGNode'] = []
    
    def add_child(self, child: 'EFGNode'):
        """Add a child node."""
        self.children.append(child)
    
    def to_efg_line(self, iset_label: str = "", outcome_num: int = 0) -> str:
        """Convert node to .efg file line.
        
        Args:
            iset_label: Information set label.
            outcome_num: Outcome number.
            
        Returns:
            EFG file line.
        """
        if self.node_type == NodeType.CHANCE:
            # c "name" infoset (iset_label) { "action1" prob1 "action2" prob2 ... } outcome
            actions_str = ' '.join(
                f'"{action}" {prob}'
                for action, prob in zip(self.actions, self.action_probs)
            )
            return f'c "{self.name}" {self.infoset} "{iset_label}" {{ {actions_str} }} {outcome_num}'
        
        elif self.node_type == NodeType.PLAYER:
            # p "name" player infoset (iset_label) { "action1" "action2" ... } outcome
            actions_str = ' '.join(f'"{action}"' for action in self.actions)
            return f'p "{self.name}" {self.player} {self.infoset} "{iset_label}" {{ {actions_str} }} {outcome_num}'
        
        elif self.node_type == NodeType.TERMINAL:
            # t "name" outcome "outcome_name" { payoff1 payoff2 ... }
            payoffs_str = ' '.join(str(p) for p in self.payoffs)
            return f't "{self.name}" {outcome_num} "{self.outcome}" {{ {payoffs_str} }}'
        
        return ""


class EFGBuilder:
    """Builder for extensive form game files."""
    
    def __init__(self):
        """Initialize EFG builder."""
        self.title: str = "Untitled Game"
        self.players: List[str] = []
        self.root: Optional[EFGNode] = None
    
    def set_title(self, title: str):
        """Set game title."""
        self.title = title
    
    def set_players(self, players: List[str]):
        """Set player names."""
        self.players = players
    
    def set_root(self, root: EFGNode):
        """Set root node of game tree."""
        self.root = root
    
    def to_efg_string(self) -> str:
        """Generate .efg file content.
        
        Returns:
            EFG file content as string.
        """
        if not self.players:
            raise ValueError("No players defined")
        if not self.root:
            raise ValueError("No root node defined")
        
        lines = []
        
        # Header
        lines.append(f'EFG 2 R "{self.title}"')
        
        # Players
        player_names = ' '.join(f'"{p}"' for p in self.players)
        lines.append(f'{{ {player_names} }}')
        
        # Empty line
        lines.append('')
        
        # Traverse tree in prefix order
        outcome_counter = [1]  # Mutable counter
        self._traverse_tree(self.root, lines, outcome_counter)
        
        return '\n'.join(lines)
    
    def _traverse_tree(
        self,
        node: EFGNode,
        lines: List[str],
        outcome_counter: List[int]
    ):
        """Traverse tree in prefix order and generate lines.
        
        Args:
            node: Current node.
            lines: List to append lines to.
            outcome_counter: Mutable outcome counter.
        """
        # Generate line for current node
        outcome_num = 0
        if node.node_type == NodeType.TERMINAL:
            outcome_num = outcome_counter[0]
            outcome_counter[0] += 1
        
        iset_label = f"({node.player},{node.infoset})" if node.infoset is not None else ""
        lines.append(node.to_efg_line(iset_label, outcome_num))
        
        # Recursively process children
        for child in node.children:
            self._traverse_tree(child, lines, outcome_counter)
    
    @classmethod
    def from_efg_string(cls, content: str) -> 'EFGBuilder':
        """Parse .efg file content into builder.
        
        Note: This is a simplified parser. Full parsing is complex.
        
        Args:
            content: EFG file content.
            
        Returns:
            EFGBuilder instance.
        """
        import re
        
        builder = cls()
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
        
        # Parse header
        header_match = re.match(r'EFG\s+\d+\s+\w+\s+"([^"]*)"', lines[0])
        if header_match:
            builder.title = header_match.group(1)
        
        # Parse players
        player_match = re.search(r'\{([^}]+)\}', lines[1])
        if player_match:
            player_str = player_match.group(1)
            builder.players = [p.strip().strip('"') for p in re.findall(r'"([^"]+)"', player_str)]
        
        # Note: Full tree parsing is complex and requires careful state management
        # For now, we store the raw content
        # A full implementation would reconstruct the tree structure
        
        return builder

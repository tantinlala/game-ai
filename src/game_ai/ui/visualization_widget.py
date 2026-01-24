"""Visualization widget for game files."""

import re
from typing import Optional, List, Tuple
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.app import ComposeResult
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich.tree import Tree
from ..game.nfg_builder import NFGBuilder
from ..game.efg_builder import EFGBuilder


class VisualizationWidget(VerticalScroll):
    """Widget for visualizing game files (NFG and EFG formats)."""
    
    # Player color scheme
    PLAYER_COLORS = [
        "cyan",      # Player 1
        "magenta",   # Player 2
        "green",     # Player 3
        "yellow",    # Player 4
        "blue",      # Player 5
        "red",       # Player 6
    ]
    
    DEFAULT_CSS = """
    VisualizationWidget {
        padding: 1;
    }
    
    #visualization-container {
        height: 1fr;
        border: solid $primary;
        background: $surface;
        overflow-x: auto;
        overflow-y: auto;
    }
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize visualization widget."""
        super().__init__(*args, **kwargs)
        self._content: str = ""
        self._game_type: Optional[str] = None
        self._content_widget: Optional[Static] = None
    
    def compose(self) -> ComposeResult:
        """Compose the widget with a Static child for content."""
        self._content_widget = Static()
        yield self._content_widget
    
    def set_content(self, content: str):
        """Parse and visualize the game file content.
        
        Args:
            content: Game file content (NFG or EFG format).
        """
        self._content = content
        
        if not content or not content.strip():
            if self._content_widget:
                self._content_widget.update(Text("No content to display", style="dim italic"))
            return
        
        # Auto-detect game type
        self._game_type = self._detect_game_type(content)
        
        try:
            if self._game_type == "NFG":
                self._visualize_nfg(content)
            elif self._game_type == "EFG":
                self._visualize_efg(content)
            else:
                if self._content_widget:
                    self._content_widget.update(Text("Unable to detect game format", style="red bold"))
        except Exception as e:
            if self._content_widget:
                self._content_widget.update(Text(f"Error visualizing game: {str(e)}", style="red"))
    
    def clear(self):
        """Clear the visualization."""
        self._content = ""
        self._game_type = None
        if self._content_widget:
            self._content_widget.update(Text("", style="dim"))
    
    def _get_player_color(self, player_index: int) -> str:
        """Get color for a player.
        
        Args:
            player_index: Player index (0-based).
            
        Returns:
            Color name for the player.
        """
        if player_index >= len(self.PLAYER_COLORS):
            return "white"
        return self.PLAYER_COLORS[player_index]
    
    def _detect_game_type(self, content: str) -> Optional[str]:
        """Detect whether content is NFG or EFG format.
        
        Args:
            content: Game file content.
            
        Returns:
            "NFG", "EFG", or None if unable to detect.
        """
        first_line = content.strip().split('\n')[0] if content.strip() else ""
        
        if first_line.startswith("NFG"):
            return "NFG"
        elif first_line.startswith("EFG"):
            return "EFG"
        
        return None
    
    def _visualize_nfg(self, content: str):
        """Visualize NFG (strategic form) game as a payoff matrix.
        
        Args:
            content: NFG file content.
        """
        try:
            builder = NFGBuilder.from_nfg_string(content)
            
            # Create header text
            header = Text()
            header.append(f"Strategic Form Game: ", style="bold cyan")
            header.append(builder.title, style="bold white")
            header.append("\n\n")
            
            # For 2-player games, create a payoff matrix table
            if len(builder.players) == 2:
                table = self._create_2player_matrix(builder)
                if self._content_widget:
                    self._content_widget.update(Group(header, table))
            else:
                # For n-player games (n > 2), display as structured text
                info = self._create_nplayer_info(builder)
                if self._content_widget:
                    self._content_widget.update(Group(header, info))
                
        except Exception as e:
            raise ValueError(f"Failed to parse NFG content: {str(e)}")
    
    def _create_2player_matrix(self, builder: NFGBuilder) -> Table:
        """Create a payoff matrix table for 2-player games.
        
        Args:
            builder: NFGBuilder instance with parsed game data.
            
        Returns:
            Rich Table with payoff matrix.
        """
        # Get player colors
        p1_color = self._get_player_color(0)
        p2_color = self._get_player_color(1)
        
        table = Table(
            title=f"{builder.players[0]} (rows) vs {builder.players[1]} (columns)",
            show_header=True,
            header_style="bold white",
            border_style="blue",
            title_style="white bold"
        )
        
        # Add column headers (Player 2's strategies)
        header_label = Text()
        header_label.append(f"{builder.players[0]}", style=f"{p1_color} bold")
        header_label.append(" \\ ", style="white")
        header_label.append(f"{builder.players[1]}", style=f"{p2_color} bold")
        table.add_column(header_label, style="white")
        
        for j in range(builder.num_strategies[1]):
            col_header = Text(f"Strategy {j+1}", style=f"{p2_color} bold")
            table.add_column(col_header, justify="center")
        
        # Add rows (Player 1's strategies)
        num_strat_p1 = builder.num_strategies[0]
        num_strat_p2 = builder.num_strategies[1]
        num_players = len(builder.players)
        
        for i in range(num_strat_p1):
            row_label = Text(f"Strategy {i+1}", style=f"{p1_color} bold")
            row = [row_label]
            
            for j in range(num_strat_p2):
                # Calculate index in payoffs array
                # NFG format: first player's strategies vary fastest
                outcome_idx = j * num_strat_p1 + i
                payoff_idx = outcome_idx * num_players
                
                # Get payoffs for both players
                p1_payoff = builder.payoffs[payoff_idx]
                p2_payoff = builder.payoffs[payoff_idx + 1]
                
                # Format with player colors
                payoff_text = Text("(")
                payoff_text.append(f"{p1_payoff:.1f}", style=f"{p1_color} bold")
                payoff_text.append(", ", style="white")
                payoff_text.append(f"{p2_payoff:.1f}", style=f"{p2_color} bold")
                payoff_text.append(")", style="white")
                
                row.append(payoff_text)
            
            table.add_row(*row)
        
        return table
    
    def _create_nplayer_info(self, builder: NFGBuilder) -> Text:
        """Create structured text info for n-player games.
        
        Args:
            builder: NFGBuilder instance with parsed game data.
            
        Returns:
            Rich Text with game information.
        """
        text = Text()
        
        # Players
        text.append("Players: ", style="bold white")
        for i, player in enumerate(builder.players):
            if i > 0:
                text.append(", ", style="white")
            player_color = self._get_player_color(i)
            text.append(player, style=f"{player_color} bold")
        text.append("\n\n")
        
        # Strategies
        text.append("Strategies per player:\n", style="bold white")
        for i, (player, num_strat) in enumerate(zip(builder.players, builder.num_strategies)):
            player_color = self._get_player_color(i)
            text.append(f"  {player}: ", style=f"{player_color} bold")
            text.append(f"{num_strat} strategies\n", style="white")
        
        text.append("\n")
        
        # Total outcomes
        total_outcomes = 1
        for num in builder.num_strategies:
            total_outcomes *= num
        
        text.append(f"Total strategy profiles: ", style="bold yellow")
        text.append(f"{total_outcomes}\n\n", style="white")
        
        # Note for n-player games
        text.append("Note: ", style="bold red")
        text.append(f"Full payoff matrix visualization is only available for 2-player games.\n", style="italic")
        text.append(f"This game has {len(builder.players)} players.\n", style="italic")
        
        return text
    
    def _visualize_efg(self, content: str):
        """Visualize EFG (extensive form) game as a Rich Tree.
        
        Args:
            content: EFG file content.
        """
        try:
            builder = EFGBuilder.from_efg_string(content)
            
            # Create header text
            header = Text()
            header.append(f"Extensive Form Game: ", style="bold white")
            header.append(builder.title, style="bold white")
            header.append("\n")
            header.append(f"Players: ", style="bold white")
            header.append(", ".join(builder.players), style="white")
            header.append("\n\n")
            
            # Parse nodes
            nodes = self._parse_all_nodes(content)
            if not nodes:
                if self._content_widget:
                    self._content_widget.update(Group(header, Text("No nodes found in game tree", style="dim italic")))
                return
            
            # Create tree visualization
            tree = Tree("🎮 Game Tree", guide_style="bold bright_blue")
            self._build_rich_tree(tree, nodes, 0, builder)
            
            if self._content_widget:
                self._content_widget.update(Group(header, tree))
            
        except Exception as e:
            raise ValueError(f"Failed to parse EFG content: {str(e)}")
    
    def _parse_all_nodes(self, content: str) -> List[Tuple]:
        """Parse all nodes from EFG content.
        
        Args:
            content: EFG file content.
            
        Returns:
            List of parsed nodes.
        """
        lines = [l.strip() for l in content.strip().split('\n') if l.strip()]
        
        nodes = []
        for i, line in enumerate(lines):
            if i >= 1 and (line.startswith('c ') or line.startswith('p ') or line.startswith('t ')):
                node_info = self._parse_node_line(line)
                if node_info:
                    nodes.append(node_info)
        
        return nodes
    
    def _build_rich_tree(self, parent_tree, nodes: list, index: int, builder: EFGBuilder) -> int:
        """Recursively build Rich Tree from parsed nodes.
        
        Args:
            parent_tree: Parent Tree or tree node to attach to.
            nodes: List of all parsed nodes.
            index: Current node index.
            builder: EFGBuilder instance.
            
        Returns:
            Next node index to process.
        """
        if index >= len(nodes):
            return index
        
        node_type, name, player, infoset, actions, payoffs, outcome = nodes[index]
        
        # Terminal node - add it directly to parent and return
        if node_type == 't':
            label = Text()
            label.append("■ Terminal", style="white bold")
            
            if payoffs:
                label.append(" → ", style="dim")
                payoff_parts = []
                for i, p in enumerate(payoffs):
                    player_color = self._get_player_color(i)
                    payoff_text = Text()
                    payoff_text.append(f"{builder.players[i]}: ", style=f"{player_color} bold")
                    payoff_text.append(f"{p:.1f}", style=player_color)
                    payoff_parts.append(payoff_text)
                
                # Combine payoff parts with separators
                combined_payoffs = Text("(")
                for i, payoff_part in enumerate(payoff_parts):
                    if i > 0:
                        combined_payoffs.append(", ", style="white")
                    combined_payoffs.append(payoff_part)
                combined_payoffs.append(")", style="white")
                label.append(combined_payoffs)
            
            parent_tree.add(label)
            return index + 1
        
        # Create node label
        label = Text()
        current_player_color = None
        
        if node_type == 'c':
            label.append("○ CHANCE", style="bright_white bold")
            if name:
                label.append(f" {name}", style="bright_white")
            if infoset and infoset != '""':
                label.append(f" ({infoset})", style="italic bright_white")
            current_player_color = "bright_white"
            
        elif node_type == 'p':
            player_name = builder.players[player - 1] if player and player <= len(builder.players) else f"Player {player}"
            player_color = self._get_player_color(player - 1)
            current_player_color = player_color
            
            label.append("● ", style=f"{player_color} bold")
            
            parts = []
            # 1. Infoset Name (if available)
            if infoset and infoset.strip():
                 parts.append((infoset, f"{player_color} italic"))
            
            # 2. Node Name (if available)
            if name and name.strip():
                 parts.append((name, f"{player_color}"))
                 
            # 3. Player Name
            parts.append((player_name, f"{player_color} bold"))
            
            for i, (text, style) in enumerate(parts):
                if i > 0:
                    label.append(" - ", style="white dim")
                label.append(text, style=style)
        
        # Add node to parent
        node = parent_tree.add(label)
        
        # Process children - each action leads to child nodes
        if actions:
            next_index = index + 1
            
            for action in actions:
                # Create branch with action label
                action_label = Text()
                action_label.append(f"[{action}]", style=f"{current_player_color}")
                branch = node.add(action_label)
                
                # Recursively add child nodes under this action branch
                next_index = self._build_rich_tree(branch, nodes, next_index, builder)
            
            return next_index
        
        return index + 1
    
    def _parse_node_line(self, line: str) -> Optional[Tuple]:
        """Parse a single node line from EFG format.
        
        Args:
            line: Node line from EFG file.
            
        Returns:
            Tuple of (node_type, name, player, infoset, actions, payoffs, outcome) or None.
        """
        try:
            # Chance node: c "name" infoset "label" { "action" prob ... } outcome
            if line.startswith('c '):
                match = re.match(r'c\s+"([^"]*)"\s+\d+\s+"([^"]*)"\s+\{([^}]*)\}', line)
                if match:
                    name = match.group(1)
                    infoset = match.group(2)
                    actions_str = match.group(3).strip()
                    # Extract actions (ignore probabilities for visualization)
                    actions = re.findall(r'"([^"]+)"', actions_str)
                    return ('c', name, None, infoset, actions, [], "")
            
            # Player node: p "name" player infoset "label" { "action" ... } outcome
            elif line.startswith('p '):
                match = re.match(r'p\s+"([^"]*)"\s+(\d+)\s+\d+\s+"([^"]*)"\s+\{([^}]*)\}', line)
                if match:
                    name = match.group(1)
                    player = int(match.group(2))
                    infoset = match.group(3)
                    actions_str = match.group(4).strip()
                    actions = re.findall(r'"([^"]+)"', actions_str)
                    return ('p', name, player, infoset, actions, [], "")
            
            # Terminal node: t "name" outcome "outcome_name" { payoff1 payoff2 ... }
            elif line.startswith('t '):
                match = re.match(r't\s+"([^"]*)"\s+\d+\s+"([^"]*)"\s+\{([^}]*)\}', line)
                if match:
                    name = match.group(1)
                    outcome = match.group(2)
                    payoffs_str = match.group(3).strip()
                    payoffs = [float(p) for p in payoffs_str.split()]
                    return ('t', name, None, None, [], payoffs, outcome)
        
        except Exception:
            pass
        
        return None

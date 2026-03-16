"""Visualization widget for game files."""

import re
import tempfile
import os
from typing import Optional, List, Tuple
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.app import ComposeResult
from rich.table import Table
from rich.text import Text
from rich.console import Group
from rich.tree import Tree
import pygambit as gbt


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
            # Use pygambit to parse the game
            with tempfile.NamedTemporaryFile(mode='w', suffix='.nfg', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                game = gbt.read_nfg(temp_path)  # type: ignore
                
                # Create header text
                header = Text()
                header.append(f"Strategic Form Game: ", style="bold cyan")
                header.append(game.title, style="bold white")
                header.append("\n\n")
                
                # For 2-player games, create a payoff matrix table
                if len(game.players) == 2:
                    table = self._create_2player_matrix_from_game(game)
                    if self._content_widget:
                        self._content_widget.update(Group(header, table))
                else:
                    # For n-player games (n > 2), display as structured text
                    info = self._create_nplayer_info_from_game(game)
                    if self._content_widget:
                        self._content_widget.update(Group(header, info))
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
        except Exception as e:
            raise ValueError(f"Failed to parse NFG content: {str(e)}")
    
    def _create_2player_matrix_from_game(self, game) -> Table:
        """Create a payoff matrix table for 2-player games from pygambit game object.
        
        Args:
            game: PyGambit game object.
            
        Returns:
            Rich Table with payoff matrix.
        """
        # Get player colors
        p1_color = self._get_player_color(0)
        p2_color = self._get_player_color(1)
        
        player1 = game.players[0]
        player2 = game.players[1]
        
        table = Table(
            title=f"{player1.label} (rows) vs {player2.label} (columns)",
            show_header=True,
            header_style="bold white",
            border_style="blue",
            title_style="white bold"
        )
        
        # Add column headers (Player 2's strategies)
        header_label = Text()
        header_label.append(f"{player1.label}", style=f"{p1_color} bold")
        header_label.append(" \\ ", style="white")
        header_label.append(f"{player2.label}", style=f"{p2_color} bold")
        table.add_column(header_label, style="white")
        
        for strat in player2.strategies:
            col_header = Text(strat.label, style=f"{p2_color} bold")
            table.add_column(col_header, justify="center")
        
        # Add rows (Player 1's strategies)
        for strat1 in player1.strategies:
            row_label = Text(strat1.label, style=f"{p1_color} bold")
            row = [row_label]
            
            for strat2 in player2.strategies:
                # Get the outcome for this strategy profile using __getitem__
                outcome = game[[strat1, strat2]]
                
                if outcome:
                    p1_payoff = outcome[player1]
                    p2_payoff = outcome[player2]
                else:
                    p1_payoff = 0
                    p2_payoff = 0
                
                # Format with player colors
                payoff_text = Text("(")
                payoff_text.append(f"{float(p1_payoff):.1f}", style=f"{p1_color} bold")
                payoff_text.append(", ", style="white")
                payoff_text.append(f"{float(p2_payoff):.1f}", style=f"{p2_color} bold")
                payoff_text.append(")", style="white")
                
                row.append(payoff_text)
            
            table.add_row(*row)
        
        return table
    
    def _create_nplayer_info_from_game(self, game) -> Text:
        """Create structured text info for n-player games from pygambit game object.
        
        Args:
            game: PyGambit game object.
            
        Returns:
            Rich Text with game information.
        """
        text = Text()
        
        # Players
        text.append("Players: ", style="bold white")
        for i, player in enumerate(game.players):
            if i > 0:
                text.append(", ", style="white")
            player_color = self._get_player_color(i)
            text.append(player.label, style=f"{player_color} bold")
        text.append("\n\n")
        
        # Strategies
        text.append("Strategies per player:\n", style="bold white")
        for i, player in enumerate(game.players):
            player_color = self._get_player_color(i)
            text.append(f"  {player.label}: ", style=f"{player_color} bold")
            text.append(f"{len(player.strategies)} strategies\n", style="white")
        
        text.append("\n")
        
        # Total outcomes
        total_outcomes = 1
        for player in game.players:
            total_outcomes *= len(player.strategies)
        
        text.append(f"Total strategy profiles: ", style="bold yellow")
        text.append(f"{total_outcomes}\n\n", style="white")
        
        # Note for n-player games
        text.append("Note: ", style="bold red")
        text.append(f"Full payoff matrix visualization is only available for 2-player games.\n", style="italic")
        text.append(f"This game has {len(game.players)} players.\n", style="italic")
        
        return text
    
    def _has_chance_nodes(self, node) -> bool:
        """Recursively check if game tree has any chance nodes.
        
        Args:
            node: Current game node.
            
        Returns:
            True if any chance nodes exist in the tree.
        """
        if not node.is_terminal:
            if node.infoset and node.infoset.is_chance:
                return True
            for action in node.infoset.actions if node.infoset else []:
                if self._has_chance_nodes(node.children[action.number]):
                    return True
        return False
    
    def _visualize_efg(self, content: str):
        """Visualize EFG (extensive form) game as a Rich Tree.
        
        Args:
            content: EFG file content.
        """
        try:
            # Use pygambit to parse the game
            with tempfile.NamedTemporaryFile(mode='w', suffix='.efg', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                game = gbt.read_efg(temp_path)  # type: ignore
                
                # Create header text
                header = Text()
                header.append(f"Extensive Form Game: ", style="bold white")
                header.append(game.title, style="bold white")
                header.append("\n")
                header.append(f"Players: ", style="bold white")
                
                # Check if there are any chance nodes
                has_chance = self._has_chance_nodes(game.root)
                
                # Add Chance first if there are chance nodes
                if has_chance:
                    header.append("Chance", style="bright_white bold")
                    header.append(", ", style="white")
                
                # Add each player with their color
                for i, player in enumerate(game.players):
                    if i > 0:
                        header.append(", ", style="white")
                    player_color = self._get_player_color(i)
                    header.append(player.label, style=f"{player_color} bold")
                
                header.append("\n\n")
                
                # Create tree visualization
                tree = Tree("🎮 Game Tree", guide_style="bold bright_blue")
                self._build_tree_from_game(tree, game.root, game)
                
                if self._content_widget:
                    self._content_widget.update(Group(header, tree))
                    
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            raise ValueError(f"Failed to parse EFG content: {str(e)}")
    
    def _build_tree_from_game(self, parent_tree, node, game):
        """Recursively build Rich Tree from pygambit game tree.
        
        Args:
            parent_tree: Parent Tree or tree node to attach to.
            node: Current pygambit game node.
            game: PyGambit game object.
        """
        # Terminal node
        if node.is_terminal:
            label = Text()
            label.append("■ Terminal", style="white bold")
            
            outcome = node.outcome
            if outcome:
                label.append(" → ", style="dim")
                payoff_parts = []
                for i, player in enumerate(game.players):
                    player_color = self._get_player_color(i)
                    payoff_text = Text()
                    payoff_text.append(f"{float(outcome[player]):.1f}", style=f"{player_color} bold")
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
            return
        
        # Create node label
        label = Text()
        
        # Chance node
        if node.infoset and node.infoset.is_chance:
            current_player_color = "bright_white"
            label.append("● ", style=f"{current_player_color} bold")
            
            # Use infoset label or node label
            infoset_label = node.infoset.label if node.infoset.label and node.infoset.label.strip() else node.label
            if infoset_label and infoset_label.strip():
                label.append(infoset_label, style=f"{current_player_color} bold")
            else:
                label.append("Nature", style=f"{current_player_color} bold")
        
        # Player node
        else:
            player = node.player
            player_index = player.number  # Players are 0-indexed in pygambit
            player_color = self._get_player_color(player_index)
            current_player_color = player_color
            
            label.append("● ", style=f"{player_color} bold")
            
            parts = []
            # Infoset label
            if node.infoset.label and node.infoset.label.strip():
                parts.append((node.infoset.label, f"{player_color} italic"))
            
            # Node label
            if node.label and node.label.strip():
                parts.append((node.label, f"{player_color}"))
            
            for i, (text, style) in enumerate(parts):
                if i > 0:
                    label.append(" - ", style="white dim")
                label.append(text, style=style)
        
        # Add node to parent
        tree_node = parent_tree.add(label)
        
        # Process children - each action leads to child nodes
        for action in node.infoset.actions if node.infoset else []:
            # Create branch with action label
            action_label = Text()
            action_label.append(f"[{action.label}]", style=f"{current_player_color}")
            
            # Add probability for chance nodes
            if node.infoset.is_chance and hasattr(action, 'prob'):
                action_label.append(f" ({float(action.prob):.2%})", style="bright_white")
            
            branch = tree_node.add(action_label)
            
            # Get child node for this action
            child = node.children[action.number]
            
            # Recursively add child nodes under this action branch
            self._build_tree_from_game(branch, child, game)


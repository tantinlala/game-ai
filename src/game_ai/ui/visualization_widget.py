"""Visualization widget for game files."""

import tempfile
import os
from typing import Optional
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
            # Write content to temporary file and load with pygambit
            with tempfile.NamedTemporaryFile(mode='w', suffix='.nfg', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Load game using pygambit
                game = gbt.read_nfg(temp_path)
                
                # Create header text
                header = Text()
                header.append(f"Strategic Form Game: ", style="bold cyan")
                header.append(game.title, style="bold white")
                header.append("\n\n")
                
                # For 2-player games, create a payoff matrix table
                if len(game.players) == 2:
                    table = self._create_2player_matrix(game)
                    if self._content_widget:
                        self._content_widget.update(Group(header, table))
                else:
                    # For n-player games (n > 2), display as structured text
                    info = self._create_nplayer_info(game)
                    if self._content_widget:
                        self._content_widget.update(Group(header, info))
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
                
        except Exception as e:
            raise ValueError(f"Failed to parse NFG content: {str(e)}")
    
    def _create_2player_matrix(self, game) -> Table:
        """Create a payoff matrix table for 2-player games.
        
        Args:
            game: PyGambit game object.
            
        Returns:
            Rich Table with payoff matrix.
        """
        # Get player colors
        p1_color = self._get_player_color(0)
        p2_color = self._get_player_color(1)
        
        players = list(game.players)
        
        table = Table(
            title=f"{players[0].label} (rows) vs {players[1].label} (columns)",
            show_header=True,
            header_style="bold white",
            border_style="blue",
            title_style="white bold"
        )
        
        # Add column headers (Player 2's strategies)
        header_label = Text()
        header_label.append(f"{players[0].label}", style=f"{p1_color} bold")
        header_label.append(" \\ ", style="white")
        header_label.append(f"{players[1].label}", style=f"{p2_color} bold")
        table.add_column(header_label, style="white")
        
        p2_strategies = list(players[1].strategies)
        for strategy in p2_strategies:
            col_header = Text(strategy.label, style=f"{p2_color} bold")
            table.add_column(col_header, justify="center")
        
        # Add rows (Player 1's strategies)
        p1_strategies = list(players[0].strategies)
        
        for i, p1_strat in enumerate(p1_strategies):
            row_label = Text(p1_strat.label, style=f"{p1_color} bold")
            row = [row_label]
            
            for j, p2_strat in enumerate(p2_strategies):
                # Get the outcome for this strategy profile
                # In pygambit, index the game with the strategy profile
                outcome = game[p1_strat, p2_strat]
                
                # Get payoffs for both players
                p1_payoff = float(outcome[players[0]])
                p2_payoff = float(outcome[players[1]])
                
                # Format with player colors
                payoff_text = Text("(")
                payoff_text.append(f"{p1_payoff:.1f}", style=f"{p1_color} bold")
                payoff_text.append(", ", style="white")
                payoff_text.append(f"{p2_payoff:.1f}", style=f"{p2_color} bold")
                payoff_text.append(")", style="white")
                
                row.append(payoff_text)
            
            table.add_row(*row)
        
        return table
    
    def _create_nplayer_info(self, game) -> Text:
        """Create structured text info for n-player games.
        
        Args:
            game: PyGambit game object.
            
        Returns:
            Rich Text with game information.
        """
        text = Text()
        
        players = list(game.players)
        
        # Players
        text.append("Players: ", style="bold white")
        for i, player in enumerate(players):
            if i > 0:
                text.append(", ", style="white")
            player_color = self._get_player_color(i)
            text.append(player.label, style=f"{player_color} bold")
        text.append("\n\n")
        
        # Strategies
        text.append("Strategies per player:\n", style="bold white")
        for i, player in enumerate(players):
            player_color = self._get_player_color(i)
            text.append(f"  {player.label}: ", style=f"{player_color} bold")
            text.append(f"{len(player.strategies)} strategies\n", style="white")
        
        text.append("\n")
        
        # Total outcomes
        total_outcomes = 1
        for player in players:
            total_outcomes *= len(player.strategies)
        
        text.append(f"Total strategy profiles: ", style="bold yellow")
        text.append(f"{total_outcomes}\n\n", style="white")
        
        # Note for n-player games
        text.append("Note: ", style="bold red")
        text.append(f"Full payoff matrix visualization is only available for 2-player games.\n", style="italic")
        text.append(f"This game has {len(players)} players.\n", style="italic")
        
        return text
    
    def _visualize_efg(self, content: str):
        """Visualize EFG (extensive form) game as a Rich Tree.
        
        Args:
            content: EFG file content.
        """
        try:
            # Write content to temporary file and load with pygambit
            with tempfile.NamedTemporaryFile(mode='w', suffix='.efg', delete=False) as f:
                f.write(content)
                temp_path = f.name
            
            try:
                # Load game using pygambit
                game = gbt.read_efg(temp_path)
                
                # Create header text
                header = Text()
                header.append(f"Extensive Form Game: ", style="bold white")
                header.append(game.title, style="bold white")
                header.append("\\n")
                header.append(f"Players: ", style="bold white")
                player_names = ", ".join([p.label for p in game.players])
                header.append(player_names, style="white")
                header.append("\\n\\n")
                
                # Create tree visualization from game tree
                tree = Tree("🎮 Game Tree", guide_style="bold bright_blue")
                self._build_tree_from_game(tree, game.root, game)
                
                if self._content_widget:
                    self._content_widget.update(Group(header, tree))
            finally:
                # Clean up temporary file
                os.unlink(temp_path)
            
        except Exception as e:
            raise ValueError(f"Failed to parse EFG content: {str(e)}")
    
    def _build_tree_from_game(self, parent_tree, node, game):
        """Recursively build Rich Tree from pygambit game tree.
        
        Args:
            parent_tree: Parent Tree or tree node to attach to.
            node: PyGambit node object.
            game: PyGambit game object.
        """
        # Check if terminal node
        if node.is_terminal:
            label = Text()
            label.append("■ Terminal", style="white bold")
            
            # Add payoffs
            label.append(" → ", style="dim")
            payoffs_text = Text("(")
            for i, player in enumerate(game.players):
                if i > 0:
                    payoffs_text.append(", ", style="white")
                player_color = self._get_player_color(i)
                payoff_value = float(node.outcome[player])
                payoffs_text.append(f"{player.label}: ", style=f"{player_color} bold")
                payoffs_text.append(f"{payoff_value:.1f}", style=player_color)
            payoffs_text.append(")", style="white")
            label.append(payoffs_text)
            
            parent_tree.add(label)
            return
        
        # Check if this is a chance node
        if node.infoset.is_chance:
            label = Text()
            label.append("○ CHANCE", style="bright_white bold")
            if node.label:
                label.append(f" {node.label}", style="bright_white")
            
            # Create this node in the tree
            tree_node = parent_tree.add(label)
            
            # Add child nodes for each action
            for action in node.infoset.actions:
                action_label = Text()
                action_label.append(f"→ {action.label}", style="bright_white")
                
                # Get probability if available
                try:
                    prob = float(action.prob)
                    action_label.append(f" (p={prob:.2f})", style="dim")
                except:
                    pass
                
                action_node = tree_node.add(action_label)
                
                # Get the child node
                child = node.children[action]
                self._build_tree_from_game(action_node, child, game)
        else:
            # Player decision node
            player = node.infoset.player
            player_idx = list(game.players).index(player)
            player_color = self._get_player_color(player_idx)
            
            label = Text()
            label.append(f"● {player.label}", style=f"{player_color} bold")
            if node.label:
                label.append(f" {node.label}", style=player_color)
            
            # Create this node in the tree
            tree_node = parent_tree.add(label)
            
            # Add child nodes for each action
            for action in node.infoset.actions:
                action_label = Text()
                action_label.append(f"→ {action.label}", style=player_color)
                
                action_node = tree_node.add(action_label)
                
                # Get the child node
                child = node.children[action]
                self._build_tree_from_game(action_node, child, game)
    

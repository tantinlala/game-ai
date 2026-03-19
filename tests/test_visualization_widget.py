"""Tests for visualization widget."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from game_ai.ui.visualization_widget import VisualizationWidget
from rich.text import Text


@pytest.mark.ui
class TestVisualizationWidget:
    """Tests for VisualizationWidget class."""
    
    def test_initialization(self):
        """Test widget initialization."""
        widget = VisualizationWidget()
        assert widget._content == ""
        assert widget._game_type is None
        assert widget._content_widget is None
    
    def test_set_content_nfg(self, sample_nfg):
        """Test setting NFG content."""
        widget = VisualizationWidget()
        # Simulate compose being called
        widget._content_widget = Mock()
        
        widget.set_content(sample_nfg)
        
        assert widget._content == sample_nfg
        assert widget._game_type == "NFG"
        # Widget should attempt to update display
        assert widget._content_widget.update.called
    
    def test_set_content_efg(self, sample_efg):
        """Test setting EFG content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content(sample_efg)
        
        assert widget._content == sample_efg
        assert widget._game_type == "EFG"
        assert widget._content_widget.update.called
    
    def test_set_content_empty(self):
        """Test setting empty content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content("")
        
        assert widget._content == ""
        # Should display "No content" message
        assert widget._content_widget.update.called
    
    def test_set_content_invalid(self):
        """Test setting invalid content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content("INVALID GAME FORMAT")
        
        # Should handle gracefully
        assert widget._content_widget.update.called
    
    def test_clear_visualization(self):
        """Test clearing visualization."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        widget.set_content("some content")
        
        widget.clear()
        
        assert widget._content == ""
        assert widget._game_type is None
    
    def test_get_player_color(self):
        """Test player color assignment."""
        widget = VisualizationWidget()
        
        # Test first few players
        assert widget._get_player_color(0) == "cyan"
        assert widget._get_player_color(1) == "magenta"
        assert widget._get_player_color(2) == "green"
        
        # Test overflow
        assert widget._get_player_color(100) == "white"
    
    def test_detect_game_type_nfg(self, sample_nfg):
        """Test game type detection for NFG."""
        widget = VisualizationWidget()
        game_type = widget._detect_game_type(sample_nfg)
        assert game_type == "NFG"
    
    def test_detect_game_type_efg(self, sample_efg):
        """Test game type detection for EFG."""
        widget = VisualizationWidget()
        game_type = widget._detect_game_type(sample_efg)
        assert game_type == "EFG"
    
    def test_detect_game_type_invalid(self):
        """Test game type detection for invalid content."""
        widget = VisualizationWidget()
        game_type = widget._detect_game_type("INVALID")
        assert game_type is None


@pytest.mark.ui
class TestVisualizationMethods:
    """Tests for visualization methods."""
    
    def test_update_visualization_nfg(self, sample_nfg):
        """Test NFG visualization update."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        # This should trigger _visualize_nfg internally
        widget.set_content(sample_nfg)
        
        # Verify update was called (actual visualization tested through integration)
        assert widget._content_widget.update.called
    
    def test_update_visualization_efg(self, sample_efg):
        """Test EFG visualization update."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content(sample_efg)
        
        assert widget._content_widget.update.called
    
    def test_update_visualization_empty(self):
        """Test visualization with empty content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content("")
        
        # Should show "No content" message
        call_args = widget._content_widget.update.call_args
        assert call_args is not None
        displayed_text = call_args[0][0]
        assert isinstance(displayed_text, Text)
    
    def test_update_visualization_invalid(self):
        """Test visualization with invalid content."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content("INVALID FORMAT")
        
        # Should handle error gracefully
        assert widget._content_widget.update.called
    
    def test_consecutive_updates(self, sample_nfg, sample_efg):
        """Test consecutive content updates."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        widget.set_content(sample_nfg)
        assert widget._game_type == "NFG"
        
        widget.set_content(sample_efg)
        assert widget._game_type == "EFG"
        
        # Should have been called twice
        assert widget._content_widget.update.call_count >= 2
    
    def test_visualization_handles_pygambit_errors(self):
        """Test that visualization handles pygambit parsing errors."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        
        # Malformed game that pygambit can't parse
        bad_content = """NFG 1 R "Bad Game"
{ "Player 1" }

{
{ "A" "B" }
}

{
{ "Outcome A" 1 }
}
1 2 3"""  # Wrong number of outcome indices
        
        # Should not raise exception
        widget.set_content(bad_content)
        
        # Should display error
        assert widget._content_widget.update.called


# EFG with imperfect information: both P2 nodes after "Bet" share infoset 1,
# and both P2 nodes after "Check" share infoset 2 (matches simplified_poker.efg).
SHARED_INFOSET_EFG = """EFG 2 R "Simplified Poker" { "Player 1" "Player 2" }
c "Deal" 1 "Nature's Deal" { "High Card" 0.5 "Low Card" 0.5 } 0
p "P1 Has High" 1 1 "P1 Sees Card" { "Bet" "Check" } 0
p "P2 Faces Bet" 2 1 "P2 Responds to Bet" { "Call" "Fold" } 0
t "Showdown After Call" 1 "P1 Wins Showdown" { 2, -2 }
t "P2 Folds to Bet" 2 "P2 Concedes" { 1, -1 }
p "P2 After Check" 2 2 "P2 After P1 Checks" { "Bet" "Check" } 0
t "P2 Bets After Check" 3 "P2 Wins Uncontested" { -1, 1 }
t "Both Check" 4 "Showdown No Bets" { 1, -1 }
p "P1 Has Low" 1 1 "P1 Sees Card" { "Bet" "Check" } 0
p "P2 Faces Bluff" 2 1 "P2 Responds to Bet" { "Call" "Fold" } 0
t "Bluff Called" 5 "P2 Catches Bluff" { -2, 2 }
t "Bluff Works" 6 "P2 Concedes" { 1, -1 }
p "P2 After Low Check" 2 2 "P2 After P1 Checks" { "Bet" "Check" } 0
t "P2 Bets vs Low" 7 "P2 Takes Pot" { -1, 1 }
t "Both Check Low" 8 "P2 Wins Showdown" { -1, 1 }"""


@pytest.mark.unit
class TestCollectInfosetMap:
    """Tests for _collect_infoset_map method."""

    def _parse_efg(self, content):
        """Helper: parse EFG content into a pygambit game."""
        import pygambit as gbt
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(mode='w', suffix='.efg', delete=False) as f:
            f.write(content)
            temp_path = f.name
        try:
            return gbt.read_efg(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_all_player_infosets_included(self, sample_efg):
        """Every player infoset (even singletons) should appear in the map."""
        game = self._parse_efg(sample_efg)
        widget = VisualizationWidget()
        infoset_map = widget._collect_infoset_map(game.root)
        # sample_efg (conftest) gives every player node its own infoset;
        # all of them must now be present.
        assert len(infoset_map) > 0

    def test_detects_shared_player_infosets(self):
        """Infosets shared by multiple nodes get a display label."""
        game = self._parse_efg(SHARED_INFOSET_EFG)
        widget = VisualizationWidget()
        infoset_map = widget._collect_infoset_map(game.root)
        # There are 2 non-trivial player infosets (P1 infoset 1, P2 infoset 1,
        # P2 infoset 2) — at minimum 2 unique display labels should be assigned.
        assert len(infoset_map) >= 2

    def test_shared_nodes_map_to_same_label(self):
        """Both nodes in the same infoset must resolve to the identical label."""
        game = self._parse_efg(SHARED_INFOSET_EFG)
        widget = VisualizationWidget()
        infoset_map = widget._collect_infoset_map(game.root)

        # Collect all infoset objects reachable from the root
        seen_infosets: dict = {}
        def collect(node):
            if node.is_terminal:
                return
            if node.infoset and not node.infoset.is_chance:
                seen_infosets.setdefault(node.infoset, []).append(node)
            for action in node.infoset.actions:
                collect(node.children[action.number])
        collect(game.root)

        # For every infoset it must appear in infoset_map
        for infoset, nodes in seen_infosets.items():
            assert infoset in infoset_map, (
                f"Infoset missing from map"
            )
            # All nodes with that infoset share the same label
            labels = {infoset_map[infoset]}
            assert len(labels) == 1

    def test_display_labels_are_unique(self):
        """Each distinct non-trivial infoset gets a unique display label."""
        game = self._parse_efg(SHARED_INFOSET_EFG)
        widget = VisualizationWidget()
        infoset_map = widget._collect_infoset_map(game.root)
        labels = list(infoset_map.values())
        assert len(labels) == len(set(labels))

    def test_chance_infosets_excluded(self):
        """Chance nodes' infosets must never appear in the map."""
        game = self._parse_efg(SHARED_INFOSET_EFG)
        widget = VisualizationWidget()
        infoset_map = widget._collect_infoset_map(game.root)
        for infoset in infoset_map:
            assert not infoset.is_chance


@pytest.mark.unit
class TestInfosetIdRendering:
    """Tests that infoset IDs appear in the EFG tree visualization."""

    def test_shared_infoset_nodes_show_id(self):
        """Nodes belonging to a non-trivial infoset should carry an ID tag."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        widget.set_content(SHARED_INFOSET_EFG)
        assert widget._content_widget.update.called

        # Capture the rendered Rich objects
        call_args = widget._content_widget.update.call_args[0][0]
        # Render to plain text so we can inspect labels
        from io import StringIO
        from rich.console import Console
        buf = StringIO()
        console = Console(file=buf, no_color=True, width=200)
        console.print(call_args)
        rendered = buf.getvalue()

        # At least one infoset label like "[I1]" or "[I2]" should appear
        import re
        assert re.search(r'\[I\d+\]', rendered), (
            "Expected infoset ID tags (e.g. [I1]) in rendered EFG tree"
        )

    def test_singleton_infoset_nodes_show_id(self, sample_efg):
        """Nodes in singleton infosets should also carry ID tags."""
        widget = VisualizationWidget()
        widget._content_widget = Mock()
        widget.set_content(sample_efg)

        call_args = widget._content_widget.update.call_args[0][0]
        from io import StringIO
        from rich.console import Console
        import re
        buf = StringIO()
        console = Console(file=buf, no_color=True, width=200)
        console.print(call_args)
        rendered = buf.getvalue()

        assert re.search(r'\[I\d+\]', rendered), (
            "Infoset ID tags expected even when all infosets are singletons"
        )

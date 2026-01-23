"""Editor widget for game file editing."""

from typing import Optional, TYPE_CHECKING
from textual.widgets import Static, TextArea
from textual.containers import Vertical
from textual.message import Message
from rich.syntax import Syntax

if TYPE_CHECKING:
    from .chat_widget import ChatWidget
    from .visualization_widget import VisualizationWidget


class EditorWidget(Vertical):
    """Widget for game file editor."""
    
    DEFAULT_CSS = """
    EditorWidget {
        padding: 1;
    }
    
    #editor-title {
        dock: top;
        height: 1;
        content-align: center middle;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    
    #editor-area {
        height: 1fr;
        border: solid $primary;
    }
    """
    
    def __init__(self, **kwargs):
        """Initialize editor widget."""
        super().__init__(**kwargs)
        self.chat_widget: Optional['ChatWidget'] = None
        self.visualization_widget: Optional['VisualizationWidget'] = None
    
    def compose(self):
        """Create child widgets."""
        yield Static("Game File Editor", id="editor-title")
        yield TextArea(
            "",
            language="python",  # Closest syntax highlighting
            theme="monokai",
            show_line_numbers=True,
            id="editor-area"
        )
    
    def set_app_context(self, chat_widget: 'ChatWidget', visualization_widget: 'VisualizationWidget'):
        """Set application context.
        
        Args:
            chat_widget: ChatWidget instance.
            visualization_widget: VisualizationWidget instance.
        """
        self.chat_widget = chat_widget
        self.visualization_widget = visualization_widget
    
    def get_content(self) -> str:
        """Get current editor content.
        
        Returns:
            Editor content as string.
        """
        editor = self.query_one("#editor-area", TextArea)
        return editor.text
    
    def set_content(self, content: str):
        """Set editor content.
        
        Args:
            content: Content to set.
        """
        editor = self.query_one("#editor-area", TextArea)
        editor.text = content
        
        # Update visualization
        if self.visualization_widget:
            self.visualization_widget.set_content(content)
        
        # Update title based on content type
        if content.strip().startswith("NFG"):
            title = self.query_one("#editor-title", Static)
            title.update("Game File Editor - Strategic Form (.nfg)")
        elif content.strip().startswith("EFG"):
            title = self.query_one("#editor-title", Static)
            title.update("Game File Editor - Extensive Form (.efg)")
        else:
            title = self.query_one("#editor-title", Static)
            title.update("Game File Editor")
    
    def clear(self):
        """Clear editor content."""
        self.set_content("")
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text area changes.
        
        Args:
            event: TextArea changed event.
        """
        # Update visualization when user edits
        if self.visualization_widget:
            content = event.text_area.text
            self.visualization_widget.set_content(content)
        
        # Update title based on content type
        content = event.text_area.text.strip()
        title = self.query_one("#editor-title", Static)
        if content.startswith("NFG"):
            title.update("Game File Editor - Strategic Form (.nfg)")
        elif content.startswith("EFG"):
            title.update("Game File Editor - Extensive Form (.efg)")
        elif not content:
            title.update("Game File Editor")

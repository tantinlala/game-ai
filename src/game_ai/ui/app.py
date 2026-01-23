"""Main Textual application."""

import os
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer
from dotenv import load_dotenv

from .chat_widget import ChatWidget
from .editor_widget import EditorWidget
from .visualization_widget import VisualizationWidget
from ..ai.game_builder import GameBuilder
from ..chat.session_manager import SessionManager
from ..chat.command_handler import CommandHandler


class GameAIApp(App):
    """Main application for game theory builder."""
    
    # Enable mouse support but allow text selection with Shift
    ENABLE_COMMAND_PALETTE = False
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Horizontal {
        height: 1fr;
    }
    
    ChatWidget {
        width: 2fr;
        border-right: solid $primary;
    }
    
    EditorWidget {
        width: 2fr;
        border-right: solid $primary;
    }
    
    VisualizationWidget {
        width: 3fr;
    }
    """
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "save_session", "Save"),
        ("ctrl+l", "list_sessions", "List Sessions"),
        ("f1", "show_help", "Help"),
    ]
    
    def __init__(self, api_key: str = None):
        """Initialize app.
        
        Args:
            api_key: Optional Gemini API key override.
        """
        super().__init__()
        self.title = "Game AI - Game Theory Builder"
        self.api_key = api_key
        
        # Initialize components
        self.game_builder: GameBuilder = None
        self.session_manager: SessionManager = None
        self.command_handler: CommandHandler = None
        
        # References to widgets
        self.chat_widget: ChatWidget = None
        self.editor_widget: EditorWidget = None
        self.visualization_widget: VisualizationWidget = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        
        with Horizontal():
            yield ChatWidget(id="chat")
            yield EditorWidget(id="editor")
            yield VisualizationWidget(id="visualization")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted."""
        # Initialize components
        self.game_builder = GameBuilder(api_key=self.api_key)
        self.session_manager = SessionManager()
        self.command_handler = CommandHandler(self.session_manager)
        
        # Get widget references
        self.chat_widget = self.query_one("#chat", ChatWidget)
        self.editor_widget = self.query_one("#editor", EditorWidget)
        self.visualization_widget = self.query_one("#visualization", VisualizationWidget)
        
        # Connect widgets
        self.chat_widget.set_app_context(
            game_builder=self.game_builder,
            command_handler=self.command_handler,
            editor_widget=self.editor_widget,
            visualization_widget=self.visualization_widget
        )
        
        self.editor_widget.set_app_context(
            chat_widget=self.chat_widget,
            visualization_widget=self.visualization_widget
        )
        
        # Start conversation
        self.chat_widget.start_conversation()
    
    def action_save_session(self) -> None:
        """Action: Save current session."""
        self.chat_widget.trigger_save_command()
    
    def action_list_sessions(self) -> None:
        """Action: List saved sessions."""
        self.chat_widget.send_command("/list")
    
    def action_show_help(self) -> None:
        """Action: Show help."""
        self.chat_widget.send_command("/help")


def run_app(api_key: str = None):
    """Run the application.
    
    Args:
        api_key: Optional Gemini API key override.
    """
    # Load environment variables
    load_dotenv()
    
    # Get API key
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        print("Please set GEMINI_API_KEY environment variable or create a .env file.")
        print("See .env.example for reference.")
        return
    
    # Run app
    app = GameAIApp(api_key=api_key)
    app.run()

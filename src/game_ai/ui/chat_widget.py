"""Chat widget for conversation interface."""

from typing import Optional, TYPE_CHECKING
from textual.widgets import Static, Input, RichLog
from textual.containers import Vertical, ScrollableContainer
from textual.message import Message
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

if TYPE_CHECKING:
    from ..ai.game_builder import GameBuilder
    from ..chat.command_handler import CommandHandler
    from .editor_widget import EditorWidget


class ChatWidget(Vertical):
    """Widget for chat interface."""
    
    DEFAULT_CSS = """
    ChatWidget {
        padding: 1;
    }
    
    #message-container {
        height: 1fr;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    #input-field {
        dock: bottom;
    }
    """
    
    class MessageSent(Message):
        """Message sent when user submits input."""
        
        def __init__(self, message: str) -> None:
            self.message = message
            super().__init__()
    
    def __init__(self, **kwargs):
        """Initialize chat widget."""
        super().__init__(**kwargs)
        self.game_builder: Optional['GameBuilder'] = None
        self.command_handler: Optional['CommandHandler'] = None
        self.editor_widget: Optional['EditorWidget'] = None
        self.last_editor_content: str = ""
    
    def compose(self):
        """Create child widgets."""
        yield RichLog(id="message-container", wrap=True, highlight=True, markup=True)
        yield Input(
            placeholder="Type a message or /command...",
            id="input-field"
        )
    
    def set_app_context(
        self,
        game_builder: 'GameBuilder',
        command_handler: 'CommandHandler',
        editor_widget: 'EditorWidget'
    ):
        """Set application context.
        
        Args:
            game_builder: GameBuilder instance.
            command_handler: CommandHandler instance.
            editor_widget: EditorWidget instance.
        """
        self.game_builder = game_builder
        self.command_handler = command_handler
        self.editor_widget = editor_widget
    
    def start_conversation(self):
        """Start the conversation with AI greeting."""
        if not self.game_builder:
            return
        
        response = self.game_builder.start_conversation()
        self.display_assistant_message(response['text'], response.get('sources', []))
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        message = event.value.strip()
        
        if not message:
            return
        
        # Clear input
        input_widget = self.query_one("#input-field", Input)
        input_widget.value = ""
        
        # Display user message
        self.display_user_message(message)
        
        # Handle command or regular message
        if message.startswith('/'):
            self.handle_command(message)
        else:
            self.handle_user_message(message)
    
    def handle_command(self, command: str):
        """Handle slash command.
        
        Args:
            command: Command string.
        """
        if not self.command_handler or not self.game_builder:
            return
        
        context = {
            'conversation_history': self.game_builder.get_conversation_history(),
            'game_content': self.game_builder.current_game_content,
            'game_type': self.game_builder.game_type
        }
        
        result = self.command_handler.handle_command(command, context)
        
        # Display result
        if result['success']:
            self.display_system_message(result['message'])
        else:
            self.display_error_message(result['message'])
        
        # Handle special command results
        if 'data' in result:
            data = result['data']
            
            # Load session
            if 'conversation_history' in data:
                self.load_session(data)
            
            # Clear session
            if data.get('action') == 'clear':
                self.clear_session()
    
    def handle_user_message(self, message: str):
        """Handle regular user message.
        
        Args:
            message: User message.
        """
        if not self.game_builder or not self.editor_widget:
            return
        
        # Check for editor changes
        current_editor_content = self.editor_widget.get_content()
        file_diff = None
        
        if current_editor_content != self.last_editor_content and current_editor_content.strip():
            # Compute simple diff
            file_diff = f"Editor content updated:\n```\n{current_editor_content}\n```"
            self.last_editor_content = current_editor_content
        
        # Send to AI
        try:
            response = self.game_builder.send_message(message, file_diff=file_diff)
            
            # Update editor if new content
            if response.get('file_content'):
                self.editor_widget.set_content(response['file_content'])
                self.last_editor_content = response['file_content']
            
            # Display response
            self.display_assistant_message(response['text'], response.get('sources', []))
        
        except Exception as e:
            self.display_error_message(f"Error: {str(e)}")
    
    def display_user_message(self, message: str):
        """Display user message in chat.
        
        Args:
            message: User message.
        """
        log = self.query_one("#message-container", RichLog)
        
        panel = Panel(
            Text(message, style="bold cyan"),
            title="You",
            title_align="left",
            border_style="cyan"
        )
        log.write(panel)
    
    def display_assistant_message(self, message: str, sources: list = None):
        """Display assistant message in chat.
        
        Args:
            message: Assistant message.
            sources: Optional list of source dicts with 'title' and 'uri'.
        """
        log = self.query_one("#message-container", RichLog)
        
        # Format message with markdown
        content = Markdown(message)
        
        # Add sources if available
        if sources:
            sources_text = "\n\n**Sources:**\n"
            for source in sources:
                title = source.get('title', 'Unknown')
                uri = source.get('uri', '')
                sources_text += f"• [{title}]({uri})\n"
            content = Markdown(message + sources_text)
        
        panel = Panel(
            content,
            title="AI Assistant",
            title_align="left",
            border_style="green"
        )
        log.write(panel)
    
    def display_system_message(self, message: str):
        """Display system message in chat.
        
        Args:
            message: System message.
        """
        log = self.query_one("#message-container", RichLog)
        
        panel = Panel(
            Markdown(message),
            title="System",
            title_align="left",
            border_style="blue"
        )
        log.write(panel)
    
    def display_error_message(self, message: str):
        """Display error message in chat.
        
        Args:
            message: Error message.
        """
        log = self.query_one("#message-container", RichLog)
        
        panel = Panel(
            Markdown(message),
            title="Error",
            title_align="left",
            border_style="red"
        )
        log.write(panel)
    
    def send_command(self, command: str):
        """Programmatically send a command.
        
        Args:
            command: Command string (with leading /).
        """
        self.display_user_message(command)
        self.handle_command(command)
    
    def trigger_save_command(self):
        """Trigger save dialog (simplified version)."""
        # For now, just show the save command hint
        self.display_system_message(
            "To save your session, use: `/save <session_name>`\n"
            "Example: `/save my_game_session`"
        )
    
    def load_session(self, session_data: dict):
        """Load a session.
        
        Args:
            session_data: Session data dict.
        """
        if not self.game_builder or not self.editor_widget:
            return
        
        # Load into game builder
        self.game_builder.load_conversation(
            history=session_data.get('conversation_history', []),
            game_content=session_data.get('game_content', ''),
            game_type=session_data.get('game_type')
        )
        
        # Update editor
        if session_data.get('game_content'):
            self.editor_widget.set_content(session_data['game_content'])
            self.last_editor_content = session_data['game_content']
        
        # Replay conversation history in UI
        log = self.query_one("#message-container", RichLog)
        log.clear()
        
        for msg in session_data.get('conversation_history', []):
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'user':
                self.display_user_message(content)
            else:
                self.display_assistant_message(content)
    
    def clear_session(self):
        """Clear current session."""
        if not self.game_builder or not self.editor_widget:
            return
        
        # Clear chat log
        log = self.query_one("#message-container", RichLog)
        log.clear()
        
        # Clear editor
        self.editor_widget.set_content("")
        self.last_editor_content = ""
        
        # Start new conversation
        self.start_conversation()

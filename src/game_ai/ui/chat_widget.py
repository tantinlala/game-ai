"""Chat widget for conversation interface."""

from typing import Optional, TYPE_CHECKING
from textual.widgets import Static, Input, RichLog
from textual.containers import Vertical, ScrollableContainer
from textual.message import Message
from textual import work
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from ..game.validator import GameValidator

if TYPE_CHECKING:
    from ..ai.game_builder import GameBuilder
    from ..chat.command_handler import CommandHandler
    from .editor_widget import EditorWidget
    from .visualization_widget import VisualizationWidget


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
        self.visualization_widget: Optional['VisualizationWidget'] = None
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
        editor_widget: 'EditorWidget',
        visualization_widget: 'VisualizationWidget'
    ):
        """Set application context.
        
        Args:
            game_builder: GameBuilder instance.
            command_handler: CommandHandler instance.
            editor_widget: EditorWidget instance.
            visualization_widget: VisualizationWidget instance.
        """
        self.game_builder = game_builder
        self.command_handler = command_handler
        self.editor_widget = editor_widget
        self.visualization_widget = visualization_widget
    
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
        if not self.command_handler or not self.game_builder or not self.editor_widget:
            return
        
        # Get current editor content (reflects any manual edits)
        current_editor_content = self.editor_widget.get_content()
        
        # Detect game type from editor content
        game_type = None
        if current_editor_content.strip().startswith("NFG"):
            game_type = "nfg"
        elif current_editor_content.strip().startswith("EFG"):
            game_type = "efg"
        
        context = {
            'conversation_history': self.game_builder.get_conversation_history(),
            'game_content': current_editor_content,  # Use live editor content
            'game_type': game_type
        }
        
        result = self.command_handler.handle_command(command, context)
        
        # Display result
        if result['success']:
            if result['message']:  # Only display if there's a message
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
            
            # Generate game file
            if data.get('action') == 'generate':
                prompt = data.get('prompt', 'Generate or update the game file.')
                self.handle_generate_request(prompt)
    
    def handle_user_message(self, message: str):
        """Handle regular user message.
        
        Args:
            message: User message.
        """
        if not self.game_builder or not self.editor_widget:
            return
        
        # Show loading indicator
        self.show_loading()
        
        # Check for editor changes
        current_editor_content = self.editor_widget.get_content()
        file_diff = None
        
        if current_editor_content != self.last_editor_content and current_editor_content.strip():
            # Compute simple diff
            file_diff = f"Editor content updated:\n```\n{current_editor_content}\n```"
            self.last_editor_content = current_editor_content
        
        # Send to AI (run async)
        self.process_ai_response(message, file_diff, generate_game_file=False)
    
    def handle_generate_request(self, prompt: str):
        """Handle /generate command to create/update game file.
        
        Args:
            prompt: Optional prompt or description for generation.
        """
        print(f"[DEBUG] handle_generate_request called with prompt: '{prompt}'")
        if not self.game_builder or not self.editor_widget:
            print("[DEBUG] Missing game_builder or editor_widget")
            return
        
        # Show loading indicator
        self.show_loading()
        
        # Check for editor changes
        current_editor_content = self.editor_widget.get_content()
        file_diff = None
        
        if current_editor_content != self.last_editor_content and current_editor_content.strip():
            # Compute simple diff
            file_diff = f"Editor content updated:\n```\n{current_editor_content}\n```"
            self.last_editor_content = current_editor_content
        
        # Send to AI with game generation flag (run async)
        # Initial generation uses main history, not temp history
        print(f"[DEBUG] Calling process_ai_response with prompt: '{prompt}'")
        print(f"[DEBUG] generate_game_file=True, is_validation_fix=False, file_diff={'present' if file_diff else 'None'}")
        self.process_ai_response(prompt, file_diff, generate_game_file=True, is_validation_fix=False)
    
    @work(exclusive=True)
    async def process_ai_response(self, message: str, file_diff: Optional[str], generate_game_file: bool = False, max_validation_attempts: int = 3, is_validation_fix: bool = False):
        """Process AI response asynchronously.
        
        Args:
            message: User message.
            file_diff: Optional file diff.
            generate_game_file: Whether to generate/update game file.
            max_validation_attempts: Maximum attempts to fix validation errors.
            is_validation_fix: If True, this is a validation error fix (use temp history).
        """
        print(f"[DEBUG] process_ai_response started")
        print(f"[DEBUG] message: '{message}'")
        print(f"[DEBUG] generate_game_file={generate_game_file}, is_validation_fix={is_validation_fix}, max_attempts={max_validation_attempts}")
        try:
            # For validation fixes, use temp history. For initial generation, use main history.
            response = self.game_builder.send_message(
                message, 
                file_diff=file_diff,
                generate_game_file=generate_game_file,
                use_temp_history=is_validation_fix  # Only use temp history for validation fixes
            )
            
            print(f"[DEBUG] Received response from game_builder")
            print(f"[DEBUG] Response keys: {list(response.keys())}")
            print(f"[DEBUG] Has file_content: {'file_content' in response}")
            if 'file_content' in response:
                print(f"[DEBUG] file_content length: {len(response.get('file_content', ''))}")
                print(f"[DEBUG] file_content first 100 chars: {response.get('file_content', '')[:100]}")
            
            # Hide loading indicator
            self.hide_loading()
            
            # Update editor if new content
            if response.get('file_content'):
                print(f"[DEBUG] Setting editor content (length: {len(response['file_content'])})")
                self.editor_widget.set_content(response['file_content'])
                self.last_editor_content = response['file_content']
            else:
                print(f"[DEBUG] No file_content in response or it's empty")
            
            # If we generated a game file, validate it
            if generate_game_file:
                file_content = response.get('file_content', '')
                print(f"[DEBUG] Starting validation (file_content length: {len(file_content)})")
                errors = GameValidator.validate(file_content)
                print(f"[DEBUG] Validation returned {len(errors) if errors else 0} errors: {errors[:2] if errors else 'None'}")
                
                # Use helper method to determine action based on validation results
                validation_result = self.handle_validation_result(file_content, errors, max_validation_attempts)
                
                if validation_result['should_retry']:
                    print(f"[DEBUG] Validation failed, requesting fix (attempts remaining: {max_validation_attempts})")
                    # Display validation errors
                    self.display_error_message(validation_result['error_text'])
                    
                    # Automatically request fix from AI
                    self.display_system_message(f"Requesting AI to fix validation errors... (attempt {validation_result['attempt_number']}/3)")
                    
                    # Request corrected version with decremented attempts
                    self.request_game_fix(validation_result['fix_prompt'], max_validation_attempts - 1)
                    return  # Don't display original response since we're getting a fix
                elif errors:
                    # Max attempts reached
                    self.display_error_message(validation_result['error_text'])
                    self.display_system_message("You can manually edit the file to fix errors or try /generate again.")
                else:
                    # Validation passed - only now display success
                    self.display_system_message("✓ Game file generated and validated successfully!")
                    # Clear temp history after successful generation
                    self.game_builder.clear_temp_history()
                
                # Don't display AI message during generation
                return
            
            # Display response only for non-generation messages
            if not generate_game_file:
                self.display_assistant_message(response['text'], response.get('sources', []))
        
        except Exception as e:
            self.hide_loading()
            self.display_error_message(f"Error: {str(e)}")
    
    def request_game_fix(self, fix_prompt: str, max_attempts: int = 3):
        """Request AI to fix validation errors in generated game file.
        
        Args:
            fix_prompt: Prompt with error details.
            max_attempts: Maximum validation attempts remaining.
        """
        # Trigger another generation with the fix prompt using temp history
        self.process_ai_response(fix_prompt, None, generate_game_file=True, max_validation_attempts=max_attempts, is_validation_fix=True)
    
    def handle_validation_result(self, file_content: str, errors: list, max_validation_attempts: int) -> dict:
        """Handle validation results and determine next action.
        
        Args:
            file_content: The game file content that was validated.
            errors: List of validation errors.
            max_validation_attempts: Maximum validation attempts remaining.
            
        Returns:
            dict with keys:
                - 'should_retry': bool - whether to retry generation
                - 'error_text': str - formatted error message
                - 'fix_prompt': str - prompt for fixing errors (if retrying)
                - 'attempt_number': int - current attempt number (1-3)
        """
        result = {
            'should_retry': False,
            'error_text': '',
            'fix_prompt': '',
            'attempt_number': 0  # Will be set correctly if there are errors
        }
        
        if not errors:
            # Validation passed - attempt_number stays 0
            return result
        
        # We have errors - calculate actual attempt number
        result['attempt_number'] = 4 - max_validation_attempts
        
        # Format error message
        if max_validation_attempts > 0:
            error_text = "**Validation Errors Found:**\n\n"
        else:
            error_text = "**Validation Errors (max attempts reached):**\n\n"
        
        for error in errors:
            error_text += f"• {str(error)}\n"
        
        result['error_text'] = error_text
        
        # Determine if we should retry
        if max_validation_attempts > 0:
            result['should_retry'] = True
            result['fix_prompt'] = f"""The game file has validation errors. Please fix them:

{error_text}

Here's the current game file:
```
{file_content}
```

Please provide a corrected version."""
        
        return result
    
    def show_loading(self):
        """Show loading indicator while waiting for AI response."""
        log = self.query_one("#message-container", RichLog)
        
        # Create a loading panel with animated dots
        loading_text = Text("●●●", style="dim green")
        panel = Panel(
            loading_text,
            title="AI Assistant",
            title_align="left",
            border_style="dim green"
        )
        log.write(panel)
    
    def hide_loading(self):
        """Hide loading indicator."""
        # The loading message will be replaced by the actual response
        # so we don't need to explicitly remove it
        pass
    
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
    
    def display_assistant_message(self, message: str, sources: Optional[list] = None):
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
        
        # Update visualization
        if session_data.get('game_content') and self.visualization_widget:
            self.visualization_widget.set_content(session_data['game_content'])
        
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
        
        # Clear visualization
        if self.visualization_widget:
            self.visualization_widget.clear()
        
        # Start new conversation
        self.start_conversation()

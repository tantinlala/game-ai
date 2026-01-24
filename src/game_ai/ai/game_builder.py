"""Game builder orchestrating AI-assisted game construction."""

from typing import Dict, List, Optional, Any
from .gemini_client import GeminiClient
from .prompts import (
    SYSTEM_PROMPT,
    FILE_EDIT_PROMPT
)


class GameBuilder:
    """Orchestrates AI-assisted game construction."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize game builder.
        
        Args:
            api_key: Gemini API key.
        """
        self.client = GeminiClient(api_key)
        self.conversation_history: List[Dict[str, str]] = []
        self.temp_conversation_history: List[Dict[str, str]] = []  # For validation loops
        self.current_game_content: str = ""
        self.game_type: Optional[str] = None  # 'nfg' or 'efg'
        
    def start_conversation(self) -> Dict[str, Any]:
        """Start a new conversation for building a game.
        
        Returns:
            Dict with AI's initial message.
        """
        self.conversation_history = []
        self.current_game_content = ""
        self.game_type = None
        
        # Fixed welcome message
        welcome_message = """Welcome to Game AI! 🎮

I'll help you build game theory models in strategic form (.nfg) or extensive form (.efg) format, and we can compute Nash equilibria together.

**To get started, tell me:**
- What type of game do you want to create?
  - **Strategic form** (normal form) for simultaneous move games
  - **Extensive form** (game tree) for sequential move games
- What is your game about?
- Who are the players?

**Example prompts:**
- "I want to create a prisoner's dilemma game"
- "Build a sequential entry game with two firms"
- "Create a coordination game about technology standards"

**Available commands:**
Type `/help` at any time to see available commands like `/solve`, `/save`, `/validate`, etc.

**Editor Tips:**
- Drag and then use ctrl+c to copy text.
- Use ctrl+z and ctrl+y to undo/redo edits.

Let's build your game!"""
        
        self.conversation_history.append({
            "role": "assistant",
            "content": welcome_message
        })
        
        return {
            "text": welcome_message,
            "sources": []
        }
    
    def send_message(
        self,
        user_message: str,
        file_diff: Optional[str] = None,
        generate_game_file: bool = False,
        use_temp_history: bool = False
    ) -> Dict[str, Any]:
        """Send a user message and get AI response.
        
        Args:
            user_message: The user's message.
            file_diff: Optional diff of file edits made by user.
            generate_game_file: Whether to generate/update the game file (use structured output).
            use_temp_history: If True, use temporary history that won't persist (for validation loops).
            
        Returns:
            Dict with AI response text, sources, and updated file content.
        """
        # If there's a file diff, prepend it to the message
        if file_diff:
            context_message = FILE_EDIT_PROMPT.format(diff=file_diff)
            augmented_message = f"User's game file edits:\n\n{context_message}\n\nUser's message:\n\n{user_message}"
        else:
            augmented_message = user_message
        
        # Choose which history to use
        if use_temp_history:
            # For temp history (validation loops), initialize with recent context from main history
            # This gives the AI context about what game is being built
            if not self.temp_conversation_history and self.conversation_history:
                # Copy the last few messages from main history to give context
                # Skip the welcome message, get conversation context
                context_messages = [msg for msg in self.conversation_history[1:] if msg["role"] == "user" or "game" in msg["content"].lower()][-5:]
                self.temp_conversation_history = context_messages.copy() if context_messages else []
            history = self.temp_conversation_history
        else:
            history = self.conversation_history
        
        # Add user message to appropriate history
        history.append({
            "role": "user",
            "content": augmented_message
        })
        
        # Generate response
        try:
            response = self.client.generate_response(
                messages=history,
                system_prompt=SYSTEM_PROMPT,
                use_grounding=not generate_game_file,  # Use grounding unless generating game file
                use_structured_output=generate_game_file  # Use structured output only when generating
            )
        except Exception as e:
            # Remove the user message from history if generation failed
            history.pop()
            raise RuntimeError(f"Failed to generate AI response: {str(e)}")
        
        # Add assistant response to appropriate history
        history.append({
            "role": "assistant",
            "content": response["text"]
        })
        
        # Use structured game_file from response if provided
        if response.get("game_file"):
            file_content = response["game_file"].strip()
            if file_content:  # Only update if not empty
                self.current_game_content = file_content
                # Detect game type from content
                if file_content.startswith("NFG"):
                    self.game_type = "nfg"
                elif file_content.startswith("EFG"):
                    self.game_type = "efg"
        
        return {
            "text": response["text"],
            "sources": response["sources"],
            "file_content": self.current_game_content if self.current_game_content else "",
            "game_type": self.game_type
        }
    
    def update_file_content(self, content: str):
        """Update the current game file content.
        
        Args:
            content: New file content.
        """
        self.current_game_content = content
        
        # Detect game type
        if content.strip().startswith("NFG"):
            self.game_type = "nfg"
        elif content.strip().startswith("EFG"):
            self.game_type = "efg"
    
    def clear_temp_history(self):
        """Clear the temporary conversation history used for validation loops."""
        self.temp_conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history.
        
        Returns:
            List of message dicts.
        """
        return self.conversation_history
    
    def load_conversation(self, history: List[Dict[str, str]], 
                         game_content: str, game_type: Optional[str]):
        """Load a saved conversation.
        
        Args:
            history: Conversation history.
            game_content: Current game file content.
            game_type: Game type ('nfg' or 'efg').
        """
        self.conversation_history = history
        self.current_game_content = game_content
        self.game_type = game_type

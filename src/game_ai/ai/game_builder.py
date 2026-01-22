"""Game builder orchestrating AI-assisted game construction."""

from typing import Dict, List, Optional, Any
from .gemini_client import GeminiClient
from .prompts import (
    SYSTEM_PROMPT,
    GAME_TYPE_PROMPT,
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
        
        # Get initial greeting
        response = self.client.generate_response(
            messages=[{"role": "user", "content": GAME_TYPE_PROMPT}],
            system_prompt=SYSTEM_PROMPT,
            use_grounding=False
        )
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response["text"]
        })
        
        return {
            "text": response["text"],
            "sources": response["sources"]
        }
    
    def send_message(
        self,
        user_message: str,
        file_diff: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a user message and get AI response.
        
        Args:
            user_message: The user's message.
            file_diff: Optional diff of file edits made by user.
            
        Returns:
            Dict with AI response text, sources, and updated file content.
        """
        # If there's a file diff, prepend it to the message
        if file_diff:
            context_message = FILE_EDIT_PROMPT.format(diff=file_diff)
            augmented_message = f"{context_message}\n\nUser's message: {user_message}"
        else:
            augmented_message = user_message
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": augmented_message
        })
        
        # Generate response
        try:
            response = self.client.generate_response(
                messages=self.conversation_history,
                system_prompt=SYSTEM_PROMPT,
                use_grounding=True
            )
        except Exception as e:
            # Remove the user message from history if generation failed
            self.conversation_history.pop()
            raise RuntimeError(f"Failed to generate AI response: {str(e)}")
        
        # Add assistant response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response["text"]
        })
        
        # Extract game file content if present in response
        file_content = self._extract_game_file(response["text"])
        if file_content:
            self.current_game_content = file_content
            # Detect game type from content
            if file_content.strip().startswith("NFG"):
                self.game_type = "nfg"
            elif file_content.strip().startswith("EFG"):
                self.game_type = "efg"
        
        return {
            "text": response["text"],
            "sources": response["sources"],
            "file_content": self.current_game_content,
            "game_type": self.game_type
        }
    
    def _extract_game_file(self, text: str) -> Optional[str]:
        """Extract game file content from AI response.
        
        Args:
            text: AI response text.
            
        Returns:
            Extracted file content or None.
        """
        # Look for code blocks with game content
        import re
        
        # Try to find code blocks
        code_block_pattern = r"```(?:nfg|efg|gambit)?\n(.*?)```"
        matches = re.findall(code_block_pattern, text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            content = match.strip()
            # Check if it looks like a game file
            if content.startswith("NFG") or content.startswith("EFG"):
                return content
        
        # Also check for lines that start with NFG or EFG without code blocks
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith(("NFG", "EFG")):
                # Extract from this line onwards until we hit non-game content
                game_lines = []
                for j in range(i, len(lines)):
                    current_line = lines[j]
                    # Stop at markdown, explanatory text, or empty lines after content
                    if j > i and (current_line.startswith('#') or 
                                 current_line.startswith('**') or
                                 (not current_line.strip() and game_lines)):
                        break
                    game_lines.append(current_line)
                
                if game_lines:
                    return '\n'.join(game_lines).strip()
        
        return None
    
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

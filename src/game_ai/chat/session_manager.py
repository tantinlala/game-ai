"""Session management for saving and loading conversations."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class SessionManager:
    """Manages session persistence."""
    
    def __init__(self, session_dir: Optional[str] = None):
        """Initialize session manager.
        
        Args:
            session_dir: Directory to store sessions. Defaults to ~/.game-ai/sessions
        """
        if session_dir:
            self.session_dir = Path(session_dir)
        else:
            self.session_dir = Path.home() / ".game-ai" / "sessions"
        
        # Create directory if it doesn't exist
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(
        self,
        name: str,
        conversation_history: List[Dict[str, str]],
        game_content: str,
        game_type: Optional[str]
    ) -> bool:
        """Save a session to disk.
        
        Args:
            name: Session name.
            conversation_history: List of conversation messages.
            game_content: Current game file content.
            game_type: Game type ('nfg' or 'efg').
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            session_data = {
                'name': name,
                'saved_at': datetime.now().isoformat(),
                'conversation_history': conversation_history,
                'game_content': game_content,
                'game_type': game_type
            }
            
            # Sanitize filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            filepath = self.session_dir / f"{safe_name}.json"
            
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def load_session(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a session from disk.
        
        Args:
            name: Session name.
            
        Returns:
            Session data dict or None if not found.
        """
        try:
            # Sanitize filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            filepath = self.session_dir / f"{safe_name}.json"
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                session_data = json.load(f)
            
            return session_data
        
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def list_sessions(self) -> List[Dict[str, str]]:
        """List all saved sessions.
        
        Returns:
            List of session info dicts with 'name' and 'saved_at' keys.
        """
        sessions = []
        
        try:
            for filepath in self.session_dir.glob("*.json"):
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        'name': data.get('name', filepath.stem),
                        'saved_at': data.get('saved_at', 'Unknown'),
                        'game_type': data.get('game_type', 'Unknown')
                    })
                except Exception:
                    continue
        
        except Exception as e:
            print(f"Error listing sessions: {e}")
        
        # Sort by saved_at descending
        sessions.sort(key=lambda x: x['saved_at'], reverse=True)
        
        return sessions
    
    def delete_session(self, name: str) -> bool:
        """Delete a session.
        
        Args:
            name: Session name.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Sanitize filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            filepath = self.session_dir / f"{safe_name}.json"
            
            if filepath.exists():
                filepath.unlink()
                return True
            
            return False
        
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    def export_game_file(self, content: str, filepath: str) -> bool:
        """Export game file to specified path.
        
        Args:
            content: Game file content.
            filepath: Destination file path.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            path = Path(filepath)
            
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                f.write(content)
            
            return True
        
        except Exception as e:
            print(f"Error exporting file: {e}")
            return False

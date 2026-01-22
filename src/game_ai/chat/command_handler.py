"""Command handler for slash commands."""

from typing import Dict, Any, Optional, Callable
from .session_manager import SessionManager
from ..game.solver import GameSolver
from ..game.validator import GameValidator


class CommandHandler:
    """Handles slash commands in chat interface."""
    
    def __init__(self, session_manager: SessionManager):
        """Initialize command handler.
        
        Args:
            session_manager: Session manager instance.
        """
        self.session_manager = session_manager
        self.commands: Dict[str, Callable] = {
            'help': self.cmd_help,
            'save': self.cmd_save,
            'load': self.cmd_load,
            'list': self.cmd_list,
            'solve': self.cmd_solve,
            'export': self.cmd_export,
            'clear': self.cmd_clear,
            'validate': self.cmd_validate,
        }
    
    def handle_command(
        self,
        command_line: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a slash command.
        
        Args:
            command_line: Full command line (e.g., "/save my_game").
            context: Context dict with 'conversation_history', 'game_content', 'game_type'.
            
        Returns:
            Result dict with 'success', 'message', and optional 'data' keys.
        """
        # Parse command
        parts = command_line[1:].split(maxsplit=1)  # Remove leading '/'
        command = parts[0].lower() if parts else ''
        args = parts[1] if len(parts) > 1 else ''
        
        # Execute command
        if command in self.commands:
            return self.commands[command](args, context)
        else:
            return {
                'success': False,
                'message': f"Unknown command: /{command}. Type /help for available commands."
            }
    
    def cmd_help(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Show help for available commands."""
        help_text = """**Available Commands:**

• `/help` - Show this help message
• `/save <name>` - Save current session with given name
• `/load <name>` - Load a saved session
• `/list` - List all saved sessions
• `/solve` - Compute Nash equilibria for current game
• `/validate` - Validate current game file syntax
• `/export <path>` - Export game file to disk (e.g., /export game.nfg)
• `/clear` - Clear current session and start fresh

**Tips:**
- Manual edits to the game file are sent as context with your next message
- Use `/validate` before `/solve` to check for errors
- Save your work frequently with `/save`
"""
        return {
            'success': True,
            'message': help_text
        }
    
    def cmd_save(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Save current session."""
        if not args.strip():
            return {
                'success': False,
                'message': "Please provide a session name: `/save <name>`"
            }
        
        name = args.strip()
        
        success = self.session_manager.save_session(
            name=name,
            conversation_history=context.get('conversation_history', []),
            game_content=context.get('game_content', ''),
            game_type=context.get('game_type')
        )
        
        if success:
            return {
                'success': True,
                'message': f"Session saved as '{name}'"
            }
        else:
            return {
                'success': False,
                'message': f"Failed to save session '{name}'"
            }
    
    def cmd_load(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Load a saved session."""
        if not args.strip():
            return {
                'success': False,
                'message': "Please provide a session name: `/load <name>`"
            }
        
        name = args.strip()
        session_data = self.session_manager.load_session(name)
        
        if session_data:
            return {
                'success': True,
                'message': f"Session '{name}' loaded successfully",
                'data': session_data
            }
        else:
            return {
                'success': False,
                'message': f"Session '{name}' not found. Use `/list` to see available sessions."
            }
    
    def cmd_list(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """List all saved sessions."""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            return {
                'success': True,
                'message': "No saved sessions found."
            }
        
        message = "**Saved Sessions:**\n\n"
        for session in sessions:
            saved_at = session['saved_at'][:19] if len(session['saved_at']) >= 19 else session['saved_at']
            game_type = session.get('game_type', 'Unknown').upper()
            message += f"• **{session['name']}** ({game_type}) - {saved_at}\n"
        
        message += f"\nTotal: {len(sessions)} session(s)\nUse `/load <name>` to load a session."
        
        return {
            'success': True,
            'message': message,
            'data': {'sessions': sessions}
        }
    
    def cmd_solve(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Solve current game for Nash equilibria."""
        game_content = context.get('game_content', '').strip()
        
        if not game_content:
            return {
                'success': False,
                'message': "No game file to solve. Create a game first through conversation."
            }
        
        # Validate first
        errors = GameValidator.validate(game_content)
        if errors:
            error_text = "**Game file has validation errors:**\n\n"
            for error in errors[:5]:  # Show first 5 errors
                error_text += f"• {str(error)}\n"
            
            if len(errors) > 5:
                error_text += f"\n...and {len(errors) - 5} more error(s)"
            
            error_text += "\n\nFix these errors before solving. Use `/validate` for details."
            
            return {
                'success': False,
                'message': error_text
            }
        
        # Solve game
        result = GameSolver.solve_from_content(game_content)
        
        if not result.is_success():
            return {
                'success': False,
                'message': f"**Solver Error:**\n\n{result.error}"
            }
        
        if not result.equilibria:
            return {
                'success': False,
                'message': "No Nash equilibria found."
            }
        
        # Format results
        message = "**Nash Equilibria Found:**\n\n"
        message += f"Game: {result.game_info.get('title', 'Untitled')}\n"
        message += f"Players: {', '.join(result.game_info.get('players', []))}\n"
        message += f"Total equilibria: {len(result.equilibria)}\n\n"
        
        for i, eq in enumerate(result.equilibria, 1):
            eq_type = "Pure Strategy" if eq['is_pure'] else "Mixed Strategy"
            message += f"**Equilibrium {i}** ({eq_type}):\n\n"
            
            # Show strategies
            for player, strategies in eq['strategies'].items():
                message += f"• **{player}:**\n"
                for strategy, prob in strategies.items():
                    if prob > 0.001:  # Only show non-zero probabilities
                        if eq['is_pure']:
                            message += f"  - {strategy}\n"
                        else:
                            message += f"  - {strategy}: {prob:.1%}\n"
            
            # Show payoffs if available
            if eq['payoffs']:
                message += "\n**Payoffs:**\n"
                for player, payoff in eq['payoffs'].items():
                    message += f"  - {player}: {payoff:.4f}\n"
            
            message += "\n"
        
        return {
            'success': True,
            'message': message,
            'data': {'result': result}
        }
    
    def cmd_export(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Export game file to disk."""
        if not args.strip():
            return {
                'success': False,
                'message': "Please provide a file path: `/export <path>` (e.g., `/export game.nfg`)"
            }
        
        filepath = args.strip()
        game_content = context.get('game_content', '').strip()
        
        if not game_content:
            return {
                'success': False,
                'message': "No game file to export. Create a game first through conversation."
            }
        
        success = self.session_manager.export_game_file(game_content, filepath)
        
        if success:
            return {
                'success': True,
                'message': f"Game file exported to: {filepath}"
            }
        else:
            return {
                'success': False,
                'message': f"Failed to export game file to: {filepath}"
            }
    
    def cmd_clear(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Clear current session."""
        return {
            'success': True,
            'message': "Session cleared. Starting fresh!",
            'data': {'action': 'clear'}
        }
    
    def cmd_validate(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate current game file."""
        game_content = context.get('game_content', '').strip()
        
        if not game_content:
            return {
                'success': False,
                'message': "No game file to validate. Create a game first through conversation."
            }
        
        errors = GameValidator.validate(game_content)
        
        if not errors:
            game_type = "Strategic Form (.nfg)" if game_content.startswith("NFG") else "Extensive Form (.efg)"
            return {
                'success': True,
                'message': f"✓ Game file is valid! ({game_type})"
            }
        
        error_text = "**Validation Errors:**\n\n"
        for error in errors:
            error_text += f"• {str(error)}\n"
        
        return {
            'success': False,
            'message': error_text
        }

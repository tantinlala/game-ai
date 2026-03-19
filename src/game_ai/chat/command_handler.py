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
            'fix': self.cmd_fix,
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
• `/solve [solver] [summary]` - Compute Nash equilibria for current game
  - Optional solvers: `enumpure`, `enummixed`, `lcp`, `lp`, `liap`, `gnm`
  - Optional `summary`: Add `summary` to get AI explanation
  - Example: `/solve lcp summary` or just `/solve summary`
• `/fix` - Fix current game file syntax
• `/export <path>` - Export game file to disk (e.g., /export game.nfg)
• `/clear` - Clear current session and start fresh

**Available Solvers:**
• `enumpure` - Pure strategy enumeration (all games)
• `enummixed` - Mixed strategy enumeration (2-player)
• `lcp` - Linear complementarity (2-player, most reliable)
• `lp` - Linear programming (2-player zero-sum)
• `liap` - Lyapunov minimization (N-player)
• `gnm` - Global Newton method (N-player)

**Tips:**
- Manual edits to the game file are sent as context with your next message
- Use `/fix` before `/solve` to check for errors
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
            message += f"- **{session['name']}** ({game_type}) - {saved_at}\n"
        
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
        
        # Parse solver and summary arguments if provided
        request_summary = False
        solver = None
        
        args_parts = args.strip().split()
        for part in args_parts:
            if part.lower() == 'summary':
                request_summary = True
            elif solver is None:  # First non-summary part is treated as solver
                solver = part
        
        # Fix/Check for errors first
        errors = GameValidator.validate(game_content)
        if errors:
            error_text = "**Game file has fix errors:**\n\n"
            for error in errors[:5]:  # Show first 5 errors
                error_text += f"• {str(error)}\n"
            
            if len(errors) > 5:
                error_text += f"\n...and {len(errors) - 5} more error(s)"
            
            error_text += "\n\nFix these errors before solving. Use `/fix` for details."
            
            return {
                'success': False,
                'message': error_text
            }
        
        # Solve game with optional solver
        result = GameSolver.solve_from_content(game_content, solver=solver)
        
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
        
        # Format results with improved readability
        message = "## 🎯 Nash Equilibria Found\n\n"
        
        # Game info summary
        message += f"**Game:** {result.game_info.get('title', 'Untitled')}\n"
        message += f"\n**Players:** {', '.join(result.game_info.get('players', []))}\n"
        
        # Game properties
        props = []
        if result.game_info.get('num_players'):
            props.append(f"{result.game_info['num_players']}-player")
        if result.game_info.get('is_const_sum'):
            props.append("constant-sum")
        if result.game_info.get('is_perfect_recall') is False:
            props.append("imperfect recall")
        
        if props:
            message += f"\n**Properties:** {', '.join(props)}\n"
        
        message += f"\n**Found:** {len(result.equilibria)} equilibrium/equilibria\n"
        message += "\n" + "─" * 50 + "\n\n"
        
        # Detect if this is an EFG game
        is_efg = game_content.startswith("EFG")
        
        for i, eq in enumerate(result.equilibria, 1):
            eq_type = "🎲 Pure Strategy" if eq['is_pure'] else "🎰 Mixed Strategy"
            message += f"### {eq_type} Equilibrium"
            if len(result.equilibria) > 1:
                message += f" #{i}"
            message += "\n\n"
            
            # For EFG pure strategies, show as sequence of events
            if is_efg and eq['is_pure']:
                message += "**Equilibrium Strategy:**\n\n"
                
                # Collect all active strategies grouped by player
                player_actions = {}
                for player, strategies in eq['strategies'].items():
                    active_strats = [(s, p) for s, p in strategies.items() if p > 0.99]
                    player_actions[player] = active_strats
                
                # Display each player's strategy with information sets clearly grouped
                for player, active_strats in player_actions.items():
                    if not active_strats:
                        continue
                    
                    message += f"**{player}:**\n```\n"
                    
                    for strategy, _ in active_strats:
                        # Format: infoset → action
                        if ':' in strategy:
                            infoset, action = strategy.split(':', 1)
                            # Show infoset label and action more clearly
                            message += f"  At {infoset:20} → {action}\n"
                        else:
                            message += f"  {strategy}\n"
                    
                    message += "```\n"
            else:
                # Show strategies in a cleaner format (for NFG or mixed EFG)
                message += "**Equilibrium Strategy:**\n\n"
                
                for player, strategies in eq['strategies'].items():
                    message += f"**{player}:**\n"
                    
                    active_strats = [(s, p) for s, p in strategies.items() if p > 0.001]
                    
                    if eq['is_pure']:
                        # For pure strategies, show the chosen strategy
                        chosen = [s for s, p in active_strats if p > 0.99]
                        if chosen:
                            message += "```\n"
                            for c in chosen:
                                # Check if this is an EFG strategy with infoset
                                if ':' in c:
                                    infoset, action = c.split(':', 1)
                                    message += f"  At {infoset:20} → {action}\n"
                                else:
                                    message += f"  {c}\n"
                            message += "```\n"
                    else:
                        # For mixed strategies, show probability distribution
                        message += "```\n"
                        for strategy, prob in sorted(active_strats, key=lambda x: -x[1]):
                            # Check if this is an EFG strategy with infoset
                            if is_efg and ':' in strategy:
                                infoset, action = strategy.split(':', 1)
                                # Create visual bar (scale to 30 chars for better granularity)
                                bar_length = int(prob * 30)
                                bar = "█" * bar_length
                                # Format: infoset and action with probability
                                message += f"  At {infoset:20} → {action:15} {bar:<30} {prob*100:>5.1f}%\n"
                            else:
                                # Create visual bar (scale to 30 chars for better granularity)
                                bar_length = int(prob * 30)
                                bar = "█" * bar_length
                                # Format: strategy name, bar, percentage
                                message += f"  {strategy:<25} {bar:<30} {prob*100:>5.1f}%\n"
                        message += "```\n"
            
            # Show payoffs in a cleaner table-like format
            if eq['payoffs']:
                message += "\n**Expected Payoffs:**\n\n"
                for player, payoff in eq['payoffs'].items():
                    message += f"  • {player:<20} {payoff:>8.4f}\n\n"
            
            if i < len(result.equilibria):
                message += "\n" + "─" * 50 + "\n\n"
            else:
                message += "\n\n"
        
        return {
            'success': True,
            'message': message,
            'data': {
                'result': result,
                'request_summary': request_summary
            }
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
    
    def cmd_fix(self, args: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix/Check current game file."""
        game_content = context.get('game_content', '').strip()
        
        if not game_content:
            return {
                'success': False,
                'message': "No game file to fix. Create a game first through conversation."
            }
        
        errors = GameValidator.validate(game_content)
        
        if not errors:
            game_type = "Strategic Form (.nfg)" if game_content.startswith("NFG") else "Extensive Form (.efg)"
            return {
                'success': True,
                'message': f"✓ Game file is valid! ({game_type})"
            }
        
        error_text = "**Fix Errors:**\n\n"
        for error in errors:
            error_text += f"• {str(error)}\n"
        
        return {
            'success': False,
            'message': error_text
        }

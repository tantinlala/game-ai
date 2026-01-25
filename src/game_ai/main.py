"""Main entry point for Game AI application."""

import sys
import argparse
from .ui.app import run_app


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Game AI - AI-powered game theory builder in the terminal",
        epilog="""
For detailed command reference and tutorials, see: https://github.com/tantinlala/game-ai
Type /help inside the application for a list of all available slash commands.
"""
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='Gemini API key (overrides GEMINI_API_KEY env var)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='game-ai 0.1.0'
    )
    
    args = parser.parse_args()
    
    try:
        run_app(api_key=args.api_key)
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Game AI

AI-powered game theory builder for creating strategic form (.nfg) and extensive form (.efg) games using natural language chat interface.

## Features

- Interactive terminal UI with split-pane view (chat + editor)
- AI-assisted game construction with Gemini API
- Google Search grounding for real-world numeric data
- PyGambit integration for Nash equilibrium computation
- Session save/load functionality
- Live .efg/.nfg file editing with context sync

## Installation

```bash
pip install -e .
```

## Configuration

Create a `.env` file with your Gemini API key:

```
GEMINI_API_KEY=your_api_key_here
```

## Usage

```bash
game-ai
```

## Commands

- `/help` - Show available commands
- `/save <name>` - Save current session
- `/load <name>` - Load saved session
- `/solve` - Compute Nash equilibria
- `/export <path>` - Export game file to disk
- `/clear` - Clear current session

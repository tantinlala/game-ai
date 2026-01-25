# Game AI

AI-powered game theory builder for creating strategic form (.nfg) and extensive form (.efg) games using natural language chat interface.

## Features

- Interactive terminal UI with split-pane view (chat + editor)
- AI-assisted game construction with Gemini API
- Google Search grounding for real-world numeric data
- PyGambit integration for Nash equilibrium computation
- Session save/load functionality
- Live .efg/.nfg file editing with context sync
- **Comprehensive test coverage for all modules**

## Installation

See [QUICKSTART.md](QUICKSTART.md) for detailed installation instructions and environment setup.

```bash
# Quick install for development
pip install -e .
```

## Configuration

Create a `.env` file with your Gemini API key (see [QUICKSTART.md](QUICKSTART.md#configure-api-key) for details):

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
- `/list` - List all saved sessions
- `/solve` - Compute Nash equilibria
- `/fix` - Fix game file syntax
- `/export <path>` - Export game file to disk
- `/clear` - Clear current session

## Development

### Running Tests

The project uses `pytest` for testing. See [TEST_COVERAGE.md](TEST_COVERAGE.md) for a detailed list of all 134 test cases.


```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_solver.py

# Run tests by marker
pytest -m unit          # Unit tests only
pytest -m ui            # UI widget tests only

# Run with coverage report (terminal + HTML)
pytest tests/ --cov=game_ai --cov-report=term --cov-report=html
```

**Total Test Coverage**: Comprehensive test coverage across all core modules.

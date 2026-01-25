# Game AI

AI-powered game theory builder for creating strategic form (.nfg) and extensive form (.efg) games using natural language chat interface.

## Features

- Interactive terminal UI with split-pane view (chat + editor)
- AI-assisted game construction with Gemini API
- Google Search grounding for real-world numeric data
- PyGambit integration for Nash equilibrium computation
- Session save/load functionality
- Live .efg/.nfg file editing with context sync
- **Comprehensive test coverage with 127 unit tests**

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

## Development

### Running Tests

The project includes comprehensive test coverage with pytest:

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
```

**Test Coverage**: 127 tests covering all modules
- ✅ 10 tests for game validator
- ✅ 13 tests for Nash equilibrium solver
- ✅ 10 tests for session manager
- ✅ 19 tests for command handler
- ✅ 16 tests for visualization widget
- ✅ 17 tests for editor widget
- ✅ 16 tests for chat widget
- ✅ 13 tests for game builder
- ✅ 15 tests for Gemini client

See [TEST_COVERAGE.md](TEST_COVERAGE.md) for detailed test documentation.

"""Setup script for game-ai package."""

from setuptools import setup, find_packages

with open("README.md", "w") as f:
    f.write("""# Game AI

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
""")

setup(
    name="game-ai",
    version="0.1.0",
    description="AI-powered game theory builder with Nash equilibrium solver",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/tantinlala/game-ai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "pygambit>=16.1.0",
        "google-genai>=1.0.0",
        "textual>=0.50.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "game-ai=game_ai.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

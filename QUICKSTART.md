# Quick Start Guide

Get started with Game AI in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

## Installation

1. **Clone and setup**:
   ```bash
   git clone https://github.com/tantinlala/game-ai.git
   cd game-ai
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install package
   pip install -e .
   ```

2. **Configure API key**:
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env and add your API key
   # GEMINI_API_KEY=your_actual_key_here
   ```

## First Run

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the application
game-ai
```

## Your First Game

Once the app starts, you'll see a split-pane interface:

### Step 1: Start Building
Type in the chat (left pane):
```
I want to create a prisoner's dilemma game
```

### Step 2: Follow AI Guidance
The AI will ask you questions like:
- Who are the players?
- What strategies can they choose?
- What are the payoffs?

Answer naturally:
```
Two prisoners: Alice and Bob
Each can either Cooperate or Defect
If both cooperate: each gets 3 years
If one defects: defector goes free, other gets 5 years
If both defect: each gets 1 year
```

### Step 3: View the Game
Watch the right pane populate with the .nfg file as you build!

### Step 4: Solve It
```
/solve
```

The AI will compute and display Nash equilibria with probabilities and payoffs.

### Step 5: Save Your Work
```
/save my_first_game
```

## Example Commands

Try these in the chat:

- `/help` - See all commands
- `/fix` - Fix game file syntax
- `/export game.nfg` - Save to file
- `/list` - See saved sessions
- `/load my_first_game` - Resume work

## Tips

1. **Edit Manually**: You can edit the game file directly in the right pane
2. **Real Data**: Ask AI to find real-world numbers (e.g., "What's the profit margin for retail?")
3. **Iterate**: Build games step-by-step, the AI remembers context
4. **Fix First**: Use `/fix` before `/solve` to catch errors

## Example Prompts

- "Create a 2-player coordination game about technology standards"
- "Build a sequential entry game for a new market"
- "Make a pricing competition game with 3 companies"
- "Create a simplified poker game with betting"

## Keyboard Shortcuts

- `Ctrl+Q` - Quit
- `Ctrl+S` - Save prompt
- `Ctrl+L` - List sessions
- `F1` - Help

## Troubleshooting

**API Key Issues?**
```bash
# Check if .env file exists
cat .env

# Or set directly
export GEMINI_API_KEY=your_key_here
game-ai
```

**Import Errors?**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate
pip install -e .
```

**No Equilibria Found?**
- Use `/fix` to check for errors
- Some complex games may not converge
- Try simplifying the game structure

## Next Steps

- Explore [examples/](examples/) for sample games
- Read the full [README.md](README.md) for details
- Learn about [.nfg and .efg formats](examples/README.md)

## Need Help?

- Type `/help` in the app
- Check [README.md](README.md) for detailed docs
- Visit the [GitHub repository](https://github.com/tantinlala/game-ai)

Happy game building! 🎮

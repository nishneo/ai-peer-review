# AI Peer Review

A collaborative AI deliberation system where multiple language models review and validate each other's responses to give you the best possible answer.

## How It Works

Instead of relying on a single AI, AI Peer Review assembles a panel of diverse language models that work together through a structured 3-stage process:

### Stage 1: Independent Analysis
Your query is sent to all panel members simultaneously. Each AI provides its independent perspective without seeing others' responses.

### Stage 2: Peer Review
Each AI reviews and ranks all responses (anonymized to prevent bias). This cross-evaluation reveals consensus and highlights different viewpoints.

### Stage 3: Synthesis
A designated synthesizer AI compiles the best insights from all responses and rankings into a comprehensive final answer.

## Why AI Peer Review?

- **Diverse perspectives**: Different AI models have different strengths and training biases
- **Reduced hallucination**: Cross-validation between models catches errors
- **Transparent reasoning**: See exactly how each model thinks and ranks others
- **Best-of-all-worlds**: Final synthesis combines the strongest elements

## Setup

### 1. Install Dependencies

The project uses [uv](https://docs.astral.sh/uv/) for Python package management.

**Backend:**
```bash
uv sync
```

**Frontend:**
```bash
cd frontend
npm install
cd ..
```

### 2. Configure API Key

Create a `.env` file in the project root:

```bash
OPENROUTER_API_KEY=sk-or-v1-...
```

Get your API key at [openrouter.ai](https://openrouter.ai/).

### 3. Configure Models (Optional)

Edit `backend/config.py` to customize your panel:

```python
PANEL_MODELS = [
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4",
    "google/gemini-2.5-flash",
    "x-ai/grok-3",
]

SYNTHESIZER_MODEL = "anthropic/claude-sonnet-4"
```

## Running the Application

**Option 1: Use the start script**
```bash
./start.sh
```

**Option 2: Run manually**

Terminal 1 (Backend):
```bash
uv run python -m backend.main
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Then open http://localhost:5173 in your browser.

## Deployment

See `render.yaml` for one-click deployment to Render (free tier available).

## Tech Stack

- **Backend:** FastAPI (Python 3.10+), async httpx, OpenRouter API
- **Frontend:** React + Vite, react-markdown for rendering
- **Storage:** JSON files in `data/conversations/`
- **Package Management:** uv for Python, npm for JavaScript

## License

MIT

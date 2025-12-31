# Seefast Backend

AI-powered data visualization agent backend using LangGraph and FastAPI.

## Features

- 🤖 **LangGraph Agent** - Stateful AI agent with tool-calling
- 🔍 **Semantic Search** - ChromaDB for API endpoint discovery
- 💾 **Caching** - Redis with in-memory fallback
- 💬 **Conversation Memory** - Context across turns
- 📊 **Auto-formatting** - Raw API data → Widgets

## Tech Stack

- **FastAPI** - API framework
- **LangGraph** - Agent orchestration
- **LangChain OpenAI** - LLM integration
- **ChromaDB** - Vector database
- **Redis** - Caching
- **Sentence Transformers** - Embeddings

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Start Redis (optional)
docker run -d -p 6379:6379 redis:alpine

# 5. Run server
uvicorn app.main:app --reload
```

Server runs at http://localhost:8000

## Project Structure

```
app/
├── main.py              # FastAPI entry + startup
├── config.py            # Settings (env vars)
├── api/
│   └── routes.py        # API endpoints
├── agent/
│   ├── core.py          # Agent entry point
│   ├── graph.py         # LangGraph definition
│   ├── tools.py         # Agent tools
│   ├── memory.py        # Conversation memory
│   ├── state.py         # State definition
│   └── prompts.py       # System prompts
├── adapters/
│   └── swagger_parser.py # OpenAPI parser
├── registry/
│   └── endpoint_registry.py # ChromaDB endpoint store
└── services/
    └── cache.py         # Redis cache
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/query` | Send query to agent |
| GET | `/api/sessions/{id}` | Get session info |
| GET | `/health` | Health check |
| GET | `/docs` | OpenAPI docs |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `OPENAI_MODEL` | Model to use | `gpt-4o` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `SWAGGER_URL` | API spec URL | Petstore |

## How It Works

```
User Query
    ↓
┌─────────────────┐
│  Load Context   │ ← Conversation memory
└────────┬────────┘
         ↓
┌─────────────────┐
│  LangGraph      │
│  Agent Loop:    │
│  • search_endpoints
│  • get_endpoint_schema
│  • call_api
│  • format_for_widget
└────────┬────────┘
         ↓
┌─────────────────┐
│  Format Output  │ → Widgets JSON
└────────┬────────┘
         ↓
Response { message, widgets[] }
```

## License

MIT

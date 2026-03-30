# Agent Harness Backend

A production-ready agentic AI framework with 5-tier memory, project isolation, and autonomous task execution.

## Quick Start

```bash
# Install dependencies
pip install fastapi uvicorn httpx pydantic-settings cryptography

# Set environment variables
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.openai.com/v1"
export LLM_MODEL="gpt-4o"
export DATA_DIR="/var/lib/agent-harness"

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Architecture

### Core Modules

**config.py**
- Centralized settings management via environment variables
- Database path configuration
- LLM provider settings
- Security and authentication configuration

**main.py**
- FastAPI application factory
- CORS middleware setup
- Startup/shutdown event handlers
- Health check endpoints

### Agent Module (`agent/`)

**personality.py**
- Load and manage soul.md and agent.md files
- Support for global and per-project personality overrides
- Personality merging logic

**prompts.py**
- System prompt assembly from multiple sources
- Integration of personality, project context, and memories
- Timestamp injection

**core.py**
- Main agent loop (AgentCore class)
- Streaming message processing
- Tool call iteration and accumulation
- Working memory management

**tools.py**
- 10 built-in tools with OpenAI function schemas
- Tool dispatcher (execute_tool)
- Path-safe workspace access
- Web search integration

### LLM Integration (`models/`)

**provider.py**
- OpenAI-compatible LLM API wrapper
- Streaming and non-streaming chat completions
- Tool/function calling support
- Embedding endpoints
- Automatic error handling and retries

**discovery.py**
- Fetch available models from LLM endpoint

### Security (`secrets/`)

**vault.py**
- Fernet-encrypted secrets storage
- SQLite-backed persistent vault
- PBKDF2 key derivation
- In-memory cache with TTL

## Memory Architecture

The system supports five tiers of memory:

1. **Working Memory** - Current conversation context (in-memory)
2. **Episodic Memory** - Specific facts and conversation records
3. **Semantic Memory** - General knowledge and insights
4. **Graph Memory** - Relationship networks and concepts
5. **Archival Memory** - Long-form documents and complete context

See `data/personality/agent.md` for detailed memory usage guidelines.

## File Structure

```
backend/
├── config.py              # Configuration management
├── main.py                # FastAPI application
├── agent/
│   ├── core.py            # Agent loop
│   ├── personality.py     # Personality management
│   ├── prompts.py         # System prompt assembly
│   └── tools.py           # Tool definitions
├── models/
│   ├── provider.py        # LLM provider
│   └── discovery.py       # Model discovery
├── secrets/
│   └── vault.py           # Encrypted secrets
├── api/                   # API routes (placeholder)
├── memory/                # Memory tier implementations (placeholder)
├── tasks/                 # Task scheduler (placeholder)
├── telegram/              # Telegram bot (placeholder)
└── data/
    └── personality/
        ├── soul.md        # Agent personality definition
        └── agent.md       # Agent configuration guide
```

## Environment Variables

```bash
# LLM Configuration
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

# Security
VAULT_MASTER_KEY=your-master-key-min-32-chars
SECRET_KEY=your-secret-key

# Application
APP_ENV=development
LOG_LEVEL=INFO
DATA_DIR=/var/lib/agent-harness
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_ALLOWED_CHAT_IDS=123456,789012

# ChromaDB (optional)
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

## API Endpoints

### Health
- `GET /health` - Health check
- `GET /` - Root endpoint with documentation link

### Chat (to be implemented)
- `POST /api/chat` - Send message to agent
- `WebSocket /api/chat/stream` - Streaming chat

### Memory (to be implemented)
- `POST /api/memory` - Store memory
- `GET /api/memory/recall` - Retrieve memories

### Personality (to be implemented)
- `GET /api/personality` - Get current personality
- `PUT /api/personality` - Update personality

### Projects (to be implemented)
- `POST /api/projects` - Create project
- `GET /api/projects` - List projects

## Built-in Tools

The agent has access to 10 tools:

1. **remember** - Store information across memory tiers
2. **recall** - Search memories for relevant information
3. **create_graph_node** - Create nodes in relationship graph
4. **link_concepts** - Link nodes with relationships
5. **read_file** - Read from workspace
6. **write_file** - Write to workspace
7. **list_workspace_files** - List workspace contents
8. **web_search** - Search via DuckDuckGo
9. **create_task** - Schedule autonomous tasks
10. **send_telegram** - Send notifications to operator

## Personality

The agent has two configuration files:

**soul.md** - Core personality and values
- Transparency and epistemic humility
- Curiosity-driven approach
- Proactive memory management
- Professional but warm tone

**agent.md** - Operational guidelines
- Memory tier usage guidelines
- Project isolation rules
- Workspace management
- Escalation policies
- Tool best practices

## Security Considerations

- Path traversal prevention in file access
- Secrets encrypted at rest with Fernet
- API keys never logged
- PBKDF2-derived encryption keys (100k iterations)
- In-memory cache with automatic expiration
- Workspace sandboxing per project

## Type Hints

All code uses Python 3.10+ type hints:
- `from __future__ import annotations` for forward references
- Full type coverage on functions and methods
- Pydantic models for validation

## Error Handling

- Comprehensive try/except blocks
- Detailed logging with context
- Graceful fallbacks (e.g., zero vector for failed embeddings)
- HTTP error details in responses

## Performance

- Async/await throughout (no blocking I/O)
- Streaming chat completions
- In-memory working memory (fast context retrieval)
- Encrypted secret caching (300-second TTL)
- Efficient tool iteration (max 10 rounds)

## Testing

Run syntax validation:
```bash
python3 -m py_compile config.py main.py agent/*.py models/*.py secrets/*.py
```

## Next Steps

1. Implement memory tier backends in `memory/`
2. Build API routes in `api/`
3. Add task scheduler in `tasks/`
4. Integrate Telegram bot in `telegram/`
5. Add comprehensive test suite
6. Create Docker deployment configuration

## Documentation

- `data/personality/soul.md` - Agent personality
- `data/personality/agent.md` - Operational guidelines
- `BUILD_SUMMARY.txt` - Detailed build information

## License

Proprietary - Agent Harness Framework

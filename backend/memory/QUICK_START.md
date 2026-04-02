# Quick Start Guide

## Installation

The memory system is self-contained. Copy the `memory/` directory to your project:

```bash
cp -r memory/ /path/to/agent-harness/backend/
```

## Basic Usage

```python
import asyncio
from memory.manager import MemoryManager

async def main():
    # Create manager
    manager = MemoryManager(
        project_id="my-project",
        session_id="session-123"
    )
    
    # Add to working memory (fast, in-context)
    manager.working.add_message("user", "Hello!")
    
    # Store semantic knowledge
    await manager.remember(
        "Alice is the project lead",
        tier="semantic"
    )
    
    # Store episodic event
    await manager.remember(
        "Completed API design review",
        tier="episodic"
    )
    
    # Recall from all tiers
    results = await manager.recall("who is in charge?")
    for r in results:
        print(f"[{r['tier']}] {r['content']} (score: {r.get('score', 'N/A')})")
    
    # At session end, consolidate
    summary = await manager.consolidate_session()
    print(summary)

asyncio.run(main())
```

## Common Scenarios

### Scenario 1: Remember a Fact
```python
# Store permanently
await manager.remember(
    "Our API uses OAuth 2.0 for authentication",
    tier="semantic"
)

# Later, retrieve
results = await manager.recall("what auth method do we use?")
```

### Scenario 2: Track a Conversation
```python
# Add each turn to working memory
manager.working.add_message("user", "Build an API")
manager.working.add_message("assistant", "I can help...")

# Get recent context
messages = manager.working.get_messages()
```

### Scenario 3: Build a Knowledge Graph
```python
# Create entities
api_id = await manager.graph.add_node("concept", "REST API")
db_id = await manager.graph.add_node("concept", "PostgreSQL")

# Connect them
await manager.graph.add_edge(api_id, db_id, "uses_database")

# Find relationships
related = await manager.graph.find_related(api_id)
```

### Scenario 4: Save Project Notes
```python
# Append timestamped note
filename = await manager.archival.append_note(
    "Decision: Use async/await throughout"
)

# Later, list all notes
notes = await manager.archival.list_notes()
for note in notes:
    print(note['filename'])
```

## Data Directory Structure

After first use:

```
data/
├── episodic.db        (SQLite - conversation history)
├── graph.db           (SQLite - relationships)
├── chroma/            (ChromaDB - vectors)
│   └── default/
├── personality/       (System prompts & personality)
└── projects/
    └── my-project/
        ├── notes/
        └── project_summary.md
```

## API Quick Reference

### MemoryManager
- `remember(content, tier, metadata)` → store
- `recall(query, tiers, project_id)` → search all tiers
- `audit_memory(tier, project_id)` → retrieve all for tier
- `consolidate_session()` → move working to semantic
- `set_active_project(project_id)` → switch projects

### WorkingMemory
- `add_message(role, content, metadata)` → add to buffer
- `get_messages(as_dicts)` → retrieve all
- `get_token_count()` → estimate tokens used
- `peek_recent(n)` → get last n messages
- `clear()` → flush all
- `len()` → number of messages

### EpisodicMemory
- `save_message(session_id, project_id, role, content)` → store turn
- `get_history(session_id, limit)` → retrieve session
- `get_sessions(project_id, limit)` → list sessions
- `search_messages(query, project_id)` → full-text search
- `log_task_event(task_id, event)` → record event
- `add_note(content, project_id)` → save note
- `get_notes(project_id)` → retrieve notes

### SemanticMemory
- `store(content, metadata)` → save with embedding
- `search(query, n)` → semantic search
- `list_memories(limit)` → get all vectors
- `count()` → number of stored memories
- `delete(doc_id)` → remove

### GraphMemory
- `add_node(node_type, label, metadata)` → create entity
- `add_edge(node_a_id, node_b_id, relationship)` → create link
- `add_edge_by_label(label_a, label_b, relationship)` → link by name
- `find_related(node_id, depth)` → multi-hop search
- `get_path(label_a, label_b)` → find connection
- `list_nodes(node_type, limit)` → retrieve all
- `search_nodes(query)` → text search entities

### ArchivalMemory
- `read_file(path)` → load file
- `write_file(path, content)` → save file
- `append_note(content, filename)` → add timestamped note
- `list_notes()` → all notes for project
- `get_project_summary()` → read summary
- `update_project_summary(content)` → write summary

## Async/Await Required

All I/O operations are async:

```python
# Always use await
msg_id = await manager.episodic.save_message(...)

# Combine with asyncio
results = await asyncio.gather(
    manager.semantic.search("query1"),
    manager.semantic.search("query2"),
    manager.graph.find_related(node_id)
)
```

## Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now see detailed logs
manager.working.add_message("user", "test")
# > Working memory: 1 messages, ~200 tokens
```

## Performance Tips

1. **Working Memory**: Regularly call `consolidate_session()` to keep token count low
2. **Episodic Search**: Use indexed date ranges with `search_by_date()`
3. **Semantic Search**: Batch searches with `asyncio.gather()`
4. **Graph Traversal**: Limit depth to 2-3 to avoid explosion
5. **Archival**: Keep notes organized with consistent filenames

## Common Errors

**"ChromaDB connection failed"**
→ Fallback to local persistent triggered, check logs

**"Path outside allowed directories"**
→ Only use relative paths like "notes/myfile.md", not absolute paths

**"No messages to consolidate"**
→ Add messages to working memory first

## Next Steps

1. Read [README.md](README.md) for architecture details
2. Check source files for docstrings and type hints
3. Run tests with `python -m pytest memory/`
4. Integrate with your agent's main loop

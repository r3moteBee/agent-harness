# Agent-Harness 5-Tier Memory System

A complete, production-grade memory architecture for AI agents with five distinct tiers, each optimized for specific use cases and performance characteristics.

## Overview

The 5-tier memory system provides persistent context retention, semantic knowledge storage, associative reasoning, and long-term archival for agent-based systems.

```
┌─────────────────────────────────────────────────────┐
│  Tier 1: Working Memory (In-context, ~8KB)         │
│  Fast, recent conversation buffer with tokens       │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Tier 2: Episodic Memory (SQLite, indexed)          │
│  Persistent conversation history & task logs        │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Tier 3: Semantic Memory (ChromaDB, vectors)        │
│  Embeddings for similarity search & knowledge base  │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Tier 4: Graph Memory (SQLite, relationships)       │
│  Concept networks and entity relationships          │
└─────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Tier 5: Archival Memory (File-based)               │
│  Long-term summaries and personality profiles       │
└─────────────────────────────────────────────────────┘
```

## Tier Details

### Tier 1: Working Memory (working.py)

**Purpose**: In-context conversation buffer  
**Backend**: Python deque (in-memory)  
**Performance**: O(1) add/retrieve  
**Capacity**: ~8,000 tokens (configurable)  

Fast rolling buffer for recent conversation history. Automatically evicts old messages when exceeding token budget.

```python
working = WorkingMemory(max_tokens=8000, max_messages=50)
working.add_message("user", "Hello!")
messages = working.get_messages()  # Returns list of recent messages
```

### Tier 2: Episodic Memory (episodic.py)

**Purpose**: Persistent conversation history and task logs  
**Backend**: SQLite  
**Performance**: O(log n) indexed search  
**Capacity**: Unlimited (disk-bound)  

Stores all messages, conversations, task events, and notes with full-text search capabilities.

```python
episodic = EpisodicMemory(db_path="data/episodic.db")
await episodic.save_message(session_id, project_id, "user", "content")
history = await episodic.get_history(session_id)
results = await episodic.search_messages("keyword", project_id)
```

**Schema**:
- `conversations`: Session metadata and grouping
- `messages`: Individual conversation turns
- `task_logs`: Timestamped events (started, completed, failed)
- `memory_notes`: Hand-written notes with tagging

### Tier 3: Semantic Memory (semantic.py)

**Purpose**: Vector embeddings for semantic search  
**Backend**: ChromaDB (with fallback to local persistent)  
**Performance**: O(1) vector similarity search  
**Capacity**: Millions of vectors  

Stores embeddings of facts, insights, and summaries for semantic recall.

```python
semantic = SemanticMemory(project_id="default")
doc_id = await semantic.store("Machine learning is ...", metadata={"type": "fact"})
results = await semantic.search("what is ML?", n=5)
# Returns: [{"id": "...", "content": "...", "score": 0.95, ...}]
```

**Features**:
- Automatic embedding via ChromaDB default (or custom embedding function)
- Cosine distance for similarity (converted to 0-1 score)
- Per-project namespacing
- HTTP or local persistent backends

### Tier 4: Graph Memory (graph.py)

**Purpose**: Associative knowledge graph for multi-hop reasoning  
**Backend**: SQLite with graph tables  
**Performance**: O(n) per hop, BFS path finding  
**Capacity**: Unlimited nodes and relationships  

Represents entities (concepts, people, projects) and their relationships.

```python
graph = GraphMemory(project_id="default")
alice_id = await graph.add_node("person", "Alice", metadata={"role": "engineer"})
project_id = await graph.add_node("project", "ProjectX")
await graph.add_edge(alice_id, project_id, "works_on")

# Find what Alice is related to
related = await graph.find_related(alice_id, depth=2)

# Find path from Alice to ProjectX
path = await graph.get_path("Alice", "ProjectX")
```

**Node Types**: `concept`, `person`, `project`, `event`, `fact`

### Tier 5: Archival Memory (archival.py)

**Purpose**: Long-term file-based storage  
**Backend**: Filesystem (Markdown, JSON, plain text)  
**Performance**: O(1) sequential read, O(1) append  
**Capacity**: Bounded by disk  

Persistent profiles, summaries, and personality settings loaded into system prompts.

```python
archival = ArchivalMemory(project_id="default")

# Append notes
filename = await archival.append_note("Learned: Alice prefers async APIs")

# Read/write files
await archival.write_file("notes/project_summary.md", "# ProjectX\n...")
content = await archival.read_file("notes/project_summary.md")

# List all notes
notes = await archival.list_notes()
```

**Structure**:
```
data/
  personality/          # Shared personality settings
  projects/
    {project_id}/
      notes/            # Timestamped markdown notes
      project_summary.md
```

## Memory Manager (manager.py)

Central orchestration for all 5 tiers.

```python
from memory.manager import MemoryManager

manager = MemoryManager(project_id="my-app", session_id="sess_123")

# Store in any tier
await manager.remember("Alice is the lead", tier="semantic")
await manager.remember("Task completed", tier="episodic")

# Recall from multiple tiers
results = await manager.recall("who is the lead?", tiers=["semantic", "episodic"])

# Audit mode: retrieve all memories for a tier
audit = await manager.audit_memory("semantic")

# Consolidate session at end
summary = await manager.consolidate_session()

# Switch projects
manager.set_active_project("other-project")
```

## Usage Patterns

### Pattern 1: Recent Context (Tier 1)
```python
# Add to working memory for immediate context
manager.working.add_message("user", "Let's build a REST API")
messages = manager.working.get_messages()
# Use in next API call to Claude
```

### Pattern 2: Session Recall (Tier 2)
```python
# Get full conversation history from previous session
history = await manager.episodic.get_history(session_id="old-session")
# Reconstruct context
```

### Pattern 3: Semantic Search (Tier 3)
```python
# Store facts as you learn them
await manager.remember("REST APIs use HTTP verbs", tier="semantic")

# Later: retrieve relevant knowledge
results = await manager.recall("how do I design an API?", tiers=["semantic"])
```

### Pattern 4: Relationship Queries (Tier 4)
```python
# Build knowledge graph
await manager.graph.add_node("concept", "REST")
await manager.graph.add_node("concept", "HTTP")
await manager.graph.add_edge_by_label("REST", "HTTP", "uses_protocol")

# Find related concepts
related = await manager.graph.find_related(rest_node_id)

# Navigate paths
path = await manager.graph.get_path("REST", "HTTP")
```

### Pattern 5: Persistent Personality (Tier 5)
```python
# Update personality file
personality = """
# Agent Personality

- Prefers async/await patterns
- Favors Python over JavaScript
- Emphasizes testing and documentation
"""
await manager.archival.write_file("personality/preferences.md", personality)

# Load for system prompt at startup
personality_text = await manager.archival.read_file("personality/preferences.md")
# Include in system prompt
```

## Configuration

All tiers use sensible defaults but can be configured:

```python
# Working Memory
working = WorkingMemory(max_tokens=12000, max_messages=100)

# Episodic Memory
episodic = EpisodicMemory(db_path="/custom/path/episodic.db")

# Semantic Memory (ChromaDB server)
semantic = SemanticMemory(project_id="default")
# Falls back to local persistent if ChromaDB server unavailable

# Graph Memory
graph = GraphMemory(project_id="default", db_path="/custom/path/graph.db")

# Archival Memory
archival = ArchivalMemory(project_id="default", base_dir="/custom/data")
```

## Performance Characteristics

| Tier | Read | Write | Search | Capacity | Cost |
|------|------|-------|--------|----------|------|
| 1 Working | O(1) | O(1) | O(n) | ~8K tokens | Memory |
| 2 Episodic | O(log n) | O(1) | O(log n) | Unlimited | Disk |
| 3 Semantic | O(1)* | O(1) | O(1)* | Millions | GPU (vector DB) |
| 4 Graph | O(n/hop) | O(1) | O(n) | Unlimited | Disk |
| 5 Archival | O(1) | O(1) | O(n) | Disk | Disk |

*Vector similarity is approximate but constant time in practice

## Error Handling

All async methods handle exceptions gracefully:

```python
try:
    results = await manager.recall("query")
except Exception as e:
    logger.error(f"Recall failed: {e}")
    # Falls back to other tiers automatically
```

## Concurrency

- Tier 1 (Working): Not thread-safe, designed for single-threaded use
- Tiers 2-4 (SQLite): Thread-safe via SQLite's built-in locking
- Tier 3 (ChromaDB): Handled by ChromaDB's concurrency model
- Tier 5 (Files): Simple file operations, atomic writes recommended

## Testing

```python
import asyncio
from memory.manager import MemoryManager

async def test_memory():
    manager = MemoryManager(project_id="test", session_id="test_1")
    
    # Test Tier 1
    manager.working.add_message("user", "Hello")
    assert len(manager.working) == 1
    
    # Test Tier 2
    await manager.episodic.add_note("Test note", "default", "test_1")
    notes = await manager.episodic.get_notes("default")
    assert len(notes) > 0
    
    # Test Tier 3
    doc_id = await manager.semantic.store("Test content")
    assert doc_id
    
    # Test Tier 4
    node_id = await manager.graph.add_node("concept", "Test")
    assert node_id
    
    # Test Tier 5
    await manager.archival.append_note("Test archival")
    notes = await manager.archival.list_notes()
    assert len(notes) > 0

asyncio.run(test_memory())
```

## Architecture Notes

1. **No External Dependencies (Tiers 1-2, 4-5)**: SQLite is stdlib, file I/O is built-in
2. **Optional ChromaDB (Tier 3)**: Vector search only if chromadb is installed
3. **Graceful Degradation**: Falls back to local persistent ChromaDB if server unavailable
4. **Project Namespacing**: All tiers support multi-project isolation
5. **Async Throughout**: All I/O operations are async-ready
6. **Type Hints**: Full type annotations for IDE support

## Future Enhancements

- Compression for archival tier (gzip for old notes)
- Automatic migration of stale semantic memories to archival
- Graph visualization endpoints
- Memory analytics (most-recalled concepts, etc.)
- Custom embedding function support per project
- SQLite connection pooling for concurrent access
- Incremental backups of episodic/graph databases

## License

Part of the agent-harness project.

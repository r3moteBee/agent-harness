# Knowledge Capture

Extract key facts, decisions, and learnings from conversation and store them in memory.

## Procedure

1. **Determine scope.** If the user highlighted something specific ("remember this: ..."), capture exactly that. If they asked for a full capture, scan the entire conversation.

2. **Extract knowledge types:**

   **Facts** — Concrete information: configurations, URLs, account details, technical specifications, names, dates.
   → Store in **semantic memory** with clear, searchable descriptions.

   **Decisions** — Choices that were made and their rationale: "We chose PostgreSQL over MongoDB because of the relational nature of the data."
   → Store in **semantic memory** tagged with the decision context.

   **Relationships** — Connections between concepts: "Service A depends on Service B," "Alice is the owner of the billing module."
   → Store in **graph memory** as nodes and edges.

   **Learnings** — Things discovered during the conversation: "The API rate limits to 100 req/min," "The CSV parser chokes on UTF-16 files."
   → Store in **semantic memory** with enough context to be useful later.

3. **Write clean memory entries.** Each entry should be:
   - Self-contained — understandable without the original conversation
   - Searchable — use clear, descriptive language someone would search for
   - Dated — include when the knowledge was captured
   - Attributed — note the source or context

4. **Confirm what was captured.** Tell the user what you stored and where:
   - "Stored 3 facts in semantic memory and 2 relationships in graph memory."
   - List each entry briefly so the user can verify.

5. **Use the `remember` tool** to store each entry in the appropriate memory tier. Use `create_graph_node` and `link_concepts` for relationship data.

## Important

- Don't store trivial or ephemeral information (greetings, clarification questions).
- De-duplicate — check if similar knowledge already exists in memory before creating new entries.
- When storing decisions, always include the reasoning — the "why" is more valuable than the "what" over time.
- For sensitive information (credentials, personal data), warn the user before storing and confirm they want it in memory.

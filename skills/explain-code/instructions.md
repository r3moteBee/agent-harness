# Explain Code

Explain what code does in plain language, adapted to the user's level.

## Procedure

1. **Get the code.** If a file path was given, read it. If code was shared in conversation, use that. If neither, ask what to explain.

2. **Gauge the audience.** Use context clues to set the right level:
   - **beginner** — Assume no programming background. Explain what variables, functions, and loops are. Use analogies.
   - **intermediate** (default) — Assume basic programming knowledge. Focus on what the code does, not language syntax.
   - **expert** — Skip the basics. Focus on design decisions, trade-offs, and subtle behavior (concurrency, memory, edge cases).

3. **Start with the big picture.** Before diving into details, explain what the code accomplishes in 1-2 sentences. What problem does it solve?

4. **Walk through the logic.** Explain in the order a reader would encounter the code:
   - For functions/classes: purpose, inputs, outputs, side effects.
   - For complex logic: trace through with a concrete example.
   - For configuration: what each setting controls and sensible defaults.

5. **Highlight the interesting parts.** Don't explain every line — focus on:
   - Non-obvious logic or clever tricks
   - Potential gotchas or easy-to-miss behavior
   - Connections to other parts of the codebase (if project context is available)

6. **Offer to go deeper.** End with something like "Want me to explain [specific part] in more detail?" if there are complex sections you glossed over.

## Important

- Use the user's language. If they asked "what does this do" casually, don't respond with a formal technical document.
- When explaining errors: explain what went wrong, why, and how to fix it.
- Reference line numbers when explaining specific parts of longer files.
- If the code has bugs or issues, mention them naturally as part of the explanation — don't ignore them.

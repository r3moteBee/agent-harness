# Summarize Conversation

Distill a conversation into a clear summary with key points, decisions, and action items.

## Procedure

1. **Gather context.** Review the current conversation. If episodic memory is available, recall recent session history to capture the full scope of what was discussed.

2. **Identify the important parts:**
   - Decisions that were made
   - Problems that were identified
   - Solutions that were proposed or implemented
   - Action items — things that still need to be done
   - Open questions that weren't resolved
   - Key facts or information that was shared

3. **Structure by format:**

   **brief** — 3-5 bullet points covering the most important outcomes. Skip details.

   **detailed** (default):
   - **Summary** — 2-3 sentences on what the conversation was about.
   - **Key Decisions** — What was decided and why.
   - **Work Completed** — What was actually done during the conversation (code written, files changed, configs updated).
   - **Action Items** — What still needs to happen, with owners if mentioned.
   - **Open Questions** — Unresolved topics that need follow-up.

   **action-items** — Just the action items, formatted as a checklist.

4. **Store the summary.** When auto_store is enabled, the summary is saved to semantic memory so it can be recalled in future conversations ("what did we discuss last time?").

## Important

- Focus on outcomes and decisions, not the back-and-forth of how you got there.
- If the conversation involved code changes, reference the specific files and what changed.
- Use the project context to frame the summary in terms the user cares about.
- Keep it concise — a summary longer than the conversation isn't a summary.

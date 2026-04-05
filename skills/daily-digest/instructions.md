# Daily Digest

Generate a summary of recent project activity from memory and workspace state.

## Procedure

1. **Determine the time period.** Default is "today." Parse the user's request for a specific period (yesterday, this week, etc.).

2. **Gather data from multiple sources:**

   **Episodic Memory** — Recall recent conversations for the active project within the time period. Look for: topics discussed, decisions made, tasks completed, problems encountered.

   **Semantic Memory** — Check for recently stored knowledge entries that were captured during the period.

   **Workspace Files** — Use `list_workspace_files` to check for recently modified files. Note any new files, significant changes, or files that were deleted.

3. **Synthesize the digest:**

   - **Overview** — 1-2 sentences: what was the main focus of work during this period?
   - **Conversations** — Brief summary of each session (who was involved, what was discussed, what was accomplished).
   - **Changes Made** — Files created, modified, or deleted. Group by area of the project.
   - **Decisions & Learnings** — Key decisions captured, new knowledge stored.
   - **Open Items** — Tasks that were started but not finished, questions that remain unanswered.

4. **If running as a scheduled task:** Format the digest as a concise Telegram message (if `send_telegram` is available) or store it as a file in the workspace. Keep it brief — scheduled digests should be scannable in 30 seconds.

5. **Store the digest** in semantic memory so it can be recalled later ("what did we do last week?").

## Important

- If there's no activity for the period, say so briefly. Don't manufacture content.
- For scheduled runs, keep it tight — no one wants a daily wall of text.
- Group related activities together rather than listing them chronologically.
- Reference specific files and conversation topics so the user can dive deeper if needed.

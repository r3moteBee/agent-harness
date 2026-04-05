# Code Review

Review code for bugs, security issues, performance problems, and style.

## Procedure

1. **Read the file.** Use `read_file` to get the contents. If no file path was given, ask the user which file to review or check recent conversation context for code that was shared.

2. **Understand the context.** What does this code do? What language and framework is it? If project context is available (via `{{project.personality}}` or `{{project.files}}`), use it to understand conventions and architecture.

3. **Review systematically.** Check each category in order of severity:

   **Bugs & Logic Errors** (Critical)
   - Off-by-one errors, null/undefined access, race conditions
   - Incorrect logic flow, missing edge cases
   - Unreachable code, infinite loops

   **Security Issues** (Critical)
   - Injection vulnerabilities (SQL, command, XSS)
   - Hardcoded secrets or credentials
   - Missing input validation or sanitization
   - Insecure cryptographic practices
   - Path traversal, SSRF

   **Performance** (Important)
   - Unnecessary allocations or copies in hot paths
   - N+1 queries, missing indexes
   - Blocking operations in async code
   - Unbounded memory growth

   **Style & Maintainability** (Advisory)
   - Unclear naming, missing type hints
   - Functions doing too many things
   - Dead code, commented-out blocks
   - Missing error handling

4. **Structure the response:**
   - Lead with a 1-2 sentence overall assessment.
   - Group findings by severity: critical, important, advisory.
   - For each finding: quote the specific line(s), explain the issue, suggest a fix.
   - End with what the code does well — good reviews aren't only about problems.

## Important

- Be specific. "This might have issues" is useless. Point to exact lines.
- Suggest fixes, don't just point out problems.
- Calibrate tone — this is a review, not an attack. Acknowledge good patterns.
- If the user asked to focus on a specific area (security, performance, etc.), prioritize that but still note any critical issues in other areas.

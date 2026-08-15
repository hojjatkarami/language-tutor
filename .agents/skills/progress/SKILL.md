---
name: progress
description: Shows user progress analytics (lessons completed, quiz questions completed, mistakes history) and starts the TypeScript/React analytics server. Matches slash commands like "/progress", "slash progress", and "progress".
---

# Skill: French Learning Progress Visual Analytics

Use this skill when the user asks for their progress, dashboard, visual analytics, or types `/progress`.

## Active Learner Database

For a learner created with `$onboard-learner`, add `--learner-id "<user-id>" --language "<language-slug>"` before every `agent_helper.py` command in this skill. Do not use the legacy French database for another target language.

## Steps to Execute

1.  **Start the Progress Dashboard Server**:
    Run the progress server in the background as a task from the workspace root:
    ```bash
    python3 src/agent_helper.py progress-server
    ```

2.  **Verify Server Startup & Get URL**:
    *   Monitor the command output to capture the actual URL (e.g., `http://localhost:8080/` or `http://localhost:8081/` if port 8080 was busy).
    *   The server will run in the background. Expose this URL directly to the user as a clickable link.

3.  **Fetch Summary Statistics**:
    Run the helper command in the terminal to obtain a text-based summary of user progress:
    ```bash
    python3 src/agent_helper.py get-stats
    ```
    Analyze the JSON output to extract:
    *   `current_level`: Current level of the user (e.g. A2).
    *   `practiced_count`: Total lessons completed.
    *   `unresolved_mistakes_count`: Number of active quiz questions the user has answered incorrectly that remain unresolved.
    *   `weak_lessons`: Array of lessons where the user has active mistakes.
    *   `practiced_lessons`: List of lessons practiced.

4.  **Present Progress Summary in Chat**:
    *   Print a clean, concise markdown summary of the progress:
        *   **Current Level**: e.g., A2
        *   **Completed Lessons**: e.g., 4 / 25 total lessons
        *   **Active Mistakes**: e.g., 2
    *   List the top recommended lessons to review or practice next based on active mistakes or unpracticed status.
    *   **Provide the Clickable Dashboard Link**: Clearly print the dashboard URL (e.g., `http://localhost:8080`) and encourage the user to click it to view the interactive, rich React + TypeScript analytics dashboard.

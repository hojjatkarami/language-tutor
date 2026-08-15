---
name: new-lesson
description: Selects and teaches a new random French lesson based on the user's level. Matches slash commands like "/new-lesson", "/new_lesson", "slash new lesson", and "new lesson".
---

# Skill: French New Lesson

Use this skill when the user asks to start a new lesson, learn something new, or explicitly types `/new-lesson`.

## Active Learner Database

For a learner created with `$onboard-learner`, add `--learner-id "<user-id>" --language "<language-slug>"` before every `agent_helper.py` command in this skill. This keeps the lesson lookup in that learner's language database; the default command targets the legacy French database.

## Level Constraints
*   **Strict Level Matching**: When selecting, suggesting, or teaching a grammar lesson, only select lessons that are at the user's **exact** level (e.g., if the user is A2, they should only get A2 lessons, not A1 or B1/B2). Do not look for lessons above or below their current level.
*   **No Levels for Prepositions**: If the user asks to practice prepositions, do NOT apply level constraints. Randomly select among preposition lessons and do not check their current level.

## Steps to Execute

1.  **Retrieve Lesson Data**:
    Run the following command from the workspace root:
    *   For **Grammar**:
        ```bash
        python3 src/agent_helper.py new-lesson
        ```
    *   For **Prepositions**:
        ```bash
        python3 src/agent_helper.py new-lesson --topic prepositions
        ```

2.  **Analyze JSON Output**:
    *   For Grammar, confirm the lesson's level matches the user's level. For Prepositions, verify the topic is "prepositions" and level is "Prepositions".
    *   If `is_review` is `true`, notify the user that they have completed all lessons for their selected topic, and this is a review session.
    *   Extract the lesson details (`id`, `title`, `topic`, `description`, `key_vocabulary`, `conversational_phrases`) and the lesson `content` (markdown).

3.  **Teach the Lesson**:
    *   Present the lesson title, topic, and description clearly using headers.
    *   Output the lesson's main markdown `content` directly.
    *   List the **Key Vocabulary** (French -> English).
    *   Display the **Conversational Phrases** and emphasize the **Pronunciation Tip**. Encourage the user to practice speaking them aloud.

4.  **Log User Interaction**:
    *   If the user has questions about this lesson during your interaction, explain it to them and save their question in the persistent log by executing:
        ```bash
        python3 src/agent_helper.py log-question "<lesson_id>" "<user's question>"
        ```

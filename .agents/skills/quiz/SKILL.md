---
name: quiz
description: Runs a personalized French quiz on a practiced lesson or a random lesson. Matches slash commands like "/quiz", "slash quiz", and "quiz".
---

# Skill: French Quiz

Use this skill when the user types `/quiz`, asks to take a quiz, or wants to test their knowledge.

## Active Learner Database

For a learner created with `$onboard-learner`, add `--learner-id "<user-id>" --language "<language-slug>"` before every `agent_helper.py` command in this skill. Do not use the legacy French database for another target language.

## Quiz Design Guidelines
*   **No Spelling Focus**: When designing, administering, or checking quiz questions, do NOT focus on spelling, accents, typos, or minor orthographical variations. The focus of the quiz is entirely on syntax, grammar patterns, active sentence production, and verb conjugations, rather than testing spelling memory.
*   **Deceiving Prepositions**: When quizzing on prepositions, expect highly deceiving distractors (like `à` vs `chez`, `en` vs `dans`, or verbs followed by `à` vs `de`).

## Steps to Execute

1.  **Determine Target Lesson**:
    *   **Contextual Auto-Selection (Important)**: Check the conversation history. If a lesson was introduced or practiced in the immediate previous turns, **automatically select that lesson** for the quiz and skip asking the user which topic/lesson they want, unless they explicitly specified otherwise.
    *   **Fallback Selection Flow**: If no lesson was recently completed:
        *   Run the stats command to see the user's level and learning history:
            ```bash
            python3 src/agent_helper.py get-stats
            ```
        *   Ask the user whether they want to take a quiz on **Grammar**, **Prepositions**, or **Phrase Blocks**.
        *   If they choose **Phrase Blocks**, skip checking for completed lessons (since phrase blocks do not have lessons). Proceed directly to the **Phrase Blocks Matching Quiz** flow.
        *   If they choose **Grammar** or **Prepositions**:
        *   If `practiced_count` is `0`, inform the user they must first complete at least one lesson (suggesting `/new-lesson`).
        *   Filter the practiced lessons by their choice. If they have not practiced any lessons in that category yet, suggest they do a `/new-lesson` for it.
        *   Present their practiced lessons in the selected category as a numbered list (highlighting any `weak_lessons` as recommended selections).
        *   Ask the user which lesson they want to quiz on (or to pick "random" from the list).

2.  **Fetch and Generate Quiz Materials**:
    *   For **Grammar / Prepositions**:
        Once the user selects a lesson (e.g., `lesson_present_indicative`):
        1.  Fetch the base questions from the database:
            ```bash
            python3 src/agent_helper.py get-quiz "<selected_lesson_id>"
            ```
            This retrieves up to 5 multiple-choice questions (prioritizing history of mistakes).
        2.  Read the lesson's markdown content (by checking the file specified by `content_markdown_path` in the database, e.g. `lessons/A1/present_indicative.md`).
        3.  Look for the `## User Notes / Preferences` section in the markdown.
        4.  If this section exists and contains custom notes/preferences (i.e. not empty, not "None", and not just a placeholder), use your LLM capabilities to dynamically generate 1 to 2 new multiple-choice questions (MCQs) that directly address those notes/preferences.
        5.  For each dynamically generated question:
            *   Assign a temporary `quiz_id` formatted as `quiz_<selected_lesson_id>_dynamic_pref_<random_int>` (e.g., `quiz_present_indicative_dynamic_pref_9731`).
            *   Include `lesson_id`, `question` text, a dictionary of `options` (A, B, C, D), a `correct_answer` letter (A, B, C, or D), and an `explanation`.
        6.  Merge these dynamically generated questions into the quiz queue, replacing standard database questions to ensure the final quiz contains exactly 5 questions (e.g., 3-4 standard questions and 1-2 preference-based questions).
    *   For **Phrase Blocks**:
        Run:
        ```bash
        python3 src/agent_helper.py get-phrase-quiz
        ```
        This retrieves 4 phrase blocks at the user's current level or below (prioritizing historical phrase blocks mistakes).


3.  **Run Quiz Interactively**:
    *   For **Grammar / Prepositions**:
        *   Present Question 1 to the user with choices A, B, C, D. **Stop and wait** for the user's response.
        *   When the user replies:
            1.  Record the result in the database:
                ```bash
                python3 src/agent_helper.py record-result "<quiz_id>" "<lesson_id>" "<question_text>" '<options_json>' "<user_answer>" "<correct_answer>"
                ```
            2.  Tell the user if their answer was correct or incorrect, provide the `explanation`, then present the next question.
    *   For **Phrase Blocks (Matching Quiz)**:
        *   Present the quiz matching list to the user:
            - Display 4 English examples as a numbered list (1 to 4). Instead of showing only the plain phrase, use the full `example_english` sentence and wrap the target English phrase block in double asterisks to make it **bold** (e.g., "**In my opinion**, it is an excellent idea.").
            - Display 4 French phrase blocks as a lettered list (A to D), shuffled randomly.
        *   Ask the user to match them (e.g., entering "1-B, 2-A, 3-D, 4-C" or similar).
        *   Once the user submits their matches:
            1.  For each of the 4 pairs:
                - Check if the French phrase block matched to the English context sentence is correct.
                - Log the match success/failure in the database:
                  ```bash
                  python3 src/agent_helper.py record-phrase-result "<phrase_id>" "<true/false>"
                  ```
                - Output whether they matched it correctly. Show the correct translation, the full context sentence, the grammatical explanation, and the pronunciation tip.
            2.  Calculate and show their matching score (e.g., 3/4).

4.  **Conclude the Quiz**:
    *   Show the user their final score.
    *   Remind them they can review their mistakes anytime or try another quiz.

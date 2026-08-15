---
name: onboard-learner
description: Create or select an isolated language-learning profile and its databases, and offer to generate a starter curriculum. Use when a learner says they are new, another learner joins, a user asks to switch learners, someone wants to set up a profile or learn a language (for example, German), or needs their learning level configured.
---

# Learner Onboarding

Create or select a profile before starting lessons, quizzes, saved vocabulary, or conversation practice. Never remove or overwrite another learner's data.

## Collect the profile

Ask for the learner's preferred name first, even when a prior learner has used the same conversation. Then look up that name before asking for other information:

```bash
rtk proxy python3 src/onboard_user.py --name "<name>" --show-profile
```

- If the profile exists, confirm the learner's target language from its `languages` list, then use that learner's `user_id` and language database for the rest of the conversation. Do not create, reset, or delete anything.
- If no profile exists, ask only for the remaining details, one question at a time: target language; CEFR level (`A1`, `A2`, `B1`, or `B2`); and native language for explanations. Treat "absolute beginner" as `A1`; otherwise ask rather than guessing.
- If two people share a name, ask the new learner for a distinct `user-id` (for example, `mira-keller-2`) and include `--user-id` when creating and selecting their profile.

For German, use **Standard German** (`de-DE`), never Swiss German, unless the learner explicitly asks for a Swiss variety. Accept `German`, `Deutsch`, `de`, `Hochdeutsch`, and `standard German` as German.

## Create the learner and language database

Use a stable lowercase, hyphenated identifier derived from the learner's name. Run this from the workspace root:

```bash
rtk proxy python3 src/onboard_user.py --name "<name>" --target-language "<language>" --level "<A1|A2|B1|B2>" --native-language "<native language>"
```

Read the JSON response. A successful setup creates:

```text
databases/learners/<user-id>/profile.json
databases/learners/<user-id>/languages/<language>/
```

The language folder contains isolated `user_db.json`, lesson, quiz, phrase-block, context, and language metadata databases. Do not copy French or Swiss-French material into another language database. For a new German learner, the initialized metadata must say `German`, `de`, `de-DE`, and `Standard German`.

If the command reports that the learner/language already exists, do not overwrite it. Look up and use that existing profile instead.

## Welcome a new learner

After creating a profile, give a concise welcome before asking about the initial curriculum. Explain that the learner can:

- Study level-appropriate grammar lessons.
- Practice guided conversations and everyday roleplays when contexts exist for their target language.
- Take adaptive quizzes that revisit mistakes.
- Save vocabulary, useful sentences, and longer text highlights for later review.
- View progress, completed lessons, saved items, and areas that need more practice.

Use plain language and mention the relevant commands where available: `/new-lesson`, `/conversation`, `/quiz`, `/save`, and `/progress`. Explain that lesson, conversation, and quiz content becomes available after the learner accepts initial curriculum generation or adds their own content.

## Offer an initial curriculum

After creating a new learner and language database, ask exactly once before writing educational content:

> Would you like me to create your initial <target-language> curriculum and databases now? It will be modelled on the existing French curriculum structure, but all lessons and examples will be created for <target-language>.

Wait for an explicit yes. If the learner declines, leave the newly created databases empty. Never ask this question when merely selecting an existing learner.

When the learner agrees, create the starter curriculum automatically. Use the existing French database only as a structural model:

- Create 10 grammar lessons for each CEFR level, `A1`, `A2`, `B1`, and `B2`.
- Create 10 preposition or equivalent high-frequency usage lessons, 40 phrase blocks, and 8 everyday contexts adapted to the target language and locale.
- Create lesson markdown under `lessons/<language-slug>/<level>/` and reference each file from the learner's `grammar_db.json` or `prepositions_db.json` using the existing lesson schema (`id`, `level`, `title`, `topic`, `description`, `content_markdown_path`, `key_vocabulary`, and `conversational_phrases`).
- Populate the learner's isolated language database only. Keep its new `user_db.json` progress empty and its `quiz_db.json` empty; quizzes are designed after lesson practice.
- Use target-language grammar, vocabulary, examples, and local contexts. Do not translate, copy, or mix French/Swiss-French phrases into another language. For German, use Standard German (`de-DE`), not Swiss German.

Afterward, verify that every database is valid JSON and every lesson markdown path exists. Confirm the created lesson and context counts to the learner.

## Migrate the legacy French learner

Use this once only when the old shared French databases belong to a known learner. Copy them into that learner's isolated profile; never move or delete the shared databases:

```bash
rtk proxy python3 src/onboard_user.py --name "<name>" --migrate-legacy-french
```

Use the returned `user_id` with `--learner-id` and `--language french` from then on. If the learner's native language is known, add `--native-language "<language>"`; otherwise leave it unspecified and store `Unknown` rather than inventing a value.

For every later helper command for this learner, add `--learner-id "<user-id>" --language "<language>"` before the command name. For example:

```bash
rtk proxy python3 src/agent_helper.py --learner-id "mira-keller" --language "german" get-stats
```

Without these flags, the helper intentionally continues to use the project's legacy French databases.

## Finish

Confirm the learner's name, target language, and level. Mention when the language database is empty and explain that lessons and contexts still need to be authored for that language before a lesson or quiz can be delivered. Keep every other learner's profile intact.

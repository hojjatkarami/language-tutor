---
name: conversation
description: Picks a random Swiss French context and practices a level-appropriate conversation roleplay. Saves custom phrases. Matches slash commands like "/conversation", "/practice", "conversation", "practice".
---

# Skill: French Conversation Practice (Swiss Contexts)

Use this skill when the user types `/conversation`, `/practice`, or asks to start a roleplay / practice conversations in everyday contexts.

For a learner created with `$onboard-learner`, use this skill only when their target language is French. Do not apply Swiss-French contexts or save French phrases for a learner of another language; their isolated language database must stay free of French content until its own conversation material exists.

## Swiss French Culture & Regionalisms
As the user lives in the French-speaking part of Switzerland (Suisse romande), emphasize and explain the local regionalisms where appropriate:
*   **Numbers**: Use *septante* (70), *huitante* (80), and *nonante* (90) instead of the standard French *soixante-dix*, *quatre-vingts*, *quatre-vingt-dix*.
*   **Supermarket**: Coop, Migros, and Manor are the main chains. A shopping bag is a *cornet*. The loyalty cards are *Cumulus* (Migros) or *Supercard* (Coop). The receipt is *la quittance*.
*   **Bank**: ATMs are *bancomats*. PostFinance and Cantonal Banks (e.g. BCV, BCGE) are typical.
*   **Post Office**: Ensending a registered letter is *lettre recommandée*.
*   **Municipality**: The administration is *la commune*. Resident registry is *le contrôle des habitants*. Trash bags are *sacs taxés* (prepaid taxed bags).
*   **Train**: The Swiss national railway is *CFF*. A platform/track is *la voie*. Subscriptions include *demi-tarif* (half-fare) and *AG* (General Abonnement).
*   **Nature**: A barbecue is *faire des grillades*. Path yellow signposts indicate walking time.

## Steps to Execute

### 1. Retrieve Current Level & Contexts
Run the helper commands from the workspace root to fetch a random Swiss context:
```bash
python3 src/agent_helper.py get-random-context
```
Also, fetch user statistics to check their level:
```bash
python3 src/agent_helper.py get-stats
```
Examine the returned context JSON and identify the level-appropriate scenario matching the user's `current_level` (A1, A2, B1, or B2).

### 2. Set the Stage
Clearly present the scenario to the user in markdown:
1.  **Context**: e.g., *Au supermarché (Migros / Coop)*
2.  **Swiss Cultural Note**: Brief highlight of the Swiss terms.
3.  **Scenario & CEFR Level**: The exact scenario description for their level.
4.  **Objectives**: Bullet points of tasks to complete during the dialog.
5.  **Helpful Vocabulary**: List the Swiss/French vocabulary with English translations.

### 3. Conduct the Roleplay
*   Start the conversation by outputting the `starter_prompt` from the database in French.
*   **Stop and wait** for the user's reply.
*   Respond entirely in French, keeping the vocabulary and sentence structure strictly aligned with the user's CEFR level:
    *   **A1**: Short, simple sentences. Present tense mostly. Acknowledge and encourage heavily.
    *   **A2**: Simple past tenses (*passé composé*), basic descriptions, and simple instructions.
    *   **B1**: More complex opinions, compound sentences, and polite requests (*conditionnel*).
    *   **B2**: High-level debates, formal vocabulary, complex business or legal contexts.
*   Add a subtle English translation and helpful tip in blockquotes after each of your French responses to assist their learning.
*   Guide them through their objectives sequentially.

### 4. Save Custom Words, Sentences, or Blocks
If at any point during the conversation the user copies/pastes a vocabulary word, a sentence, or a block of text, or explicitly states they want to save an item:
1.  Determine the item type:
    *   **word**: single words or short vocabulary terms (e.g. *le cornet*, *septante*).
    *   **sentence**: standard conversational sentences (e.g. *Où se trouve le Gruyère ?*).
    *   **block**: expressions, paragraphs, or dialogue segments (e.g. *Il y a une erreur sur ma quittance...*).
2.  Verify the French text and its English translation.
3.  Execute the CLI command to save it to the database with the appropriate type flag:
    ```bash
    python3 src/agent_helper.py save-phrase "<context_id>" "<french_text>" "<english_translation>" --type "<word/sentence/block>"
    ```
4.  Confirm to the user that the item was successfully saved to their profile under that context.

### 5. Conclude
Once all objectives are met, wrap up the roleplay in French, congratulate them, and encourage them to view their saved phrases in the web dashboard!

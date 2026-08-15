---
name: save
description: Saves a custom vocabulary word, sentence, or text block to the user database. Matches slash commands like "/save", "slash save", "save".
---

# Skill: French Save Phrase / Vocabulary

Use this skill when the user types `/save`, asks to save a word, sentence, or expression, or pastes a French phrase they want to preserve.

## Active Learner Database

For a learner created with `$onboard-learner`, add `--learner-id "<user-id>" --language "<language-slug>"` before every `agent_helper.py` command in this skill. Apply the Swiss French context rules below only to French learners; use `general` for another language unless that language has its own defined contexts.

## Steps to Execute

### 1. Parse French and English Text
*   Analyze the user's input to extract the **French text** and the **English translation**.
*   The input may be formatted like `/save <french> | <english>`, `/save <french> - <english>`, or `/save <french> : <english>`.
*   **Translation Fallback**: If the user only provides the French text (e.g., `/save septante` or `/save Avez-vous la carte Cumulus ?`), you **MUST** translate it to English yourself and use that translation.

### 2. Determine Item Type
Classify the French text into one of these three types:
1.  **word**: If the text is a single word or short vocabulary phrase (1 to 3 words, e.g., *le cornet*, *huitante*, *la déchèterie*).
2.  **sentence**: If the text is a single complete sentence (e.g., *Où se trouve le bancomat le plus proche ?*).
3.  **block**: If the text is multiple sentences, a paragraph, or a larger dialogue block.

### 3. Determine Context ID
Identify which Swiss context category this item belongs to:
*   **supermarket**: If the item relates to shopping, supermarkets, groceries, payments, scales, or contains words like *Coop*, *Migros*, *cornet*, *action*, *peser*, *caisse*, *quittance*, *Cumulus*, *Supercard*.
*   **bank**: If the item relates to finance, banking, ATM, or contains words like *banque*, *bancomat*, *retirer*, *compte*, *virement*, *taux*, *intérêt*, *hypothèque*, *débit*.
*   **post_office**: If the item relates to postal services or packages, containing words like *poste*, *colis*, *timbre*, *recommandé*, *enveloppe*, *courrier*.
*   **municipality**: If the item relates to local administration or municipal regulations, containing words like *commune*, *municipalité*, *contrôle des habitants*, *sac taxé*, *déchets*, *attestation*, *naturalisation*.
*   **train**: If the item relates to train travel, stations, CFF, containing words like *train*, *gare*, *CFF*, *voie*, *billet*, *correspondance*, *retard*, *demi-tarif*, *SwissPass*.
*   **nature**: If the item relates to outdoor activities, lakes, hiking, containing words like *nature*, *randonnée*, *lac*, *montagne*, *grillade*, *forêt*, *col*, *refuge*, *météo*.
*   **general**: If the text does not fit any of the specific Swiss scenarios, default to `general`.

*Note: If the user is currently engaged in an active conversation roleplay with you, use the context of that active roleplay.*

### 4. Execute Save Command
Run the save-phrase helper command in the terminal:
```bash
python3 src/agent_helper.py save-phrase "<context_id>" "<french_text>" "<english_translation>" --type "<word/sentence/block>"
```

### 5. Acknowledge and Confirm
Output a clean, polite confirmation to the user showing:
*   **Saved Item**: French text -> English translation.
*   **Categorized Context**: The human-readable name of the context (e.g., *Au supermarché* or *Vocabulaire général*).
*   **Type**: e.g., `Vocabulary (Word)`, `Sentence`, or `Expression (Block)`.
*   Encourage them to view the item in their progress dashboard.

import sys
import os
import random
from db_manager import FrenchLearningDB

# Add parent dir to path just in case
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_banner(text):
    print("\n" + "=" * 50)
    print(f" {text}")
    print("=" * 50)

def main_menu():
    db = FrenchLearningDB()

    while True:
        level = db.get_user_level()
        print_banner(f"FRENCH LEARNING SYSTEM (Current Level: {level})")

        # Check for review suggestion
        weaknesses = db.get_most_difficult_lessons()
        if weaknesses:
            top_weakness = weaknesses[0]
            print(f"\033[93m★ Recommendation: You have {top_weakness['mistakes_count']} unresolved mistakes in '{top_weakness['title']}' ({top_weakness['level']}).")
            print("  Consider doing a /quiz on this lesson to practice! \033[0m\n")

        print("1. [Command: /new-lesson] Start a new random lesson")
        print("2. [Command: /quiz] Start a quiz on a lesson")
        print("3. View Progress & Mistake Analytics")
        print("4. Change Level")
        print("5. Log a Question/Feedback for a Lesson")
        print("6. Exit")
        print("7. [Command: /conversation] Practice Conversation (Swiss Contexts)")

        choice = input("\nSelect an option (1-7) or type a command: ").strip().lower()

        if choice in ['1', '/new-lesson', 'new-lesson', 'new lesson']:
            run_new_lesson(db)
        elif choice in ['2', '/quiz', 'quiz']:
            run_quiz(db)
        elif choice == '3':
            show_analytics(db)
        elif choice == '4':
            change_level(db)
        elif choice == '5':
            log_question(db)
        elif choice in ['7', '/conversation', 'conversation', '/practice', 'practice']:
            run_conversation_practice(db)
        elif choice == '6':
            print("\nAu revoir! Keep practicing French!")
            break
        else:
            print("\nInvalid option. Please choose 1-7.")

def run_new_lesson(db):
    print_banner("STARTING NEW LESSON")
    print("Select Topic:")
    print("1. Grammar (Level: {})".format(db.get_user_level()))
    print("2. Prepositions (Level: None)")
    topic_choice = input("\nSelect a topic (1-2) [Default: 1]: ").strip()

    if topic_choice == '2':
        print_banner("STARTING NEW LESSON: Prepositions")
        unpracticed = db.get_unpracticed_preposition_lessons()

        if not unpracticed:
            print("Fantastic! You have already practiced all preposition lessons.")
            review_choice = input("Would you like to review a random practiced lesson? (y/n): ").strip().lower()
            if review_choice == 'y':
                all_lessons = db.get_all_preposition_lessons()
                if not all_lessons:
                    print("No preposition lessons available.")
                    return
                selected = random.choice(all_lessons)
            else:
                return
        else:
            selected = random.choice(unpracticed)
    else:
        level = db.get_user_level()
        print_banner(f"STARTING NEW LESSON: Grammar (Level: {level})")
        unpracticed = db.get_unpracticed_lessons(level)

        if not unpracticed:
            print(f"Fantastic! You have already practiced all lessons for level {level}.")
            review_choice = input("Would you like to review a random practiced lesson? (y/n): ").strip().lower()
            if review_choice == 'y':
                all_lessons = [l for l in db.get_all_lessons() if l["level"] == level]
                if not all_lessons:
                    print("No lessons available for this level.")
                    return
                selected = random.choice(all_lessons)
            else:
                print("Tip: You can use option 4 in the main menu to upgrade your level.")
                return
        else:
            selected = random.choice(unpracticed)

    print(f"\nTitle: {selected['title']}")
    print(f"Topic: {selected['topic']}")
    print(f"Description: {selected['description']}")

    print("\n--- Lesson Markdown Content ---")
    content = db.get_lesson_markdown_content(selected)
    print(content)
    print("-------------------------------")

    print("\nKey Vocabulary:")
    for vocab in selected.get("key_vocabulary", []):
        print(f"  • {vocab['french']} : {vocab['english']}")

    print("\nConversational Phrases (Practice Speaking!):")
    for phrase in selected.get("conversational_phrases", []):
        print(f"  • French: \"{phrase['french']}\"")
        print(f"    English: \"{phrase['english']}\"")
        print(f"    Pronunciation Tip: {phrase['pronunciation_tip']}")

    # Mark it as practiced
    db.mark_lesson_practiced(selected["id"])
    print(f"\n[Saved] '{selected['title']}' has been marked as practiced.")
    input("\nPress Enter to return to main menu...")

def run_quiz(db):
    print_banner("QUIZ EVALUATION")

    print("Select Topic for Quiz:")
    print("1. Grammar")
    print("2. Prepositions")
    print("3. Phrase Blocks (Matching Quiz)")
    topic_choice = input("\nSelect a topic (1-3) [Default: 1]: ").strip()

    if topic_choice == '3':
        run_phrase_blocks_matching_quiz(db)
        return

    # Show practiced lessons to choose from
    practiced = db.user_db.get("progress", {}).get("practiced_lessons", {})
    if not practiced:
        print("You haven't practiced any grammar or preposition lessons yet! Go do a new lesson first or change your level.")
        input("\nPress Enter to return...")
        return

    target_topic = "prepositions" if topic_choice == '2' else "grammar"

    # Filter practiced lessons by topic
    filtered_practiced = {}
    for lesson_id, details in practiced.items():
        lesson = db.get_lesson_by_id(lesson_id)
        if lesson and lesson.get("topic") == target_topic:
            filtered_practiced[lesson_id] = details

    if not filtered_practiced:
        print(f"\nYou haven't practiced any {target_topic} lessons yet! Go do a new lesson first.")
        input("\nPress Enter to return...")
        return

    print(f"\nAvailable {target_topic} lessons to quiz:")
    options_map = {}
    idx = 1

    for lesson_id in filtered_practiced:
        lesson = db.get_lesson_by_id(lesson_id)
        if lesson:
            lvl_str = lesson.get("level")
            lvl_display = f" ({lvl_str})" if lvl_str else ""
            print(f"{idx}. {lesson['title']}{lvl_display}")
            options_map[str(idx)] = lesson_id
            idx += 1

    print(f"{idx}. Random Lesson (from practiced ones)")
    options_map[str(idx)] = "random"

    choice = input(f"\nSelect a lesson to quiz (1-{idx}): ").strip()

    if choice not in options_map:
        print("Invalid choice.")
        input("\nPress Enter to return...")
        return

    selected_id = options_map[choice]
    if selected_id == "random":
        selected_id = random.choice(list(filtered_practiced.keys()))

    lesson = db.get_lesson_by_id(selected_id)
    print_banner(f"QUIZ: {lesson['title']}")

    # Get questions (prioritizing previous mistakes)
    questions = db.get_quiz_questions_for_lesson(selected_id, limit=5)

    if not questions:
        print("No quiz questions found for this lesson in the database.")
        input("\nPress Enter to return...")
        return

    score = 0
    total = len(questions)

    for i, q in enumerate(questions, 1):
        print(f"\nQuestion {i} of {total}: {q['question']}")
        for opt_key, opt_val in q["options"].items():
            print(f"  {opt_key}. {opt_val}")

        user_ans = input("\nYour answer (A/B/C/D): ").strip().upper()
        while user_ans not in ['A', 'B', 'C', 'D']:
            user_ans = input("Invalid option. Enter A, B, C, or D: ").strip().upper()

        is_correct = db.record_quiz_result(
            quiz_id=q["quiz_id"],
            lesson_id=selected_id,
            question_text=q["question"],
            options=q["options"],
            user_answer=user_ans,
            correct_answer=q["correct_answer"]
        )

        if is_correct:
            print("\033[92m✔ Correct!\033[0m")
            score += 1
        else:
            print(f"\033[91m✘ Incorrect. (Correct Answer: {q['correct_answer']})\033[0m")

        print(f"Explanation: {q['explanation']}")

    print_banner("QUIZ COMPLETED")
    print(f"Your Score: {score} / {total} ({(score/total)*100:.1f}%)")
    input("\nPress Enter to return to main menu...")

def run_phrase_blocks_matching_quiz(db):
    print_banner("PHRASE BLOCKS MATCHING QUIZ")
    level = db.get_user_level()
    print(f"Level: {level} and below")

    # Fetch 4 phrase blocks
    blocks = db.get_phrase_blocks_for_quiz(level=level, limit=4)
    if not blocks:
        print("No phrase blocks found for your level.")
        input("\nPress Enter to return...")
        return

    # Shuffle English and French options
    shuffled_english_blocks = list(blocks)
    shuffled_french_blocks = list(blocks)

    random.shuffle(shuffled_english_blocks)
    random.shuffle(shuffled_french_blocks)

    print("\nMatch the English phrases (1-4) with their French equivalents (A-D):\n")

    import re
    for i, block in enumerate(shuffled_english_blocks, 1):
        example = block["example_english"]
        phrase = block["english"]
        # Bold target phrase in terminal using ANSI escape codes
        pattern = re.compile(re.escape(phrase), re.IGNORECASE)
        bolded_example = pattern.sub(lambda m: f"\033[1m{m.group(0)}\033[0m", example)
        print(f"  {i}. {bolded_example}")

    print("")

    letters = ["A", "B", "C", "D"]
    for letter, block in zip(letters, shuffled_french_blocks):
        print(f"  {letter}. {block['french']}")

    print("\nEnter matches in format '1-B, 2-A, 3-D, 4-C' or simply space/comma separated like 'B A D C':")
    user_input = input("\nYour matches: ").strip()

    # Robust parsing
    tokens = re.findall(r'[a-zA-Z]', user_input)
    letters_entered = [t.upper() for t in tokens if t.upper() in ['A', 'B', 'C', 'D']]

    user_mapping = {}
    pairs = re.findall(r'([1-4])\s*[-:/\s]*\s*([a-dA-D])', user_input)
    if pairs:
        for digit, letter in pairs:
            user_mapping[int(digit)] = letter.upper()
    elif len(letters_entered) == 4:
        for i, letter in enumerate(letters_entered, 1):
            user_mapping[i] = letter

    # Retry loop if matching fails
    while len(user_mapping) < 4:
        print("\nInvalid format. Please enter 4 matches (e.g., '1-B, 2-A, 3-D, 4-C' or 'B, A, D, C').")
        user_input = input("Your matches: ").strip()
        tokens = re.findall(r'[a-zA-Z]', user_input)
        letters_entered = [t.upper() for t in tokens if t.upper() in ['A', 'B', 'C', 'D']]

        user_mapping = {}
        pairs = re.findall(r'([1-4])\s*[-:/\s]*\s*([a-dA-D])', user_input)
        if pairs:
            for digit, letter in pairs:
                user_mapping[int(digit)] = letter.upper()
        elif len(letters_entered) == 4:
            for i, letter in enumerate(letters_entered, 1):
                user_mapping[i] = letter

    print_banner("MATCHING RESULTS")
    score = 0

    for i in range(1, 5):
        correct_block = shuffled_english_blocks[i - 1]
        correct_french = correct_block["french"]

        # Find which French phrase user matched
        user_letter = user_mapping[i]
        letter_idx = letters.index(user_letter)
        matched_block = shuffled_french_blocks[letter_idx]
        user_french = matched_block["french"]

        is_match_correct = (matched_block["id"] == correct_block["id"])
        db.record_phrase_block_result(correct_block["id"], is_match_correct)

        if is_match_correct:
            print(f"\033[92m✔ Pair {i}: Correct! '{correct_block['english']}' matches '{correct_french}'.\033[0m")
            score += 1
        else:
            print(f"\033[91m✘ Pair {i}: Incorrect. '{correct_block['english']}' was matched to '{user_french}'.\033[0m")
            print(f"  Correct: '{correct_french}'")

        print(f"  Context: {correct_block['example_english']}")
        print(f"  Explanation: {correct_block['explanation']}")
        print(f"  Pronunciation Tip: {correct_block['pronunciation_tip']}\n")

    print(f"Quiz Score: {score} / 4 ({(score / 4) * 100:.1f}%)")
    input("\nPress Enter to return to main menu...")


def show_analytics(db):
    print_banner("PROGRESS & MISTAKE ANALYTICS")

    # General stats
    user_level = db.get_user_level()
    practiced = db.user_db.get("progress", {}).get("practiced_lessons", {})
    incorrect_history = db.user_db.get("progress", {}).get("incorrect_questions_history", [])
    questions_logged = db.user_db.get("progress", {}).get("user_questions_log", [])

    # Phrase blocks stats
    pb_stats = db.user_db.get("progress", {}).get("phrase_blocks_stats", {
        "total_quizzed": 0,
        "correct_answers": 0,
        "last_practiced": None
    })
    incorrect_pb_ids = db.user_db.get("progress", {}).get("incorrect_phrase_blocks", [])

    print(f"User Level: {user_level}")
    print(f"Lessons Practiced: {len(practiced)}")
    print(f"Unresolved Grammar/Preposition Mistakes: {len(incorrect_history)}")
    print(f"Questions Logged: {len(questions_logged)}")
    print(f"Phrase Blocks Quizzed: {pb_stats['total_quizzed']}")
    if pb_stats['total_quizzed'] > 0:
        accuracy = (pb_stats['correct_answers'] / pb_stats['total_quizzed']) * 100
        print(f"Phrase Blocks Accuracy: {accuracy:.1f}% ({pb_stats['correct_answers']}/{pb_stats['total_quizzed']})")
    print(f"Active Phrase Block Mistakes: {len(incorrect_pb_ids)}")

    print("\n--- Practiced Lessons List ---")
    if not practiced:
        print("No lessons practiced yet.")
    for lesson_id, details in practiced.items():
        lesson = db.get_lesson_by_id(lesson_id)
        if lesson:
            lvl_str = lesson.get("level")
            lvl_display = f" ({lvl_str})" if lvl_str else " (Prepositions)"
            print(f"• {lesson['title']}{lvl_display} - Practiced {details['times_practiced']} time(s). Last: {details['last_practiced'][:10]}")

    print("\n--- Current Grammar/Preposition Mistakes (Need Review) ---")
    weaknesses = db.get_most_difficult_lessons()
    if not weaknesses:
        print("Excellent! You have no unresolved grammar/preposition mistakes.")
    for w in weaknesses:
        lvl_display = f" ({w['level']})" if w['level'] else ""
        print(f"• '{w['title']}'{lvl_display} - {w['mistakes_count']} active mistake(s).")

    print("\n--- Current Phrase Block Mistakes ---")
    if not incorrect_pb_ids:
        print("Excellent! You have no active phrase block mistakes.")
    else:
        all_pb = {pb["id"]: pb for pb in db.get_all_phrase_blocks()}
        for pbid in incorrect_pb_ids:
            if pbid in all_pb:
                pb = all_pb[pbid]
                print(f"• [{pb['level']}] \"{pb['french']}\" — Meaning: \"{pb['english']}\"")

    print("\n--- Questions Logged ---")
    if not questions_logged:
        print("No feedback or questions logged yet.")
    for q in questions_logged:
        lesson = db.get_lesson_by_id(q["lesson_id"])
        lesson_title = lesson["title"] if lesson else q["lesson_id"]
        print(f"• [{q['timestamp'][:10]}] Lesson: '{lesson_title}'")
        print(f"  Q: \"{q['question']}\"")

    print("\n--- Saved Phrases by Context ---")
    saved_phrases = db.get_saved_phrases()
    has_saved = False
    for ctx in db.get_all_contexts():
        ctx_phrases = saved_phrases.get(ctx["id"], [])
        if ctx_phrases:
            has_saved = True
            print(f"• {ctx['title']}:")
            for item in ctx_phrases:
                p_type = item.get("type", "sentence").capitalize()
                print(f"  - [{p_type}] French: \"{item['french']}\"")
                print(f"    English: \"{item['english']}\"")
    if not has_saved:
        print("No phrases saved yet. Try a conversation practice to save some!")

    input("\nPress Enter to return to main menu...")

def change_level(db):
    print_banner("CHANGE LEVEL")
    print(f"Your current level is: {db.get_user_level()}")
    new_lvl = input("Enter new level (A1, A2, B1, B2): ").strip().upper()

    if new_lvl in ['A1', 'A2', 'B1', 'B2']:
        db.set_user_level(new_lvl)
        print(f"Level updated to {new_lvl}!")
    else:
        print("Invalid level. Level must be A1, A2, B1, or B2.")

    input("\nPress Enter to return...")

def log_question(db):
    print_banner("LOG USER QUESTION OR FEEDBACK")

    # Pick a lesson
    lessons = db.get_all_lessons() + db.get_all_preposition_lessons()
    print("Available lessons:")
    for idx, lesson in enumerate(lessons, 1):
        lvl_display = f" ({lesson['level']})" if lesson.get('level') else " (Prepositions)"
        print(f"{idx}. {lesson['title']}{lvl_display}")

    choice = input(f"\nSelect a lesson to link this question to (1-{len(lessons)}): ").strip()
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(lessons):
            print("Invalid choice.")
            input("\nPress Enter to return...")
            return
        selected_lesson = lessons[idx]
    except ValueError:
        print("Invalid input.")
        input("\nPress Enter to return...")
        return

    question_text = input("Enter your question/feedback for this lesson: ").strip()
    if question_text:
        db.log_user_question(selected_lesson["id"], question_text)
        print("\n[Logged] Your question was saved to persistent user memory.")
    else:
        print("\nNo question entered.")

    input("\nPress Enter to return...")

def run_conversation_practice(db):
    print_banner("SWISS CONVERSATION PRACTICE")
    level = db.get_user_level()
    contexts = db.get_all_contexts()
    if not contexts:
        print("No contexts found in database.")
        input("\nPress Enter to return...")
        return

    context = random.choice(contexts)
    print(f"Context: {context['title']}")
    print(f"Description: {context['description']}")
    print(f"\033[94mSwiss Cultural Tip:\033[0m {context['swiss_notes']}")

    level_data = context["levels"].get(level)
    if not level_data:
        print(f"No scenario found for your level: {level}")
        input("\nPress Enter to return...")
        return

    print(f"\nYour Scenario (Level {level}): {level_data['scenario']}")

    print("\nObjectives to achieve:")
    for i, obj in enumerate(level_data["objectives"], 1):
        print(f"  {i}. {obj}")

    print("\nHelpful Vocabulary:")
    for vocab in level_data["helpful_vocabulary"]:
        print(f"  • {vocab['french']} : {vocab['english']}")

    input("\nPress Enter to start the conversation roleplay...")

    print_banner("ROLEPLAY ACTIVE (Type 'exit' to quit, 'save' to save a phrase)")

    # We will simulate a simple dialog turns structure
    # Turn 1: AI starts with starter_prompt. User replies.
    # Turn 2: AI acknowledges, responds, guides to objective 2. User replies.
    # Turn 3: AI acknowledges, responds, guides to objective 3. User replies.
    # Turn 4: AI concludes.

    turns = [
        {
            "ai_prompt": level_data["starter_prompt"],
            "hint": "Greet back and address the first objective."
        },
        {
            "ai_prompt": "Très bien. Et ensuite, " + level_data["objectives"][1].lower() + " ?",
            "hint": "Respond to proceed to the second objective."
        },
        {
            "ai_prompt": "Entendu. Pour terminer, " + level_data["objectives"][2].lower() + " ?",
            "hint": "Address the final objective."
        }
    ]

    current_turn = 0
    while current_turn < len(turns):
        turn = turns[current_turn]
        print(f"\n\033[92m[Partner]:\033[0m {turn['ai_prompt']}")
        print(f"\033[90m(Hint: {turn['hint']})\033[0m")

        user_input = input("\n\033[94m[You]:\033[0m ").strip()

        if user_input.lower() == 'exit':
            print("\nConversation practice ended.")
            break

        if user_input.lower() == 'save':
            # Run save sub-flow
            print("\n--- Save Vocabulary/Phrase/Block ---")
            french_phrase = input("Enter French word, sentence, or block of text: ").strip()
            english_phrase = input("Enter its English translation: ").strip()
            print("\nSelect the type of item:")
            print("1. Word / Vocabulary")
            print("2. Sentence")
            print("3. Expression / Block of text")
            type_choice = input("Select an option (1-3) [Default: 2]: ").strip()

            p_type = "sentence"
            if type_choice == '1':
                p_type = "word"
            elif type_choice == '3':
                p_type = "block"

            if french_phrase and english_phrase:
                saved = db.save_context_phrase(context["id"], french_phrase, english_phrase, p_type)
                if saved:
                    print(f"\033[92m✔ {p_type.capitalize()} saved successfully!\033[0m")
                else:
                    print("\033[93m⚠ This item is already saved.\033[0m")
            else:
                print("Invalid input. Item not saved.")
            continue

        if not user_input:
            print("Please type something to reply!")
            continue

        # Acknowledge user reply and move to next turn
        current_turn += 1

    if current_turn == len(turns):
        print(f"\n\033[92m[Partner]:\033[0m Parfait ! Merci beaucoup et bonne journée, au revoir !")
        print("\n\033[92m★ Bravo! You completed the conversation practice scenario!\033[0m")

    input("\nPress Enter to return to main menu...")

if __name__ == "__main__":
    main_menu()

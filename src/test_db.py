import os
import json
import shutil
from db_manager import FrenchLearningDB, USER_DB_PATH

def test_flow():
    print("Starting automated tests for French Learning Database Manager...")

    # Create backup of user_db.json to restore it after testing
    backup_path = USER_DB_PATH + ".bak"
    if os.path.exists(USER_DB_PATH):
        shutil.copyfile(USER_DB_PATH, backup_path)
        os.remove(USER_DB_PATH)
        has_backup = True
    else:
        has_backup = False

    try:
        # Initialize DB
        db = FrenchLearningDB()

        # Test 1: Level Management
        initial_level = db.get_user_level()
        assert initial_level == "A1", f"Expected initial level A1, got {initial_level}"
        print("✔ Test 1 passed: Initial level is A1")

        # Test 2: Unpracticed Lessons
        unpracticed = db.get_unpracticed_lessons("A1")
        assert len(unpracticed) > 0, "Expected some A1 lessons to be unpracticed"
        lesson_ids = [l["id"] for l in unpracticed]
        assert "lesson_present_indicative" in lesson_ids, "Expected lesson_present_indicative to be unpracticed"
        print("✔ Test 2 passed: Unpracticed lessons retrieved successfully")

        # Test 3: Mark lesson practiced
        db.mark_lesson_practiced("lesson_present_indicative")
        unpracticed_after = db.get_unpracticed_lessons("A1")
        lesson_ids_after = [l["id"] for l in unpracticed_after]
        assert "lesson_present_indicative" not in lesson_ids_after, "Expected lesson_present_indicative to be marked practiced"
        print("✔ Test 3 passed: Marked lesson practiced successfully")

        # Test 4: Retrieve quiz questions
        questions = db.get_quiz_questions_for_lesson("lesson_present_indicative", limit=2)
        assert len(questions) == 2, f"Expected 2 questions, got {len(questions)}"
        print("✔ Test 4 passed: Fetched quiz questions successfully")

        # Test 5: Record correct and incorrect answers
        q1 = questions[0]
        # Record incorrect answer
        is_correct = db.record_quiz_result(
            quiz_id=q1["quiz_id"],
            lesson_id="lesson_present_indicative",
            question_text=q1["question"],
            options=q1["options"],
            user_answer="Z", # definitely incorrect
            correct_answer=q1["correct_answer"]
        )
        assert not is_correct, "Expected incorrect answer to register as False"

        # Weakness check
        weaknesses = db.get_most_difficult_lessons()
        assert len(weaknesses) > 0, "Expected at least one weak lesson in history"
        assert weaknesses[0]["lesson_id"] == "lesson_present_indicative", "Expected lesson_present_indicative to be flagged as weak"
        print("✔ Test 5 passed: Recorded incorrect answer and identified weakness successfully")

        # Record correct answer to clear mistake
        is_correct_2 = db.record_quiz_result(
            quiz_id=q1["quiz_id"],
            lesson_id="lesson_present_indicative",
            question_text=q1["question"],
            options=q1["options"],
            user_answer=q1["correct_answer"],
            correct_answer=q1["correct_answer"]
        )
        assert is_correct_2, "Expected correct answer to register as True"

        # Check that weakness has been cleared
        weaknesses_after = db.get_most_difficult_lessons()
        assert len(weaknesses_after) == 0, f"Expected mistakes to be cleared, got: {weaknesses_after}"
        print("✔ Test 6 passed: Recorded correct answer and cleared weakness successfully")

        # Test 7: Set level
        db.set_user_level("A2")
        assert db.get_user_level() == "A2", "Expected level to be changed to A2"
        print("✔ Test 7 passed: Level change worked successfully")

        # Test 8: Prepositions Retrieval and Practice
        prep_lessons = db.get_all_preposition_lessons()
        assert len(prep_lessons) == 10, f"Expected 10 preposition lessons, got {len(prep_lessons)}"
        unpracticed_prep = db.get_unpracticed_preposition_lessons()
        assert len(unpracticed_prep) == 10, f"Expected 10 unpracticed preposition lessons, got {len(unpracticed_prep)}"

        # Mark one practiced
        selected_prep = prep_lessons[0]
        db.mark_lesson_practiced(selected_prep["id"])
        unpracticed_prep_after = db.get_unpracticed_preposition_lessons()
        assert len(unpracticed_prep_after) == 9, f"Expected 9 unpracticed preposition lessons, got {len(unpracticed_prep_after)}"
        print("✔ Test 8 passed: Preposition lesson retrieval and practice tracking works")

        # Test 9: Preposition Quizzes
        prep_questions = db.get_quiz_questions_for_lesson(selected_prep["id"], limit=3)
        assert len(prep_questions) == 3, f"Expected 3 quiz questions, got {len(prep_questions)}"

        q_prep = prep_questions[0]
        # Record incorrect result for preposition question
        is_correct_prep = db.record_quiz_result(
            quiz_id=q_prep["quiz_id"],
            lesson_id=selected_prep["id"],
            question_text=q_prep["question"],
            options=q_prep["options"],
            user_answer="Z",
            correct_answer=q_prep["correct_answer"]
        )
        assert not is_correct_prep, "Expected incorrect preposition answer to register as False"

        # Weakness check including prepositions
        weaknesses_prep = db.get_most_difficult_lessons()
        assert len(weaknesses_prep) > 0, "Expected at least one weak lesson in history"
        assert weaknesses_prep[0]["lesson_id"] == selected_prep["id"], "Expected preposition lesson to be flagged as weak"
        assert weaknesses_prep[0]["level"] == "Prepositions", f"Expected level to be 'Prepositions', got {weaknesses_prep[0]['level']}"
        print("✔ Test 9 passed: Preposition quiz recording and error analysis works")

        # Test 10: Phrase Blocks Database
        phrase_blocks = db.get_all_phrase_blocks()
        assert len(phrase_blocks) == 40, f"Expected 40 phrase blocks, got {len(phrase_blocks)}"

        a1_blocks = db.get_phrase_blocks_by_level("A1")
        assert len(a1_blocks) == 10, f"Expected 10 A1 phrase blocks, got {len(a1_blocks)}"
        assert a1_blocks[0]["french"] == "à mon avis", f"Expected first A1 phrase block to be 'à mon avis', got {a1_blocks[0]['french']}"

        b2_blocks = db.get_phrase_blocks_by_level("B2")
        assert len(b2_blocks) == 10, f"Expected 10 B2 phrase blocks, got {len(b2_blocks)}"
        print("✔ Test 10 passed: Phrase blocks retrieved and filtered by level successfully")

        # Test 11: Phrase Block Matching Quiz and Result recording
        # Initially, no incorrect phrase blocks
        assert len(db.user_db.get("progress", {}).get("incorrect_phrase_blocks", [])) == 0

        # Get quiz blocks
        quiz_blocks = db.get_phrase_blocks_for_quiz(level="A2", limit=4)
        assert len(quiz_blocks) == 4, f"Expected 4 phrase blocks for quiz, got {len(quiz_blocks)}"
        # Make sure they are A1 or A2
        for block in quiz_blocks:
            assert block["level"] in ["A1", "A2"], f"Expected block level A1 or A2, got {block['level']}"

        # Record a mistake
        target_pb = quiz_blocks[0]
        db.record_phrase_block_result(target_pb["id"], is_correct=False)
        assert target_pb["id"] in db.user_db.get("progress", {}).get("incorrect_phrase_blocks", [])

        # Verify stats updated
        pb_stats = db.user_db.get("progress", {}).get("phrase_blocks_stats", {})
        assert pb_stats["total_quizzed"] == 1
        assert pb_stats["correct_answers"] == 0

        # Get quiz again - it should prioritize the mistake block
        new_quiz = db.get_phrase_blocks_for_quiz(level="A2", limit=4)
        new_quiz_ids = [b["id"] for b in new_quiz]
        assert target_pb["id"] in new_quiz_ids, "Expected previous mistake to be prioritized in the next quiz"

        # Record it as correct
        db.record_phrase_block_result(target_pb["id"], is_correct=True)
        assert target_pb["id"] not in db.user_db.get("progress", {}).get("incorrect_phrase_blocks", [])

        # Verify stats updated
        pb_stats_after = db.user_db.get("progress", {}).get("phrase_blocks_stats", {})
        assert pb_stats_after["total_quizzed"] == 2
        assert pb_stats_after["correct_answers"] == 1

        print("✔ Test 11 passed: Phrase block matching quiz generation and mistake tracking works")

        # Test 12: Contexts and Saved Phrases
        contexts = db.get_all_contexts()
        assert len(contexts) >= 7, f"Expected at least 7 contexts, got {len(contexts)}"

        supermarket = db.get_context_by_id("supermarket")
        assert supermarket is not None, "Expected to find supermarket context"
        assert supermarket["title"] == "Au supermarché (Migros / Coop)", f"Unexpected supermarket title: {supermarket['title']}"

        # Test saving phrase
        assert len(db.get_saved_phrases("supermarket")) == 0, "Expected 0 saved phrases initially"
        saved = db.save_context_phrase("supermarket", "Je cherche un cornet.", "I am looking for a bag.")
        assert saved, "Expected phrase to be saved successfully"

        saved_phrases = db.get_saved_phrases("supermarket")
        assert len(saved_phrases) == 1, f"Expected 1 saved phrase, got {len(saved_phrases)}"
        assert saved_phrases[0]["french"] == "Je cherche un cornet."
        assert saved_phrases[0]["english"] == "I am looking for a bag."
        assert saved_phrases[0]["type"] == "sentence", f"Expected type to be sentence, got {saved_phrases[0]['type']}"

        # Test saving a word type
        saved_word = db.save_context_phrase("supermarket", "le cornet", "the shopping bag", "word")
        assert saved_word, "Expected word to be saved successfully"
        saved_phrases_2 = db.get_saved_phrases("supermarket")
        assert len(saved_phrases_2) == 2, f"Expected 2 saved items, got {len(saved_phrases_2)}"
        assert saved_phrases_2[1]["type"] == "word"

        # Test saving a block type
        saved_block = db.save_context_phrase("supermarket", "En Suisse, on dit septante, huitante, nonante.", "In Switzerland, they say 70, 80, 90.", "block")
        assert saved_block, "Expected block to be saved successfully"
        saved_phrases_3 = db.get_saved_phrases("supermarket")
        assert len(saved_phrases_3) == 3, f"Expected 3 saved items, got {len(saved_phrases_3)}"
        assert saved_phrases_3[2]["type"] == "block"

        # Test duplicate prevention
        saved_dup = db.save_context_phrase("supermarket", "Je cherche un cornet.", "I want a bag.")
        assert not saved_dup, "Expected duplicate phrase to be rejected"
        assert len(db.get_saved_phrases("supermarket")) == 3, "Expected still 3 saved phrases"

        print("✔ Test 12 passed: Context loading and phrase saving/deduplication works")

        print("\nAll automated tests passed successfully!")

    finally:
        # Restore backup
        if has_backup:
            shutil.copyfile(backup_path, USER_DB_PATH)
            os.remove(backup_path)
        elif os.path.exists(USER_DB_PATH):
            os.remove(USER_DB_PATH)

if __name__ == "__main__":
    test_flow()

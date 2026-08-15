import os
import json
import random
from datetime import datetime

# Define base directory relative to this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAMMAR_DB_PATH = os.path.join(BASE_DIR, "databases", "grammar_db.json")
PREPOSITIONS_DB_PATH = os.path.join(BASE_DIR, "databases", "prepositions_db.json")
PHRASE_BLOCKS_DB_PATH = os.path.join(BASE_DIR, "databases", "phrase_blocks_db.json")
QUIZ_DB_PATH = os.path.join(BASE_DIR, "databases", "quiz_db.json")
USER_DB_PATH = os.path.join(BASE_DIR, "databases", "user_db.json")
CONTEXTS_DB_PATH = os.path.join(BASE_DIR, "databases", "contexts_db.json")

class FrenchLearningDB:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or os.path.join(BASE_DIR, "databases")
        self.grammar_db_path = os.path.join(self.data_dir, "grammar_db.json")
        self.prepositions_db_path = os.path.join(self.data_dir, "prepositions_db.json")
        self.phrase_blocks_db_path = os.path.join(self.data_dir, "phrase_blocks_db.json")
        self.quiz_db_path = os.path.join(self.data_dir, "quiz_db.json")
        self.user_db_path = os.path.join(self.data_dir, "user_db.json")
        self.contexts_db_path = os.path.join(self.data_dir, "contexts_db.json")
        self.grammar_db = self._load_json(self.grammar_db_path, {"lessons": []})
        self.prepositions_db = self._load_json(self.prepositions_db_path, {"lessons": []})
        self.phrase_blocks_db = self._load_json(self.phrase_blocks_db_path, {"phrase_blocks": []})
        self.quiz_db = self._load_json(self.quiz_db_path, {"quizzes": []})
        self.contexts_db = self._load_json(self.contexts_db_path, {"contexts": []})
        self.user_db = self._load_json(self.user_db_path, {
            "user_profile": {"current_level": "A1", "joined_date": datetime.now().isoformat()},
            "progress": {"practiced_lessons": {}, "user_questions_log": [], "incorrect_questions_history": [], "saved_phrases": {}}
        })

    def _load_json(self, path, default):
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(default, f, indent=2, ensure_ascii=False)
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default

    def _save_user_db(self):
        with open(self.user_db_path, "w", encoding="utf-8") as f:
            json.dump(self.user_db, f, indent=2, ensure_ascii=False)

    def _save_quiz_db(self):
        with open(self.quiz_db_path, "w", encoding="utf-8") as f:
            json.dump(self.quiz_db, f, indent=2, ensure_ascii=False)

    # User Profile management
    def get_user_level(self):
        return self.user_db.get("user_profile", {}).get("current_level", "A1")

    def set_user_level(self, level):
        self.user_db["user_profile"]["current_level"] = level
        self._save_user_db()

    # Lesson logic
    def get_all_lessons(self):
        return self.grammar_db.get("lessons", [])

    def get_all_preposition_lessons(self):
        return self.prepositions_db.get("lessons", [])

    def get_all_phrase_blocks(self):
        return self.phrase_blocks_db.get("phrase_blocks", [])

    def get_phrase_blocks_by_level(self, level):
        return [pb for pb in self.get_all_phrase_blocks() if pb.get("level") == level]

    def get_lesson_by_id(self, lesson_id):
        for lesson in self.get_all_lessons():
            if lesson["id"] == lesson_id:
                return lesson
        for lesson in self.get_all_preposition_lessons():
            if lesson["id"] == lesson_id:
                return lesson
        return None

    def get_unpracticed_preposition_lessons(self):
        all_lessons = self.get_all_preposition_lessons()
        practiced = self.user_db.get("progress", {}).get("practiced_lessons", {})
        unpracticed = [l for l in all_lessons if l["id"] not in practiced]
        return unpracticed

    def get_unpracticed_lessons(self, level=None):
        if level is None:
            level = self.get_user_level()

        all_lessons = [l for l in self.get_all_lessons() if l["level"] == level]
        practiced = self.user_db.get("progress", {}).get("practiced_lessons", {})

        unpracticed = [l for l in all_lessons if l["id"] not in practiced]
        return unpracticed

    def mark_lesson_practiced(self, lesson_id):
        progress = self.user_db.setdefault("progress", {})
        practiced = progress.setdefault("practiced_lessons", {})

        if lesson_id not in practiced:
            practiced[lesson_id] = {
                "times_practiced": 0,
                "last_practiced": None
            }

        practiced[lesson_id]["times_practiced"] += 1
        practiced[lesson_id]["last_practiced"] = datetime.now().isoformat()
        self._save_user_db()

    def get_lesson_markdown_content(self, lesson):
        path = lesson.get("content_markdown_path")
        if not path:
            return "No content path specified."
        full_path = os.path.join(BASE_DIR, path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        return f"Markdown file not found at: {full_path}"

    # Log user questions & feedback
    def log_user_question(self, lesson_id, question, context=""):
        log_entry = {
            "lesson_id": lesson_id,
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "context": context
        }
        self.user_db.setdefault("progress", {}).setdefault("user_questions_log", []).append(log_entry)
        self._save_user_db()

    # Quiz store: the agent designs quizzes from lesson context and persists
    # them here. Questions accumulate over time so they can be reused/reviewed.
    def save_quiz_questions(self, questions):
        """Append agent-designed quiz questions to the quiz store (deduped by quiz_id).

        Returns the number of newly stored questions."""
        store = self.quiz_db.setdefault("quizzes", [])
        existing_ids = {q.get("quiz_id") for q in store}
        added = 0
        for q in questions:
            qid = q.get("quiz_id")
            if not qid or qid in existing_ids:
                continue
            store.append({
                "quiz_id": qid,
                "lesson_id": q.get("lesson_id"),
                "question": q.get("question", ""),
                "options": q.get("options", {}),
                "correct_answer": q.get("correct_answer", ""),
                "explanation": q.get("explanation", ""),
            })
            existing_ids.add(qid)
            added += 1
        if added:
            self._save_quiz_db()
        return added

    # Quiz selection and logging
    def get_quiz_questions_for_lesson(self, lesson_id, limit=5):
        # 1. Fetch all previously designed questions for this lesson from the store
        pool = [q for q in self.quiz_db.get("quizzes", []) if q["lesson_id"] == lesson_id]

        # 2. Check user's incorrect questions history for this lesson
        incorrect_history = self.user_db.get("progress", {}).get("incorrect_questions_history", [])

        # Identify any incorrect questions that are not in the main pool (e.g. dynamic questions)
        failed_dynamic_questions = []
        pool_ids = {q["quiz_id"] for q in pool}
        for item in incorrect_history:
            if item["lesson_id"] == lesson_id and item["quiz_id"] not in pool_ids:
                failed_dynamic_questions.append({
                    "quiz_id": item["quiz_id"],
                    "lesson_id": item["lesson_id"],
                    "question": item.get("question_text", ""),
                    "options": item.get("options", {}),
                    "correct_answer": item.get("correct_answer", ""),
                    "explanation": "Review question from your previous mistakes."
                })

        incorrect_ids = {item["quiz_id"] for item in incorrect_history if item["lesson_id"] == lesson_id}

        # Split pool into questions the user has failed before and new/other questions
        failed_questions = [q for q in pool if q["quiz_id"] in incorrect_ids]
        other_questions = [q for q in pool if q["quiz_id"] not in incorrect_ids]

        # Combine failed pool questions with failed dynamic questions
        all_failed = failed_questions + failed_dynamic_questions

        # Shuffle both lists to ensure variety
        random.shuffle(all_failed)
        random.shuffle(other_questions)

        # Prioritize failed questions, then fill remainder with other questions
        selected = (all_failed + other_questions)[:limit]
        return selected


    def record_quiz_result(self, quiz_id, lesson_id, question_text, options, user_answer, correct_answer):
        progress = self.user_db.setdefault("progress", {})
        incorrect_history = progress.setdefault("incorrect_questions_history", [])

        is_correct = user_answer.strip().upper() == correct_answer.strip().upper()

        # Track statistics
        practiced = progress.setdefault("practiced_lessons", {})
        if lesson_id not in practiced:
            practiced[lesson_id] = {
                "times_practiced": 0,
                "last_practiced": datetime.now().isoformat()
            }

        if "quizzes_practiced" not in practiced[lesson_id]:
            practiced[lesson_id]["quizzes_practiced"] = 0
        if "quiz_correct_answers" not in practiced[lesson_id]:
            practiced[lesson_id]["quiz_correct_answers"] = 0

        practiced[lesson_id]["quizzes_practiced"] += 1
        if is_correct:
            practiced[lesson_id]["quiz_correct_answers"] += 1

        if not is_correct:
            # If incorrect, check if it's already in history. If not, add it.
            already_in = False
            for item in incorrect_history:
                if item["quiz_id"] == quiz_id:
                    already_in = True
                    item["timestamp"] = datetime.now().isoformat()
                    item["user_answer"] = user_answer
                    break

            if not already_in:
                incorrect_history.append({
                    "quiz_id": quiz_id,
                    "lesson_id": lesson_id,
                    "timestamp": datetime.now().isoformat(),
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "question_text": question_text,
                    "options": options
                })
        else:
            # If correct, remove it from incorrect history if it exists there
            progress["incorrect_questions_history"] = [
                item for item in incorrect_history if item["quiz_id"] != quiz_id
            ]

        self._save_user_db()
        return is_correct

    # Weakness analyzer
    def get_most_difficult_lessons(self):
        incorrect_history = self.user_db.get("progress", {}).get("incorrect_questions_history", [])
        mistakes_count = {}
        for item in incorrect_history:
            lesson_id = item["lesson_id"]
            mistakes_count[lesson_id] = mistakes_count.get(lesson_id, 0) + 1

        # Sort lessons by count of mistakes descending
        sorted_weaknesses = sorted(mistakes_count.items(), key=lambda x: x[1], reverse=True)

        weak_lessons = []
        for l_id, count in sorted_weaknesses:
            lesson = self.get_lesson_by_id(l_id)
            if lesson:
                weak_lessons.append({
                    "lesson_id": l_id,
                    "title": lesson["title"],
                    "level": lesson.get("level", "Prepositions"),
                    "mistakes_count": count
                })
        return weak_lessons

    # Phrase Blocks matching quiz methods
    def get_allowed_levels(self, level):
        levels = ["A1", "A2", "B1", "B2"]
        if level not in levels:
            return ["A1"]
        idx = levels.index(level)
        return levels[:idx + 1]

    def get_phrase_blocks_for_quiz(self, level=None, limit=4):
        if level is None:
            level = self.get_user_level()

        allowed_levels = self.get_allowed_levels(level)
        all_blocks = [pb for pb in self.get_all_phrase_blocks() if pb.get("level") in allowed_levels]

        if not all_blocks:
            return []

        # Get historical mistakes
        incorrect_ids = self.user_db.setdefault("progress", {}).setdefault("incorrect_phrase_blocks", [])
        # Filter mistakes to only those within allowed levels
        mistake_blocks = [pb for pb in all_blocks if pb["id"] in incorrect_ids]
        other_blocks = [pb for pb in all_blocks if pb["id"] not in incorrect_ids]

        random.shuffle(mistake_blocks)
        random.shuffle(other_blocks)

        # Mix in mistakes (up to limit)
        num_mistakes = min(len(mistake_blocks), max(1, limit // 2))
        num_others = limit - num_mistakes

        selected = mistake_blocks[:num_mistakes] + other_blocks[:num_others]
        if len(selected) < limit and len(other_blocks) > num_others:
            selected += other_blocks[num_others:num_others + (limit - len(selected))]

        random.shuffle(selected)
        return selected[:limit]

    def record_phrase_block_result(self, phrase_id, is_correct):
        progress = self.user_db.setdefault("progress", {})
        incorrect_list = progress.setdefault("incorrect_phrase_blocks", [])

        # Track general stats for phrase blocks
        pb_stats = progress.setdefault("phrase_blocks_stats", {
            "total_quizzed": 0,
            "correct_answers": 0,
            "last_practiced": None
        })
        pb_stats["total_quizzed"] += 1
        if is_correct:
            pb_stats["correct_answers"] += 1
        pb_stats["last_practiced"] = datetime.now().isoformat()

        if not is_correct:
            if phrase_id not in incorrect_list:
                incorrect_list.append(phrase_id)
        else:
            if phrase_id in incorrect_list:
                incorrect_list.remove(phrase_id)

        self._save_user_db()

    # Contexts & Saved Phrases methods
    def get_all_contexts(self):
        return self.contexts_db.get("contexts", [])

    def get_context_by_id(self, context_id):
        for ctx in self.get_all_contexts():
            if ctx["id"] == context_id:
                return ctx
        return None

    def save_context_phrase(self, context_id, french, english, phrase_type="sentence"):
        progress = self.user_db.setdefault("progress", {})
        saved_phrases = progress.setdefault("saved_phrases", {})
        phrases_for_context = saved_phrases.setdefault(context_id, [])

        # Check if already exists to avoid duplicates
        for item in phrases_for_context:
            if item["french"].strip().lower() == french.strip().lower():
                return False # Already exists

        # Validate type
        if phrase_type not in ["word", "sentence", "block"]:
            phrase_type = "sentence"

        phrases_for_context.append({
            "french": french.strip(),
            "english": english.strip(),
            "type": phrase_type,
            "saved_at": datetime.now().isoformat()
        })
        self._save_user_db()
        return True

    def get_saved_phrases(self, context_id=None):
        saved_phrases = self.user_db.get("progress", {}).get("saved_phrases", {})
        if context_id:
            return saved_phrases.get(context_id, [])
        return saved_phrases

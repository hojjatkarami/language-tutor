import sys
import json
import argparse
import os
import re
from functools import partial
import http.server
import socketserver
from db_manager import FrenchLearningDB

def get_progress_analytics(db):
    user_level = db.get_user_level()
    grammar_lessons = db.get_all_lessons()
    prepos_lessons = db.get_all_preposition_lessons()

    practiced = db.user_db.get("progress", {}).get("practiced_lessons", {})
    incorrect_history = db.user_db.get("progress", {}).get("incorrect_questions_history", [])

    # 1. Total counts
    all_lessons = grammar_lessons + prepos_lessons
    total_lessons_count = len(all_lessons)
    practiced_lessons_count = len(practiced)
    unresolved_mistakes_count = len(incorrect_history)

    # 2. Quizzes statistics
    total_quizzes_practiced = 0
    total_quiz_correct_answers = 0

    for details in practiced.values():
        total_quizzes_practiced += details.get("quizzes_practiced", 0)
        total_quiz_correct_answers += details.get("quiz_correct_answers", 0)

    accuracy_rate = 0.0
    if total_quizzes_practiced > 0:
        accuracy_rate = total_quiz_correct_answers / total_quizzes_practiced

    # 3. Levels breakdown
    levels = ["A1", "A2", "B1", "B2", "Prepositions"]
    levels_breakdown = {lvl: {"total": 0, "practiced": 0} for lvl in levels}

    for l in grammar_lessons:
        lvl = l.get("level", "A1")
        if lvl in levels_breakdown:
            levels_breakdown[lvl]["total"] += 1
            if l["id"] in practiced:
                levels_breakdown[lvl]["practiced"] += 1

    for l in prepos_lessons:
        lvl = "Prepositions"
        levels_breakdown[lvl]["total"] += 1
        if l["id"] in practiced:
            levels_breakdown[lvl]["practiced"] += 1

    # 4. Lessons list
    lessons_list = []
    lesson_titles = {}
    for l in all_lessons:
        lesson_titles[l["id"]] = l["title"]

    # Track mistakes count per lesson
    lesson_mistakes = {}
    for item in incorrect_history:
        lid = item["lesson_id"]
        lesson_mistakes[lid] = lesson_mistakes.get(lid, 0) + 1

    for l in all_lessons:
        lid = l["id"]
        lvl = l.get("level", "Prepositions")
        times_prac = practiced.get(lid, {}).get("times_practiced", 0)
        quizzes_prac = practiced.get(lid, {}).get("quizzes_practiced", 0)
        correct_prac = practiced.get(lid, {}).get("quiz_correct_answers", 0)
        last_prac = practiced.get(lid, {}).get("last_practiced", None)
        active_mistakes = lesson_mistakes.get(lid, 0)

        lessons_list.append({
            "id": lid,
            "title": l["title"],
            "level": lvl,
            "times_practiced": times_prac,
            "quizzes_practiced": quizzes_prac,
            "quiz_correct_answers": correct_prac,
            "active_mistakes_count": active_mistakes,
            "last_practiced": last_prac
        })

    level_order = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "Prepositions": 4}
    lessons_list.sort(key=lambda x: (level_order.get(x["level"], 9), x["title"]))

    # 5. Incorrect questions history with lesson titles
    incorrect_list = []
    for item in incorrect_history:
        incorrect_list.append({
            "quiz_id": item["quiz_id"],
            "lesson_id": item["lesson_id"],
            "lesson_title": lesson_titles.get(item["lesson_id"], item["lesson_id"]),
            "timestamp": item.get("timestamp", ""),
            "user_answer": item.get("user_answer", ""),
            "correct_answer": item.get("correct_answer", ""),
            "question_text": item.get("question_text", ""),
            "options": item.get("options", {})
        })
    incorrect_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    # 6. Needs practice recommendations
    needs_practice = []
    for l in lessons_list:
        if l["active_mistakes_count"] > 0:
            needs_practice.append({
                "id": l["id"],
                "title": l["title"],
                "level": l["level"],
                "active_mistakes_count": l["active_mistakes_count"],
                "reason": "mistake"
            })
    needs_practice.sort(key=lambda x: x["active_mistakes_count"], reverse=True)

    unpracticed_curr_level = []
    for l in lessons_list:
        if l["level"] == user_level and l["times_practiced"] == 0:
            unpracticed_curr_level.append({
                "id": l["id"],
                "title": l["title"],
                "level": l["level"],
                "active_mistakes_count": 0,
                "reason": "unpracticed"
            })
    needs_practice.extend(unpracticed_curr_level)

    # 7. Phrase blocks stats
    pb_stats = db.user_db.get("progress", {}).get("phrase_blocks_stats", {
        "total_quizzed": 0,
        "correct_answers": 0,
        "last_practiced": None
    })
    incorrect_pb_ids = db.user_db.get("progress", {}).get("incorrect_phrase_blocks", [])

    all_phrase_blocks = {pb["id"]: pb for pb in db.get_all_phrase_blocks()}
    incorrect_pb_details = []
    for pbid in incorrect_pb_ids:
        if pbid in all_phrase_blocks:
            incorrect_pb_details.append(all_phrase_blocks[pbid])

    return {
        "current_level": user_level,
        "total_lessons_count": total_lessons_count,
        "practiced_lessons_count": practiced_lessons_count,
        "unresolved_mistakes_count": unresolved_mistakes_count,
        "total_quizzes_practiced": total_quizzes_practiced,
        "total_quiz_correct_answers": total_quiz_correct_answers,
        "accuracy_rate": accuracy_rate,
        "levels_breakdown": levels_breakdown,
        "lessons": lessons_list,
        "incorrect_questions_history": incorrect_list,
        "needs_practice_lessons": needs_practice[:6],
        "phrase_blocks_stats": pb_stats,
        "incorrect_phrase_blocks": incorrect_pb_details,
        "saved_phrases": db.get_saved_phrases()
    }

class ProgressHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, data_dir=None, **kwargs):
        self.data_dir = data_dir
        self.dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "progress-ui", "dist")
        super().__init__(*args, directory=self.dist_dir, **kwargs)

    def do_GET(self):
        if self.path == '/api/stats':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            db = FrenchLearningDB(data_dir=self.data_dir)
            stats = get_progress_analytics(db)
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode('utf-8'))
        else:
            requested_path = self.path.split('?')[0]
            full_path = os.path.join(self.dist_dir, requested_path.lstrip('/'))

            if not os.path.exists(full_path) or os.path.isdir(full_path):
                self.path = '/index.html'

            super().do_GET()

    def log_message(self, format, *args):
        pass

def run_server(port=8080, data_dir=None):
    dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "progress-ui", "dist")
    if not os.path.exists(dist_dir):
        print(f"Error: Build folder not found at {dist_dir}.")
        print("Please build the progress-ui first: cd progress-ui && npm run build")
        return

    server = None
    actual_port = port
    max_attempts = 20
    for i in range(max_attempts):
        try:
            handler = partial(ProgressHTTPRequestHandler, data_dir=data_dir)
            server = socketserver.TCPServer(("", actual_port), handler)
            break
        except OSError:
            actual_port += 1

    if not server:
        print("Error: Could not find an open port to start the server.")
        return

    print(f"\n==================================================")
    print(f" 📊 FRENCH LEARNING PROGRESS SERVER STARTED")
    print(f"==================================================")
    print(f" Local URL: http://localhost:{actual_port}/")
    print(f" Exposing stats API at: http://localhost:{actual_port}/api/stats")
    print(f" Press Ctrl+C to stop the server.")
    print(f"==================================================\n")
    sys.stdout.flush()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping French progress server... Au revoir!")
        server.server_close()

def main():
    parser = argparse.ArgumentParser(description="Language Learning Agent Helper")
    parser.add_argument("--learner-id", help="Use databases for this initialized learner")
    parser.add_argument("--language", help="Use this initialized target-language database")
    subparsers = parser.add_subparsers(dest="command")

    # Command: new-lesson
    new_lesson_parser = subparsers.add_parser("new-lesson", help="Retrieve a new random lesson and mark it practiced")
    new_lesson_parser.add_argument("--topic", type=str, default="grammar", choices=["grammar", "prepositions"], help="Topic of the lesson")

    # Command: get-quiz
    quiz_parser = subparsers.add_parser("get-quiz", help="Get lesson context + previously designed questions to build a quiz")
    quiz_parser.add_argument("lesson_id", type=str, help="ID of the lesson to quiz")

    # Command: save-quiz
    save_quiz_parser = subparsers.add_parser("save-quiz", help="Persist agent-designed quiz questions to the quiz store")
    save_quiz_parser.add_argument("questions_json", type=str, help="JSON array of designed question objects")

    # Command: record-result
    result_parser = subparsers.add_parser("record-result", help="Record a quiz result")
    result_parser.add_argument("quiz_id", type=str)
    result_parser.add_argument("lesson_id", type=str)
    result_parser.add_argument("question_text", type=str)
    result_parser.add_argument("options_json", type=str)
    result_parser.add_argument("user_answer", type=str)
    result_parser.add_argument("correct_answer", type=str)

    # Command: log-question
    log_parser = subparsers.add_parser("log-question", help="Log a user question")
    log_parser.add_argument("lesson_id", type=str)
    log_parser.add_argument("question", type=str)

    # Command: get-stats
    subparsers.add_parser("get-stats", help="Get user progress and mistakes stats")

    # Command: progress-server
    server_parser = subparsers.add_parser("progress-server", help="Start the React progress dashboard server")
    server_parser.add_argument("--port", type=int, default=8080, help="Initial port to run the server on")

    # Command: get-phrase-quiz
    phrase_quiz_parser = subparsers.add_parser("get-phrase-quiz", help="Get a matching phrase blocks quiz")
    phrase_quiz_parser.add_argument("--limit", type=int, default=4, help="Number of phrase blocks to include")

    # Command: record-phrase-result
    phrase_result_parser = subparsers.add_parser("record-phrase-result", help="Record a phrase block match result")
    phrase_result_parser.add_argument("phrase_id", type=str, help="ID of the phrase block")
    phrase_result_parser.add_argument("is_correct", type=str, choices=["true", "false"], help="Whether user got it correct")

    # Command: get-contexts
    subparsers.add_parser("get-contexts", help="Get all Swiss contexts")

    # Command: get-random-context
    subparsers.add_parser("get-random-context", help="Get a random Swiss context")

    # Command: save-phrase
    save_phrase_parser = subparsers.add_parser("save-phrase", help="Save a phrase under a context")
    save_phrase_parser.add_argument("context_id", type=str)
    save_phrase_parser.add_argument("french", type=str)
    save_phrase_parser.add_argument("english", type=str)
    save_phrase_parser.add_argument("--type", type=str, default="sentence", choices=["word", "sentence", "block"], help="Type of item (word, sentence, block)")

    # Command: get-saved-phrases
    get_saved_phrases_parser = subparsers.add_parser("get-saved-phrases", help="Get saved phrases for a context")
    get_saved_phrases_parser.add_argument("--context_id", type=str, default=None)

    args = parser.parse_args()

    if bool(args.learner_id) != bool(args.language):
        parser.error("--learner-id and --language must be used together")

    data_dir = None
    if args.learner_id:
        learner_id = args.learner_id.strip().lower()
        language = args.language.strip().lower()
        valid_slug = r"[a-z0-9]+(?:-[a-z0-9]+)*"
        if not re.fullmatch(valid_slug, learner_id) or not re.fullmatch(valid_slug, language):
            parser.error("--learner-id and --language must be lowercase hyphenated identifiers")
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "databases",
            "learners",
            learner_id,
            "languages",
            language,
        )
        if not os.path.isdir(data_dir):
            parser.error(f"No initialized language database exists at: {data_dir}")

    db = FrenchLearningDB(data_dir=data_dir)

    if args.command == "new-lesson":
        topic = getattr(args, "topic", "grammar")
        is_review = False

        if topic == "prepositions":
            unpracticed = db.get_unpracticed_preposition_lessons()
            if not unpracticed:
                all_lessons = db.get_all_preposition_lessons()
                if not all_lessons:
                    print(json.dumps({"error": "No preposition lessons found"}))
                    return
                import random
                selected = random.choice(all_lessons)
                is_review = True
            else:
                import random
                selected = random.choice(unpracticed)
            level = "Prepositions"
        else:
            level = db.get_user_level()
            unpracticed = db.get_unpracticed_lessons(level)

            if not unpracticed:
                # Fallback to random practiced lesson if all are completed
                all_lessons = [l for l in db.get_all_lessons() if l["level"] == level]
                if not all_lessons:
                    print(json.dumps({"error": f"No lessons found for level {level}"}))
                    return
                import random
                selected = random.choice(all_lessons)
                is_review = True
            else:
                import random
                selected = random.choice(unpracticed)

        # Mark practiced
        db.mark_lesson_practiced(selected["id"])

        # Load markdown content
        content = db.get_lesson_markdown_content(selected)

        output = {
            "lesson": selected,
            "content": content,
            "is_review": is_review,
            "level": level
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))

    elif args.command == "get-quiz":
        lesson = db.get_lesson_by_id(args.lesson_id)
        if not lesson:
            print(json.dumps({"error": "Lesson not found"}))
            return

        # Provide everything the agent needs to design a quiz from context:
        # the lesson's own content, plus any previously designed questions
        # (prioritizing the user's past mistakes) that can be reused/reviewed.
        content = db.get_lesson_markdown_content(lesson)
        existing_questions = db.get_quiz_questions_for_lesson(args.lesson_id, limit=5)
        output = {
            "lesson_id": lesson["id"],
            "lesson_title": lesson["title"],
            "level": lesson.get("level", "Prepositions"),
            "content_markdown_path": lesson.get("content_markdown_path"),
            "content": content,
            "existing_questions": existing_questions
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))

    elif args.command == "save-quiz":
        try:
            questions = json.loads(args.questions_json)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON for questions"}))
            return
        if isinstance(questions, dict):
            questions = [questions]
        added = db.save_quiz_questions(questions)
        print(json.dumps({"added": added, "total_for_store": len(db.quiz_db.get("quizzes", []))}))

    elif args.command == "record-result":
        try:
            options = json.loads(args.options_json)
        except json.JSONDecodeError:
            options = {}

        is_correct = db.record_quiz_result(
            quiz_id=args.quiz_id,
            lesson_id=args.lesson_id,
            question_text=args.question_text,
            options=options,
            user_answer=args.user_answer,
            correct_answer=args.correct_answer
        )

        print(json.dumps({"is_correct": is_correct}))

    elif args.command == "log-question":
        db.log_user_question(args.lesson_id, args.question)
        print(json.dumps({"status": "success"}))

    elif args.command == "get-stats":
        user_level = db.get_user_level()
        practiced = db.user_db.get("progress", {}).get("practiced_lessons", {})
        incorrect_history = db.user_db.get("progress", {}).get("incorrect_questions_history", [])
        weaknesses = db.get_most_difficult_lessons()

        # Phrase blocks stats
        pb_stats = db.user_db.get("progress", {}).get("phrase_blocks_stats", {
            "total_quizzed": 0,
            "correct_answers": 0,
            "last_practiced": None
        })
        incorrect_pb_ids = db.user_db.get("progress", {}).get("incorrect_phrase_blocks", [])
        all_phrase_blocks = {pb["id"]: pb for pb in db.get_all_phrase_blocks()}
        incorrect_pb_details = [all_phrase_blocks[pbid] for pbid in incorrect_pb_ids if pbid in all_phrase_blocks]

        output = {
            "current_level": user_level,
            "practiced_count": len(practiced),
            "unresolved_mistakes_count": len(incorrect_history),
            "weak_lessons": weaknesses,
            "practiced_lessons": [
                {
                    "lesson_id": lid,
                    "title": (db.get_lesson_by_id(lid)["title"] if db.get_lesson_by_id(lid) else lid),
                    "times_practiced": details["times_practiced"]
                }
                for lid, details in practiced.items()
            ],
            "phrase_blocks_stats": pb_stats,
            "incorrect_phrase_blocks": incorrect_pb_details,
            "saved_phrases": db.get_saved_phrases()
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))

    elif args.command == "get-phrase-quiz":
        limit = getattr(args, "limit", 4)
        selected = db.get_phrase_blocks_for_quiz(limit=limit)
        print(json.dumps({"phrase_blocks": selected}, ensure_ascii=False, indent=2))

    elif args.command == "record-phrase-result":
        is_correct_bool = args.is_correct == "true"
        db.record_phrase_block_result(args.phrase_id, is_correct_bool)
        print(json.dumps({"status": "success"}))

    elif args.command == "progress-server":
        port = getattr(args, "port", 8080)
        run_server(port, data_dir=data_dir)

    elif args.command == "get-contexts":
        contexts = db.get_all_contexts()
        print(json.dumps({"contexts": contexts}, ensure_ascii=False, indent=2))

    elif args.command == "get-random-context":
        import random
        contexts = db.get_all_contexts()
        if contexts:
            selected = random.choice(contexts)
            print(json.dumps({"context": selected}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "No contexts found"}))

    elif args.command == "save-phrase":
        phrase_type = getattr(args, "type", "sentence")
        success = db.save_context_phrase(args.context_id, args.french, args.english, phrase_type)
        print(json.dumps({"success": success}))

    elif args.command == "get-saved-phrases":
        phrases = db.get_saved_phrases(args.context_id)
        print(json.dumps({"saved_phrases": phrases}, ensure_ascii=False, indent=2))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()

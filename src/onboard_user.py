#!/usr/bin/env python3
"""Create an isolated learner profile and language-specific JSON databases."""

import argparse
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOT = BASE_DIR / "databases" / "learners"
CEFR_LEVELS = ("A1", "A2", "B1", "B2")
LEGACY_DATABASE_FILENAMES = (
    "grammar_db.json",
    "prepositions_db.json",
    "phrase_blocks_db.json",
    "quiz_db.json",
    "contexts_db.json",
    "user_db.json",
)

LANGUAGE_ALIASES = {
    "de": ("German", "de", "de-DE", "Standard German"),
    "deutsch": ("German", "de", "de-DE", "Standard German"),
    "german": ("German", "de", "de-DE", "Standard German"),
    "german german": ("German", "de", "de-DE", "Standard German"),
    "hochdeutsch": ("German", "de", "de-DE", "Standard German"),
    "standard german": ("German", "de", "de-DE", "Standard German"),
    "fr": ("French", "fr", "fr-FR", "Standard French"),
    "french": ("French", "fr", "fr-FR", "Standard French"),
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    if not slug:
        raise ValueError("Use a name and target language containing letters or numbers.")
    return slug


def resolve_language(value: str) -> dict:
    key = " ".join(value.strip().lower().split())
    if key in LANGUAGE_ALIASES:
        name, code, locale, variant = LANGUAGE_ALIASES[key]
    else:
        name = value.strip()
        code = slugify(name)
        locale = code
        variant = f"Standard {name}"
    return {
        "name": name,
        "slug": slugify(name),
        "code": code,
        "locale": locale,
        "variant": variant,
    }


def write_json(path: Path, data: dict, overwrite: bool) -> bool:
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return True


def get_profile(args: argparse.Namespace) -> dict:
    user_id = slugify(args.user_id or args.name)
    profile_path = Path(args.data_root).expanduser().resolve() / user_id / "profile.json"
    if not profile_path.exists():
        raise FileNotFoundError(f"No learner profile exists for '{args.name.strip()}'.")

    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Existing profile is not valid JSON: {profile_path}") from error

    return {
        "status": "existing",
        "user_id": user_id,
        "profile_path": str(profile_path),
        "profile": profile,
    }


def migrate_legacy_french(args: argparse.Namespace) -> dict:
    """Copy the pre-multi-learner French store into one named learner profile."""
    user_id = slugify(args.user_id or args.name)
    legacy_dir = BASE_DIR / "databases"
    learner_dir = Path(args.data_root).expanduser().resolve() / user_id
    language_dir = learner_dir / "languages" / "french"
    missing = [filename for filename in LEGACY_DATABASE_FILENAMES if not (legacy_dir / filename).is_file()]
    if missing:
        raise FileNotFoundError(f"Legacy French database file(s) not found: {', '.join(missing)}.")
    if learner_dir.exists():
        raise FileExistsError(
            f"A learner directory already exists for '{args.name.strip()}'. Do not overwrite it; look up that profile instead."
        )

    now = datetime.now(timezone.utc).isoformat()
    legacy_user_db = json.loads((legacy_dir / "user_db.json").read_text(encoding="utf-8"))
    level = legacy_user_db.get("user_profile", {}).get("current_level", "A1")
    if level not in CEFR_LEVELS:
        level = "A1"
    native_language = args.native_language.strip() if args.native_language else "Unknown"
    profile = {
        "schema_version": 1,
        "user_id": user_id,
        "name": args.name.strip(),
        "native_language": native_language,
        "active_language": "french",
        "created_at": now,
        "updated_at": now,
        "languages": {
            "french": {
                "language": "French",
                "language_code": "fr",
                "locale": "fr-FR",
                "variant": "Standard French",
                "added_at": now,
            }
        },
    }
    language_metadata = {
        "schema_version": 1,
        "language": "French",
        "language_code": "fr",
        "locale": "fr-FR",
        "variant": "Standard French",
        "created_at": now,
        "content_status": "migrated",
        "migrated_from": str(legacy_dir),
    }

    language_dir.mkdir(parents=True)
    for filename in LEGACY_DATABASE_FILENAMES:
        shutil.copy2(legacy_dir / filename, language_dir / filename)
    write_json(learner_dir / "profile.json", profile, overwrite=False)
    write_json(language_dir / "language.json", language_metadata, overwrite=False)

    return {
        "status": "migrated",
        "user_id": user_id,
        "profile_path": str(learner_dir / "profile.json"),
        "language_database_path": str(language_dir),
        "language": {"name": "French", "slug": "french", "code": "fr", "locale": "fr-FR"},
        "level": level,
        "legacy_data_preserved": True,
    }


def initialize_databases(args: argparse.Namespace) -> dict:
    level = args.level.upper()
    if level not in CEFR_LEVELS:
        raise ValueError(f"Level must be one of: {', '.join(CEFR_LEVELS)}.")

    user_id = slugify(args.user_id or args.name)
    language = resolve_language(args.target_language)
    now = datetime.now(timezone.utc).isoformat()
    learner_dir = Path(args.data_root).expanduser().resolve() / user_id
    language_dir = learner_dir / "languages" / language["slug"]
    profile_path = learner_dir / "profile.json"

    existing_profile = {}
    if profile_path.exists():
        try:
            existing_profile = json.loads(profile_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"Existing profile is not valid JSON: {profile_path}") from error
        if existing_profile.get("name") and existing_profile["name"] != args.name.strip():
            raise ValueError(
                f"The user ID '{user_id}' is already assigned to {existing_profile['name']!r}. "
                "Choose a distinct --user-id."
            )

    profile = {
        "schema_version": 1,
        "user_id": user_id,
        "name": args.name.strip(),
        "native_language": args.native_language.strip(),
        "active_language": language["slug"],
        "created_at": existing_profile.get("created_at", now),
        "updated_at": now,
        "languages": existing_profile.get("languages", {}),
    }
    profile["languages"][language["slug"]] = {
        "language": language["name"],
        "language_code": language["code"],
        "locale": language["locale"],
        "variant": language["variant"],
        "added_at": profile["languages"].get(language["slug"], {}).get("added_at", now),
    }
    language_metadata = {
        "schema_version": 1,
        "language": language["name"],
        "language_code": language["code"],
        "locale": language["locale"],
        "variant": language["variant"],
        "created_at": now,
        "content_status": "empty",
    }
    user_db = {
        "user_profile": {
            "name": args.name.strip(),
            "target_language": language["name"],
            "language_code": language["code"],
            "locale": language["locale"],
            "variant": language["variant"],
            "native_language": args.native_language.strip(),
            "current_level": level,
            "joined_date": now,
        },
        "progress": {
            "practiced_lessons": {},
            "user_questions_log": [],
            "incorrect_questions_history": [],
            "incorrect_phrase_blocks": [],
            "phrase_blocks_stats": {"total_quizzed": 0, "correct_answers": 0, "last_practiced": None},
            "saved_phrases": {},
        },
    }
    databases = {
        profile_path: profile,
        language_dir / "language.json": language_metadata,
        language_dir / "user_db.json": user_db,
        language_dir / "grammar_db.json": {"lessons": []},
        language_dir / "prepositions_db.json": {"lessons": []},
        language_dir / "phrase_blocks_db.json": {"phrase_blocks": []},
        language_dir / "quiz_db.json": {"quizzes": []},
        language_dir / "contexts_db.json": {"contexts": []},
    }

    existing = [str(path) for path in databases if path != profile_path and path.exists()]
    if existing:
        raise FileExistsError(
            "Language data already exists. Look up and use the existing learner profile instead: " + ", ".join(existing)
        )

    write_json(profile_path, profile, overwrite=True)
    for path, data in databases.items():
        if path != profile_path:
            write_json(path, data, overwrite=False)

    return {
        "status": "created",
        "user_id": user_id,
        "profile_path": str(profile_path),
        "language_database_path": str(language_dir),
        "language": language,
        "level": level,
        "content_status": "empty",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an isolated learner profile and language-specific database set.")
    parser.add_argument("--name", required=True, help="Learner's preferred name")
    parser.add_argument("--show-profile", action="store_true", help="Look up an existing learner without changing it")
    parser.add_argument(
        "--migrate-legacy-french",
        action="store_true",
        help="Copy the pre-existing shared French data into this new learner profile",
    )
    parser.add_argument("--target-language", help="Language to learn")
    parser.add_argument("--level", help="CEFR level: A1, A2, B1, or B2")
    parser.add_argument("--native-language", help="Language for explanations")
    parser.add_argument("--user-id", help="Stable optional learner identifier")
    parser.add_argument("--data-root", default=str(DEFAULT_DATA_ROOT), help="Directory for learner profiles (useful for testing)")
    args = parser.parse_args()

    try:
        if args.show_profile:
            print(json.dumps(get_profile(args), ensure_ascii=False, indent=2))
            return
        if args.migrate_legacy_french:
            print(json.dumps(migrate_legacy_french(args), ensure_ascii=False, indent=2))
            return

        missing = [
            option
            for option, value in {
                "--target-language": args.target_language,
                "--level": args.level,
                "--native-language": args.native_language,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing required option(s): {', '.join(missing)}.")

        print(json.dumps(initialize_databases(args), ensure_ascii=False, indent=2))
    except (ValueError, FileExistsError, FileNotFoundError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

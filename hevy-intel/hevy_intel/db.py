import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from hevy_intel.config import DB_PATH, DATA_DIR


def _get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


@contextmanager
def get_db():
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS workouts (
                id TEXT PRIMARY KEY,
                title TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                raw_json TEXT NOT NULL,
                synced_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sets (
                workout_id TEXT NOT NULL,
                exercise_index INTEGER NOT NULL,
                exercise_title TEXT,
                exercise_template_id TEXT,
                set_index INTEGER NOT NULL,
                set_type TEXT,
                weight_kg REAL,
                reps REAL,
                rpe REAL,
                PRIMARY KEY (workout_id, exercise_index, set_index)
            );

            CREATE TABLE IF NOT EXISTS exercise_templates (
                id TEXT PRIMARY KEY,
                title TEXT,
                primary_muscle_group TEXT,
                secondary_muscle_groups TEXT NOT NULL,
                equipment TEXT,
                synced_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sync_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource TEXT NOT NULL,
                synced_at TEXT NOT NULL,
                records_fetched INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_workouts_start ON workouts(start_time);
            CREATE INDEX IF NOT EXISTS idx_sets_workout ON sets(workout_id);
            CREATE INDEX IF NOT EXISTS idx_sets_template ON sets(exercise_template_id);
        """)


def upsert_workout(data: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO workouts (id, title, start_time, end_time, raw_json, synced_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data["id"], data.get("title"), data["start_time"], data.get("end_time"),
             json.dumps(data), now),
        )
        conn.execute("DELETE FROM sets WHERE workout_id = ?", (data["id"],))
        for exercise in data.get("exercises", []):
            for s in exercise.get("sets", []):
                conn.execute(
                    """INSERT OR REPLACE INTO sets
                       (workout_id, exercise_index, exercise_title, exercise_template_id,
                        set_index, set_type, weight_kg, reps, rpe)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (data["id"], exercise.get("index"), exercise.get("title"),
                     exercise.get("exercise_template_id"), s.get("index"), s.get("type"),
                     s.get("weight_kg"), s.get("reps"), s.get("rpe")),
                )


def delete_workout(workout_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
        conn.execute("DELETE FROM sets WHERE workout_id = ?", (workout_id,))


def upsert_exercise_template(data: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO exercise_templates
               (id, title, primary_muscle_group, secondary_muscle_groups, equipment, synced_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (data["id"], data.get("title"), data.get("primary_muscle_group"),
             json.dumps(data.get("secondary_muscle_groups") or []),
             data.get("equipment"), now),
        )


def log_sync(resource: str, count: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sync_log (resource, synced_at, records_fetched) VALUES (?, ?, ?)",
            (resource, now, count),
        )


def get_cursor(key: str) -> str | None:
    with get_db() as conn:
        row = conn.execute("SELECT value FROM sync_state WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_cursor(key: str, value: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sync_state (key, value) VALUES (?, ?)", (key, value)
        )


def query_recent_workouts(days: int = 30, limit: int = 50) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT raw_json FROM workouts WHERE start_time >= datetime('now', ?) "
            "ORDER BY start_time DESC LIMIT ?",
            (f"-{days} days", limit),
        ).fetchall()
    return [json.loads(r["raw_json"]) for r in rows]


def query_sets_since(days: int) -> list[dict]:
    """Every working set in the window, joined with the exercise template's
    muscle groups — the input muscle.py's fatigue model works from."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT s.exercise_template_id, s.exercise_title, s.set_type, s.weight_kg,
                      s.reps, s.rpe, w.start_time,
                      t.primary_muscle_group, t.secondary_muscle_groups
               FROM sets s
               JOIN workouts w ON w.id = s.workout_id
               LEFT JOIN exercise_templates t ON t.id = s.exercise_template_id
               WHERE w.start_time >= datetime('now', ?)
               ORDER BY w.start_time DESC""",
            (f"-{days} days",),
        ).fetchall()
    return [dict(r) for r in rows]


def exercise_template_count() -> int:
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM exercise_templates").fetchone()
    return row["c"]

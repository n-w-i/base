import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from whoop_core.config import DB_PATH, DATA_DIR


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
            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                start TEXT NOT NULL,
                end_time TEXT,
                strain REAL,
                kilojoule REAL,
                average_heart_rate INTEGER,
                max_heart_rate INTEGER,
                score_state TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                synced_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS recoveries (
                cycle_id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                recovery_score INTEGER,
                resting_heart_rate INTEGER,
                hrv_rmssd_milli REAL,
                spo2_percentage REAL,
                skin_temp_celsius REAL,
                user_calibrating BOOLEAN,
                score_state TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                synced_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sleeps (
                id TEXT PRIMARY KEY,
                cycle_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                start TEXT NOT NULL,
                end_time TEXT NOT NULL,
                nap BOOLEAN NOT NULL,
                total_in_bed_milli INTEGER,
                total_awake_milli INTEGER,
                total_light_sleep_milli INTEGER,
                total_slow_wave_sleep_milli INTEGER,
                total_rem_sleep_milli INTEGER,
                sleep_cycle_count INTEGER,
                disturbance_count INTEGER,
                baseline_need_milli INTEGER,
                need_from_debt_milli INTEGER,
                need_from_strain_milli INTEGER,
                need_from_nap_milli INTEGER,
                respiratory_rate REAL,
                sleep_performance_pct REAL,
                sleep_consistency_pct REAL,
                sleep_efficiency_pct REAL,
                score_state TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                synced_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS workouts (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                start TEXT NOT NULL,
                end_time TEXT NOT NULL,
                sport_id INTEGER,
                sport_name TEXT,
                strain REAL,
                average_heart_rate INTEGER,
                max_heart_rate INTEGER,
                kilojoule REAL,
                distance_meter REAL,
                score_state TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                synced_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource TEXT NOT NULL,
                synced_at TEXT NOT NULL,
                records_fetched INTEGER NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_cycles_start ON cycles(start);
            CREATE INDEX IF NOT EXISTS idx_sleeps_start ON sleeps(start);
            CREATE INDEX IF NOT EXISTS idx_workouts_start ON workouts(start);
            CREATE INDEX IF NOT EXISTS idx_recoveries_cycle ON recoveries(cycle_id);
        """)


def upsert_cycle(data: dict) -> None:
    now = datetime.utcnow().isoformat()
    score = data.get("score") or {}
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO cycles
               (id, user_id, start, end_time, strain, kilojoule,
                average_heart_rate, max_heart_rate, score_state, raw_json, synced_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["id"], data["user_id"], data["start"], data.get("end"),
                score.get("strain"), score.get("kilojoule"),
                score.get("average_heart_rate"), score.get("max_heart_rate"),
                data["score_state"], json.dumps(data), now,
            ),
        )


def upsert_recovery(data: dict) -> None:
    now = datetime.utcnow().isoformat()
    score = data.get("score") or {}
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO recoveries
               (cycle_id, user_id, created_at, recovery_score, resting_heart_rate,
                hrv_rmssd_milli, spo2_percentage, skin_temp_celsius,
                user_calibrating, score_state, raw_json, synced_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["cycle_id"], data["user_id"], data["created_at"],
                score.get("recovery_score"), score.get("resting_heart_rate"),
                score.get("hrv_rmssd_milli"), score.get("spo2_percentage"),
                score.get("skin_temp_celsius"), score.get("user_calibrating"),
                data["score_state"], json.dumps(data), now,
            ),
        )


def upsert_sleep(data: dict) -> None:
    now = datetime.utcnow().isoformat()
    score = data.get("score") or {}
    stages = score.get("stage_summary") or {}
    need = score.get("sleep_needed") or {}
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO sleeps
               (id, cycle_id, user_id, start, end_time, nap,
                total_in_bed_milli, total_awake_milli,
                total_light_sleep_milli, total_slow_wave_sleep_milli,
                total_rem_sleep_milli, sleep_cycle_count, disturbance_count,
                baseline_need_milli, need_from_debt_milli,
                need_from_strain_milli, need_from_nap_milli,
                respiratory_rate, sleep_performance_pct,
                sleep_consistency_pct, sleep_efficiency_pct,
                score_state, raw_json, synced_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["id"], data["cycle_id"], data["user_id"],
                data["start"], data["end"], data["nap"],
                stages.get("total_in_bed_time_milli"),
                stages.get("total_awake_time_milli"),
                stages.get("total_light_sleep_time_milli"),
                stages.get("total_slow_wave_sleep_time_milli"),
                stages.get("total_rem_sleep_time_milli"),
                stages.get("sleep_cycle_count"),
                stages.get("disturbance_count"),
                need.get("baseline_milli"),
                need.get("need_from_sleep_debt_milli"),
                need.get("need_from_recent_strain_milli"),
                need.get("need_from_recent_nap_milli"),
                score.get("respiratory_rate"),
                score.get("sleep_performance_percentage"),
                score.get("sleep_consistency_percentage"),
                score.get("sleep_efficiency_percentage"),
                data["score_state"], json.dumps(data), now,
            ),
        )


def upsert_workout(data: dict) -> None:
    now = datetime.utcnow().isoformat()
    score = data.get("score") or {}
    with get_db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO workouts
               (id, user_id, start, end_time, sport_id, sport_name,
                strain, average_heart_rate, max_heart_rate, kilojoule,
                distance_meter, score_state, raw_json, synced_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["id"], data["user_id"], data["start"], data["end"],
                data.get("sport_id"), data.get("sport_name"),
                score.get("strain"), score.get("average_heart_rate"),
                score.get("max_heart_rate"), score.get("kilojoule"),
                score.get("distance_meter"),
                data["score_state"], json.dumps(data), now,
            ),
        )


def log_sync(resource: str, count: int) -> None:
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO sync_log (resource, synced_at, records_fetched) VALUES (?, ?, ?)",
            (resource, now, count),
        )


def query_recent(table: str, days: int = 30, limit: int = 100) -> list[dict]:
    time_col = "created_at" if table == "recoveries" else "start"
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT raw_json FROM {table} WHERE {time_col} >= datetime('now', ?) ORDER BY {time_col} DESC LIMIT ?",
            (f"-{days} days", limit),
        ).fetchall()
    return [json.loads(r["raw_json"]) for r in rows]

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import EngineeringRecord, EngineeringRecordCreate

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("ENGRAMOPS_DB_PATH", str(BASE_DIR / "data" / "engramops.db")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                incident_type TEXT NOT NULL,
                system_name TEXT NOT NULL,
                severity TEXT NOT NULL,
                summary TEXT NOT NULL,
                context TEXT NOT NULL,
                changes_json TEXT NOT NULL,
                symptoms_json TEXT NOT NULL,
                root_cause TEXT NOT NULL,
                attempted_fixes_json TEXT NOT NULL,
                outcome TEXT NOT NULL,
                lessons_json TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_json TEXT NOT NULL,
                output_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)


def create_record(data: EngineeringRecordCreate) -> EngineeringRecord:
    created_at = datetime.now(timezone.utc)
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO records (
              title, incident_type, system_name, severity, summary, context,
              changes_json, symptoms_json, root_cause, attempted_fixes_json,
              outcome, lessons_json, tags_json, occurred_at, source, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (data.title, data.incident_type, data.system, data.severity, data.summary,
             data.context, json.dumps(data.changes), json.dumps(data.symptoms),
             data.root_cause, json.dumps(data.attempted_fixes), data.outcome,
             json.dumps(data.lessons), json.dumps(data.tags), data.occurred_at.isoformat(),
             data.source, created_at.isoformat()))
        record_id = int(cur.lastrowid)
    return get_record(record_id)


def row_to_record(row: sqlite3.Row) -> EngineeringRecord:
    return EngineeringRecord(
        id=row["id"], title=row["title"], incident_type=row["incident_type"],
        system=row["system_name"], severity=row["severity"], summary=row["summary"],
        context=row["context"], changes=json.loads(row["changes_json"]),
        symptoms=json.loads(row["symptoms_json"]), root_cause=row["root_cause"],
        attempted_fixes=json.loads(row["attempted_fixes_json"]), outcome=row["outcome"],
        lessons=json.loads(row["lessons_json"]), tags=json.loads(row["tags_json"]),
        occurred_at=datetime.fromisoformat(row["occurred_at"]),
        source=row["source"], created_at=datetime.fromisoformat(row["created_at"]))


def get_record(record_id: int) -> EngineeringRecord:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
    if row is None:
        raise KeyError(record_id)
    return row_to_record(row)


def list_records(limit: int = 100) -> list[EngineeringRecord]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM records ORDER BY occurred_at DESC, id DESC LIMIT ?", (limit,)).fetchall()
    return [row_to_record(row) for row in rows]


def stats() -> dict[str, int]:
    with get_conn() as conn:
        row = conn.execute("""SELECT COUNT(*) total,
          SUM(CASE WHEN outcome='failure' THEN 1 ELSE 0 END) failures,
          SUM(CASE WHEN outcome='partial' THEN 1 ELSE 0 END) partial,
          SUM(CASE WHEN outcome='success' THEN 1 ELSE 0 END) successes,
          SUM(CASE WHEN severity IN ('critical','high') THEN 1 ELSE 0 END) critical_high
          FROM records""").fetchone()
    return {"total": row["total"] or 0, "failures": row["failures"] or 0,
            "partial": row["partial"] or 0, "successes": row["successes"] or 0,
            "critical_high": row["critical_high"] or 0}


def store_analysis(input_payload: dict[str, Any], output_payload: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute("INSERT INTO analyses (input_json, output_json, created_at) VALUES (?, ?, ?)",
                     (json.dumps(input_payload), json.dumps(output_payload),
                      datetime.now(timezone.utc).isoformat()))
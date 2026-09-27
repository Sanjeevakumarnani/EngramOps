from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from .models import EngineeringRecord, EngineeringRecordCreate


def parse_json(value: str | None) -> Any:
    if not value or not value.strip():
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {exc.msg}") from exc


def parse_pipe_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=str)


def record_to_memory(record: EngineeringRecord) -> str:
    return f"""Engineering memory record #{record.id}
Title: {record.title}
Type: {record.incident_type}
System: {record.system}
Severity: {record.severity}
Occurred: {record.occurred_at.isoformat()}
Summary: {record.summary}
Context: {record.context}
Changes: {', '.join(record.changes) or 'None'}
Symptoms: {', '.join(record.symptoms) or 'None'}
Root cause: {record.root_cause or 'Unknown'}
Attempted fixes: {', '.join(record.attempted_fixes) or 'None'}
Outcome: {record.outcome}
Lessons: {', '.join(record.lessons) or 'None'}
Tags: {', '.join(record.tags) or 'None'}
Source: {record.source}
""".strip()


def records_from_csv(text: str) -> tuple[list[EngineeringRecordCreate], list[str]]:
    rows = csv.DictReader(io.StringIO(text))
    records: list[EngineeringRecordCreate] = []
    errors: list[str] = []
    for idx, row in enumerate(rows, start=2):
        try:
            raw_date = (row.get("occurred_at") or "").strip()
            occurred_at = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else datetime.now(timezone.utc)
            records.append(
                EngineeringRecordCreate(
                    title=(row.get("title") or "Untitled record").strip(),
                    incident_type=(row.get("incident_type") or "incident").strip(),
                    system=(row.get("system") or "").strip(),
                    severity=(row.get("severity") or "medium").strip().lower(),
                    summary=(row.get("summary") or "").strip(),
                    context=(row.get("context") or "").strip(),
                    changes=parse_pipe_list(row.get("changes")),
                    symptoms=parse_pipe_list(row.get("symptoms")),
                    root_cause=(row.get("root_cause") or "").strip(),
                    attempted_fixes=parse_pipe_list(row.get("attempted_fixes")),
                    outcome=(row.get("outcome") or "unknown").strip().lower(),
                    lessons=parse_pipe_list(row.get("lessons")),
                    tags=parse_pipe_list(row.get("tags")),
                    occurred_at=occurred_at,
                    source=(row.get("source") or "csv").strip(),
                )
            )
        except Exception as exc:
            errors.append(f"Row {idx}: {exc}")
    return records, errors


def slugify(value: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe or "default"
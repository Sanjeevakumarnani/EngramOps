from app.models import EngineeringRecord
from app.utils import parse_pipe_list, records_from_csv, record_to_memory


def test_parse_pipe_list():
    assert parse_pipe_list("a | b|| c") == ["a", "b", "c"]


def test_demo_csv_parses():
    csv_text = """title,incident_type,system,severity,summary,context,changes,symptoms,root_cause,attempted_fixes,outcome,lessons,tags,occurred_at,source
Example,incident,API,high,summary,context,cache|ttl,stale,root,rollback,success,lesson,cache,2026-01-01T00:00:00Z,test
"""
    records, errors = records_from_csv(csv_text)
    assert not errors
    assert len(records) == 1
    assert records[0].title == "Example"


def test_memory_format():
    record = EngineeringRecord(
        id=1, title="Test", incident_type="incident", system="API", severity="high",
        summary="s", context="c", changes=[], symptoms=[], root_cause="r",
        attempted_fixes=[], outcome="success", lessons=["l"], tags=["t"],
        occurred_at="2026-01-01T00:00:00Z", source="test",
        created_at="2026-01-01T00:00:00Z")
    assert "Engineering memory record #1" in record_to_memory(record)
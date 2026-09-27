from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

Outcome = Literal["failure", "partial", "success", "unknown"]
Severity = Literal["critical", "high", "medium", "low"]


class EngineeringRecordCreate(BaseModel):
    title: str
    incident_type: str = "incident"
    system: str = ""
    severity: Severity = "medium"
    summary: str = ""
    context: str = ""
    changes: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)
    root_cause: str = ""
    attempted_fixes: list[str] = Field(default_factory=list)
    outcome: Outcome = "unknown"
    lessons: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = "manual"


class EngineeringRecord(EngineeringRecordCreate):
    id: int
    created_at: datetime


class ChangePlanInput(BaseModel):
    system: str = ""
    change: str = ""
    goal: str = ""
    context: str = ""
    constraints: list[str] = Field(default_factory=list)
    notes: str = ""


class RiskAnalysis(BaseModel):
    risk_level: Literal["low", "medium", "high"] = "medium"
    confidence: Literal["low", "medium", "high"] = "medium"
    summary: str = ""
    historical_matches: list[str] = Field(default_factory=list)
    recurring_patterns: list[str] = Field(default_factory=list)
    likely_failure_mechanisms: list[str] = Field(default_factory=list)
    contradictions_or_exceptions: list[str] = Field(default_factory=list)
    preventative_actions: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)


class ProjectStats(BaseModel):
    total_records: int = 0
    failures: int = 0
    partial: int = 0
    successes: int = 0
    critical_high: int = 0
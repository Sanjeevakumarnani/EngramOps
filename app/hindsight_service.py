from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError

from .models import ChangePlanInput, EngineeringRecord, RiskAnalysis
from .utils import pretty_json, record_to_memory, slugify

load_dotenv()

class HindsightUnavailable(RuntimeError):
    pass

MISSION = ("Build durable engineering memory from incidents, changes, root causes, attempted fixes, outcomes, "
           "and lessons learned. Prefer reusable experience over transient chatter. Surface contradictions and uncertainty.")
GUARDRAIL = ("Provide decision support, not autonomous production control. Do not execute destructive actions, expose secrets, "
             "or provide unsafe operational instructions. Recommend human review for high-impact changes.")

@lru_cache(maxsize=1)
def get_client():
    base_url = os.getenv("HINDSIGHT_BASE_URL", "").strip()
    api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
    if not base_url:
        raise HindsightUnavailable("HINDSIGHT_BASE_URL is not configured")
    try:
        from hindsight_client import Hindsight
    except ImportError as exc:
        raise HindsightUnavailable("hindsight-client is not installed") from exc
    kwargs: dict[str, Any] = {"base_url": base_url}
    if api_key:
        kwargs["api_key"] = api_key
    return Hindsight(**kwargs)

class EngineeringMemory:
    def __init__(self) -> None:
        self.client = get_client()

    @staticmethod
    def bank_id() -> str:
        return slugify("engramops-engineering-memory")[:120]

    def ensure_bank(self) -> None:
        bank = self.bank_id()
        try:
            self.client.create_bank(bank_id=bank, name="Engineering Memory OS")
        except Exception:
            pass
        try:
            self.client.update_bank_config(
                bank, retain_mission=MISSION, retain_extraction_mode="verbose",
                observations_mission=("Track repeated causes, fragile dependencies, recurring change failures, successful "
                                      "mitigations, and lessons that should influence future engineering decisions."),
                disposition_skepticism=5, disposition_literalism=4, disposition_empathy=1)
        except Exception:
            pass
        try:
            self.client.create_directive(bank_id=bank, name="Decision Safety", content=GUARDRAIL)
        except Exception:
            pass

    def retain_record(self, record: EngineeringRecord) -> None:
        self.ensure_bank()
        tags = [f"outcome:{record.outcome}", f"severity:{record.severity}",
                f"system:{slugify(record.system)[:50]}", f"type:{slugify(record.incident_type)[:50]}"] +                [f"tag:{slugify(tag)[:50]}" for tag in record.tags]
        self.client.retain(bank_id=self.bank_id(), content=record_to_memory(record),
                           context="engineering incident and decision record",
                           timestamp=record.occurred_at.isoformat(),
                           document_id=f"record-{record.id}", tags=tags)

    def recall_for_plan(self, plan: ChangePlanInput, limit: int = 8) -> list[dict[str, Any]]:
        self.ensure_bank()
        query = (f"Find historical engineering incidents and decisions similar to this proposed change. "
                 f"System: {plan.system}. Change: {plan.change}. Goal: {plan.goal}. Context: {plan.context}. "
                 f"Constraints: {pretty_json(plan.constraints)}. Notes: {plan.notes}")
        result = self.client.recall(bank_id=self.bank_id(), query=query,
                                    tags=["outcome:failure","outcome:partial","outcome:success"],
                                    tags_match="any_strict")
        rows = getattr(result, "results", result)
        return [{"text": getattr(item, "text", str(item)), "type": getattr(item, "type", "memory"),
                 "context": getattr(item, "context", ""), "occurred_start": getattr(item, "occurred_start", None)}
                for item in list(rows)[:limit]]

    def analyze_plan(self, plan: ChangePlanInput) -> RiskAnalysis:
        self.ensure_bank()
        query = f"""You are an engineering decision-memory analyst.

Proposed change:
System: {plan.system}
Change: {plan.change}
Goal: {plan.goal}
Context: {plan.context}
Constraints: {pretty_json(plan.constraints)}
Notes: {plan.notes}

Use remembered engineering experience to analyze whether this change resembles prior failures, partial successes,
repeated causes, or exceptions. Focus on evidence from memory. Do not invent benchmarks or pretend to have live system access.
Return a concise, structured engineering review containing:
- overall risk level
- confidence
- concise summary
- historical matches
- recurring patterns
- likely failure mechanisms
- contradictions/exceptions
- preventative actions for human review
- evidence""".strip()
        response = self.client.reflect(bank_id=self.bank_id(), query=query,
                                       response_schema=RiskAnalysis.model_json_schema(), include_facts=True)
        structured = getattr(response, "structured_output", None) or {}
        try:
            return RiskAnalysis.model_validate(structured)
        except ValidationError:
            return RiskAnalysis(risk_level="medium", confidence="low",
                                 summary="Hindsight returned an unstructured analysis; review retrieved evidence manually.",
                                 evidence=[getattr(response, "text", "")])

    def memory_views(self) -> dict[str, str]:
        self.ensure_bank()
        queries = {
            "Recurring failure patterns": "What failure patterns have repeatedly appeared in our engineering history?",
            "What actually worked": "Which recovery or prevention approaches have worked repeatedly, and under what conditions?",
            "Fragile dependencies": "Which systems, dependencies, or change combinations repeatedly correlate with failure?",
            "Institutional lessons": "What durable engineering lessons should influence future decisions?"}
        output: dict[str, str] = {}
        for title, query in queries.items():
            try:
                response = self.client.reflect(bank_id=self.bank_id(), query=query, include_facts=True)
                output[title] = getattr(response, "text", "") or "No memory summary available yet."
            except Exception as exc:
                output[title] = f"Unavailable: {exc}"
        return output
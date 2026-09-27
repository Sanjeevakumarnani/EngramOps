from __future__ import annotations

import os
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import create_record, get_record, init_db, list_records, stats, store_analysis
from .hindsight_service import EngineeringMemory, HindsightUnavailable
from .models import ChangePlanInput, EngineeringRecordCreate
from .utils import parse_pipe_list, records_from_csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = FastAPI(title="EngramOps — Engineering Failure & Decision Memory")
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

@app.on_event("startup")
def startup() -> None:
    init_db()

def hindsight_status() -> str:
    if not os.getenv("HINDSIGHT_BASE_URL"):
        return "Demo mode — configure HINDSIGHT_BASE_URL to activate persistent memory."
    try:
        EngineeringMemory()
        return "Hindsight configured."
    except HindsightUnavailable as exc:
        return str(exc)
    except Exception as exc:
        return f"Hindsight connection check failed: {exc}"

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html",
        {"request": request, "records": list_records(), "stats": stats(), "hindsight_status": hindsight_status()})

@app.post("/records")
def add_record(title: str = Form(...), incident_type: str = Form("incident"), system: str = Form(""),
               severity: str = Form("medium"), summary: str = Form(""), context: str = Form(""),
               changes: str = Form(""), symptoms: str = Form(""), root_cause: str = Form(""),
               attempted_fixes: str = Form(""), outcome: str = Form("unknown"), lessons: str = Form(""),
               tags: str = Form("")) -> RedirectResponse:
    record = create_record(EngineeringRecordCreate(
        title=title, incident_type=incident_type, system=system, severity=severity.lower(),
        summary=summary, context=context, changes=parse_pipe_list(changes), symptoms=parse_pipe_list(symptoms),
        root_cause=root_cause, attempted_fixes=parse_pipe_list(attempted_fixes), outcome=outcome.lower(),
        lessons=parse_pipe_list(lessons), tags=parse_pipe_list(tags)))
    try:
        EngineeringMemory().retain_record(record)
    except Exception:
        pass
    return RedirectResponse(url=f"/?selected={record.id}", status_code=303)

@app.post("/import")
async def import_csv(file: UploadFile = File(...)) -> RedirectResponse:
    text = (await file.read()).decode("utf-8")
    records, _errors = records_from_csv(text)
    memory = None
    try:
        memory = EngineeringMemory()
        memory.ensure_bank()
    except Exception:
        pass
    for data in records:
        record = create_record(data)
        if memory:
            try:
                memory.retain_record(record)
            except Exception:
                pass
    return RedirectResponse(url="/", status_code=303)

@app.post("/analyze")
def analyze(system: str = Form(""), change: str = Form(...), goal: str = Form(""),
            context: str = Form(""), constraints: str = Form(""), notes: str = Form("")) -> RedirectResponse:
    plan = ChangePlanInput(system=system, change=change, goal=goal, context=context,
                           constraints=parse_pipe_list(constraints), notes=notes)
    try:
        memory = EngineeringMemory()
        analysis = memory.analyze_plan(plan)
        similar = memory.recall_for_plan(plan)
        store_analysis(plan.model_dump(), {"analysis": analysis.model_dump(), "similar": similar, "memory_live": True})
    except Exception as exc:
        payload = {"analysis": {"risk_level":"medium","confidence":"low",
            "summary":f"Memory analysis is unavailable: {exc}","historical_matches":[],"recurring_patterns":[],
            "likely_failure_mechanisms":[],"contradictions_or_exceptions":[],
            "preventative_actions":["Connect Hindsight and rerun the analysis."],"evidence":[]},
            "similar":[],"memory_live":False}
        store_analysis(plan.model_dump(), payload)
    return RedirectResponse(url="/analysis?result=1", status_code=303)

@app.get("/analysis", response_class=HTMLResponse)
def analysis_page(request: Request):
    return templates.TemplateResponse(request, "analysis.html",
        {"request": request, "hindsight_status": hindsight_status()})

@app.get("/api/latest-analysis")
def latest_analysis():
    import json
    from .db import get_conn
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        return JSONResponse({})
    return JSONResponse({"input": json.loads(row["input_json"]), **json.loads(row["output_json"]), "created_at": row["created_at"]})

@app.get("/api/records")
def records_api():
    return [record.model_dump(mode="json") for record in list_records()]

@app.get("/api/records/{record_id}")
def record_api(record_id: int):
    return get_record(record_id).model_dump(mode="json")

@app.get("/api/memory-views")
def memory_views():
    try:
        return {"live": True, "views": EngineeringMemory().memory_views()}
    except Exception as exc:
        return {"live": False, "views": {}, "error": str(exc)}

@app.get("/demo")
def demo():
    if list_records():
        return RedirectResponse(url="/")
    sample = os.path.join(BASE_DIR, "data", "demo_incidents.csv")
    with open(sample, "r", encoding="utf-8") as fh:
        content = fh.read()
    records, _errors = records_from_csv(content)
    memory = None
    try:
        memory = EngineeringMemory()
        memory.ensure_bank()
    except Exception:
        pass
    for data in records:
        record = create_record(data)
        if memory:
            try:
                memory.retain_record(record)
            except Exception:
                pass
    return RedirectResponse(url="/", status_code=303)

@app.get("/health")
def health():
    return {"status": "ok", "hindsight": hindsight_status()}
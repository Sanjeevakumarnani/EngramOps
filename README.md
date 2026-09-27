# EngramOps

## Engineering Failure & Decision Memory

EngramOps is a Hindsight-powered memory layer for engineering teams. It turns incidents, changes, root causes, attempted fixes, outcomes, and lessons into durable memory, then recalls relevant experience when an engineer proposes a similar change.

### Why it exists

Engineering teams repeatedly encounter the same failure mechanisms: retry amplification, unsafe caching, coupled deployments, migration timing, dependency timeouts, idempotency gaps, and fragile cross-service assumptions. Postmortems are often stored, but the lesson is not available at the moment a new decision is made.

EngramOps makes that memory operationally visible:

**RETAIN → HINDSIGHT → RECALL → DECISION**

### Core workflow

1. Capture an incident, near-miss, change, experiment, or decision.
2. Store a structured local record and retain a normalized memory in Hindsight.
3. Propose a future engineering change.
4. Recall historically similar failures and successes.
5. Ask Hindsight to synthesize recurring patterns, likely failure mechanisms, exceptions, preventative actions, and evidence.
6. Keep the engineer in the decision loop; EngramOps does not autonomously modify production systems.

### Hindsight integration

Memory bank: `engramops-engineering-memory`

Environment variables:

- `HINDSIGHT_BASE_URL`
- `HINDSIGHT_API_KEY`
- `ENGRAMOPS_DB_PATH`

Hindsight operations used by the application:

- `retain` — durable engineering records
- `recall` — historical matches for proposed changes
- `reflect` — structured risk analysis and living memory views

### Features

- FastAPI web dashboard
- SQLite local record store
- Hindsight persistent memory
- 12-record synthetic engineering history
- CSV import
- Memory-backed change analysis
- Recurring failure-pattern views
- What-worked / fragile-dependency / institutional-lesson views
- JSON API
- Docker and Render configuration
- Automated tests

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000`.

Without Hindsight credentials the application runs in demo mode. Use **Load 12-record demo memory** to populate the local timeline.

### Production

Set the Hindsight variables in the deployment environment, then run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

A `render.yaml` and `Dockerfile` are included.

### API

- `GET /`
- `GET /health`
- `GET /api/records`
- `GET /api/records/{id}`
- `GET /api/latest-analysis`
- `GET /api/memory-views`
- `POST /records`
- `POST /import`
- `POST /analyze`
- `GET /demo`

### Safety

EngramOps is decision support. It does not execute destructive production actions, expose secrets, or replace human approval for high-impact engineering changes.

### Validation

The project has been validated locally with Python compilation, pytest, CSV parsing, and local HTTP smoke tests. Live Hindsight behavior requires valid Hindsight credentials and is intentionally not represented as verified without them.

### Attribution

This repository is a clean-room reimplementation and domain adaptation inspired by the public architecture and Hindsight integration of FailTrace. See [UPSTREAM.md](UPSTREAM.md).

## License

MIT

# SignalTrust Mission Control v4 — Radiation + TimeShield Research Prototype

**Research/demo-only, no clinical validation.** Existing SignalTrust v3.1 PPG pipeline preserved. New modules: historical ISS DosTel radiation integrity/covered-interval estimation, and deterministic event-time replay for late, duplicate and out-of-order synthetic telemetry. **No Supabase, RBAC, persistent DB/outbox or live astronaut data.**

## Start on Windows (two terminals)

Unzip to a short local path and open **PowerShell terminal 1** in `SignalTrust_Mission_Control`:

```powershell
.\run_preview_windows.bat
```

This starts the FastAPI backend and an npm-free standalone dashboard at http://127.0.0.1:8000. Open http://127.0.0.1:8000/docs for the OpenAPI documentation. Use the **Radiation Context** and **TimeShield** sidebar entries to open the new modules.

For the full **Next.js** UI, open **PowerShell terminal 2** in the same root folder:

```powershell
.\run_next_windows.bat
```

Next.js should open at http://127.0.0.1:3000, with the same Radiation and TimeShield pages at `/radiation` and `/timeshield`. Ensure `frontend/.env.local` contains `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`. New pages require a running backend; unlike some existing mock health cards, they do not silently substitute fake NASA radiation observations if the server is down.

If the `.bat` launcher fails, run manually:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

For frontend (new terminal):

```powershell
cd frontend
copy .env.example .env.local
npm install
npm run dev
npm run typecheck
npm run build
```

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Expected on included code: **23 passing** tests. See `docs/QA_REPORT_V4.md` for what was and was not verified in the authoring environment.

## API endpoints

- `GET /api/radiation/summary?max_interval_seconds=300`
- `GET /api/radiation/instruments/DosTel1?max_interval_seconds=300`
- `GET /api/timeshield/scenarios`
- `POST /api/timeshield/replay` with JSON `{"scenario":"late"}`
- Existing PPG routes `/api/datasets`, `/api/analyses`, `/api/evaluations`, etc. are unchanged.

## What is real and what is simulated?

| Capability | Source | Status |
|---|---|---|
| PPG filters, quality and rate | Supplied BIDMC terrestrial recording | Real local processing; nonclinical |
| Radiation instrument rate and coverage | `backend/sample_data/radlab_iss_dostel_2022.csv`, uploaded by team | Historical instrument sample (2022); source not independently re-fetched |
| TimeShield event-time replay | Deterministic synthetic fixtures | Simulated in memory, no durable transport |
| Crew health, SpO2, sleep, stress, bone and immune | Synthetic dashboard fixtures | Not connected to real sources |
| Supabase auth, RLS, persistent history | None | Deferred |

The radiation computation expresses instrument absorbed dose rates in **µGy/hour**, integrated to **µGy** for accepted intervals. Missing intervals do not become zero, and full-span total is reported *undetermined* when gaps exist. These values **must not** be presented as an astronaut's personal radiation dose or long-term health risk.

The TimeShield engine proves a limited event-ordering invariant in deterministic replay. It does **not** implement or claim the architecture's persistent outbox, WebSockets, LISTEN/NOTIFY, end-to-end delivery guarantees, or propagation-latency reduction. See `docs/ARCHITECTURE_V4_RADIATION_TIMESHIELD.md`.

## Contents

- `frontend/`: Next.js TypeScript, role-aware dashboards, typed `reliabilityApi`, `/radiation` + `/timeshield` routes
- `backend/`: FastAPI, original processing modules, `radiation_service.py`, `timeshield_service.py`, router and tests
- `standalone/`: no-build preview, same data contracts, sidebar pages
- `docs/source_radlab/`: unmodified user-supplied experiment scripts for provenance
- `docs/`: architecture, QA and render screenshots

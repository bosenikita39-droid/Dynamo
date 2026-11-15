# SignalTrust - backend-only preservation package

## Why this package exists
The Emergent application in the uploaded `nasa hackathon.zip.zip` included 78 file entries, all with **zero-byte contents**. No runnable original React components were available. The prior v1 prototype therefore supplied a different UI. That UI has deliberately been **excluded** from this package.

This package preserves the Python processing adapter and its API routes, and **does not touch your original frontend**. It is NOT a completed merge of the old frontend: please re-export the actual Emergent frontend source before integration. Do not deploy this unauthenticated demo API publicly.

## Local Windows backend setup

From the extracted `signaltrust_preserve_ui` folder:

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

- Health check: http://127.0.0.1:8000/api/health
- API docs: http://127.0.0.1:8000/docs
- The root page `/` intentionally returns 404: there is no replacement dashboard.
- Existing frontend may run on localhost port **5173** or **3000**, and call `http://127.0.0.1:8000/api/...`. The old frontend code has not been modified or verified.

## Original UI integration after a correct source export

1. Obtain an Emergent ZIP with nonzero `frontend/src/App.tsx`, `frontend/src/pages/*.tsx`, `frontend/package.json` and CSS files.
2. Preserve the app shell, routes, dashboard pages, styling, and existing mock components.
3. Compare `frontend/src/lib/api.ts`, `apiService.ts`, and `types/index.ts` to `docs/API_CONTRACTS.md`.
4. Point only the signal-analysis / dataset / evaluation features to the actual API, using an environment-configured base URL. Leave unrelated astronaut-health UI unchanged.
5. Verify both dev servers, navigation, API calls, and error states. Do not claim success until this has been tested.

## Scope

Includes PPG preprocessing, filtering, quality assessment, CSV ingestion, analysis/evaluation endpoints, in-process history, and tests. No Supabase, authentication, database persistence, clinical validation, or personal astronaut data.

## Origins and privacy

CORS allows localhost ports 5173 and 3000 for development. This is not an access-control mechanism. The local API is not authenticated.

# SignalTrust v3 — Next.js Frontend

This is the editable production-style frontend source implementing the provided dark aerospace mission-control visual direction. The user interface is code, not a static mockup image.

- `components/RoleGate.tsx`: demo role selection.
- `components/MissionV3.tsx`: admin overview, astronaut overview, scientific Signal Lab, datasets, evaluation, history and settings.
- `app/mission-v3.css`, `app/login-v3.css`: visual system.
- `lib/types.ts`: typed contract. `lib/api.ts`: actual FastAPI HTTP adapter. `lib/bridge.ts`: API-first/fallback service.
- `public/mock/`: precomputed demonstration responses. Only the known BIDMC sample has offline analysis fixtures; uploaded recordings require FastAPI.
- `public/assets/`: decorative images cropped from the approved/generated design concept.

## Run

From repository root, start the unchanged local backend via `run_preview_windows.bat` (port 8000). Then in `frontend/`:

```
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. Copy `.env.example` to `.env.local` if needed. Environment variable `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000` points at the local backend.

`npm run typecheck` and `npm run build` must be performed on a machine able to install npm dependencies; these builds could not be verified in the artifact environment. The zero-build preview at port 8000 is a separate browser fallback provided for testing without npm.

Everything shown in crew health dashboards is synthetic research demo data. PPG analysis results from the live API use the bundled terrestrial BIDMC dataset. No authentication, database, or clinical validation is implemented.

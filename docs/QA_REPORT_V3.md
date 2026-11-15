# SignalTrust UI v3 - Verification status

## Confirmed in the preparation environment

- Existing FastAPI backend imported and executed an analysis on `bidmc_01` successfully.
- 11 FastAPI tests passed via `python -m pytest -q`, including dataset upload, analysis, evaluation, static preview route and mission-health fixture routes.
- Zero-build preview JavaScript passed Node.js syntax check (`node --check standalone/app.js`).
- `MissionV3.tsx`, `RoleGate.tsx` and `bridge.ts` passed TypeScript transpilation syntax diagnostics (zero).
- Static UI assets, CSS and mock fixture files were checked for existence.
- The local FastAPI server served the preview and endpoints successfully via HTTP/TestClient.

## Not confirmed

- Next.js `npm run typecheck` or `npm run build`: package registry access failed in the preparation environment.
- Automated browser screenshot / click-through test: Chromium policy blocked both localhost and file URLs, so this was not completed. Use the local Windows run procedure to review and verify the visual match.
- Real astronaut health accuracy, NASA mission integration, multi-user RBAC or live radiation/SpO2 feeds: not implemented.

## Acceptance checklist for the receiving developer

1. Run `run_preview_windows.bat`; visit `http://127.0.0.1:8000/` and choose a demo role.
2. Navigate all seven internal pages from sidebar.
3. Open Signal Lab; run `Start Analysis` with 0% and 80% Gaussian noise and observe different results.
4. Open Evaluation Lab and run the controlled evaluation.
5. Upload a valid CSV on Dataset Management and verify catalog refresh; reject an invalid file.
6. Verify History shows recent analysis sessions until the process restarts.
7. Install frontend dependencies; run `npm run typecheck` and `npm run build` and fix any environment-specific errors.
8. Check desktop (1448px) and mobile (390px) layouts, keyboard accessibility and browser console.

## Data provenance rules

- Mission overview and astronaut health readings: synthetic demo data.
- Radiation: synthetic environmental instrument context, not personal dose.
- Waveforms: real bundled BIDMC terrestrial PPG samples processed by Python or labelled precomputed demo fixtures.
- Baseline and evaluation outputs: research estimates; not independently established clinical false-positive rates.

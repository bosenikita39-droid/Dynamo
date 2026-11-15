# SignalTrust v3.1 - Stability review and regression results

Date: November 15, 2026. Scope: UI stability, typed frontend service layer, standalone preview, and existing FastAPI contracts. **TimeShield is not implemented.**

## Findings and fixes

| ID | Area | Failure / risk | Correction |
|---|---|---|---|
| ST-01 | Original waveform | A 0%-noise analysis returns `waveform.reference=null`. The UI plotted `reference` unconditionally, leaving the original trace blank. | Original waveform now uses `waveform.reference ?? waveform.raw`. No signal-processing algorithm changed. |
| ST-02 | Role navigation | Demo role could silently reset when navigating from astronaut screen to Signal Lab or history. | Store the explicitly selected demo role in browser `sessionStorage` and restore it across routes; admin remains admin when previewing astronaut page. Not security enforcement. |
| ST-03 | API fallback | A backend 404/422/500 could be hidden by offline fixture substitution. | Fallback only on transport-level connection errors (status 0); propagate real HTTP errors to UI. Uploaded recordings always require the backend. |
| ST-04 | ECG selector | Selecting an ECG placeholder left the PPG pipeline running, with misleading active ECG text. | ECG marked disabled/planned until the Python service supports ECG. |
| ST-05 | Stale comparison | Original graphs could remain visible after recording/noise parameters changed, implying the old analysis reflected new controls. | Clear previous result and prompt user to rerun analysis when inputs change. |
| ST-06 | Crew navigation | Clicking a crew card did not reliably show that crew's demo health indicators. | Store selected crew ID and open the corresponding astronaut view; standalone preview reloads that crew's demo health. |
| ST-07 | Dead controls | Info / Checks / Context tabs changed only visual state or did nothing. | Tabs now display distinct research / quality / provenance content. |
| ST-08 | Preferences | Grid and explanation controls did not affect the laboratory; page changes reset preferences. | Persist local demo preferences; expose Plotly grid toggle, explanation panel toggle, and reduced motion. |
| ST-09 | Standalone recording selection | Upload succeeded, but the standalone Signal Lab still analyzed only bundled BIDMC 01. | Added a functional recording selector; uploads become selectable in the preview. |
| ST-10 | Navigation scroll | Hash navigation could preserve the previous page's scroll position and make panels appear displaced after navigation. | Reset to top when switching standalone pages. |
| ST-11 | UI mobile menu | Navigation drawer had no accessible outside-click dismiss target. | Added a mobile backdrop control to the Next.js navigation. |
| ST-12 | Windows setup | Install failures could be followed by misleading startup commands. | Batch startup scripts stop on dependency installation errors. |

## Tests actually executed

- **15/15 backend tests passed** (`cd backend && python -m pytest -q`). Includes new tests for zero-noise waveform behavior, demo metric/alert contracts, trend and settings endpoints, CORS and error response semantics.
- Typed bridge behavior validated by Node/TypeScript transpilation harness: API success, network offline fallback, and HTTP 422 propagation.
- `standalone/app.js` passed `node --check`.
- Main Next.js TS/TSX source files passed TypeScript **transpilation syntax** checks, including `MissionV3.tsx`, `RoleGate.tsx`, `api.ts`, `bridge.ts`, and route files. **This is not a full typecheck or Next.js build.**
- Offline Chromium DOM rendering of the standalone preview at 1440x900, 1024x900, and 390x844 checked all seven internal pages for document-level horizontal overflow and JavaScript exceptions; none were found. Dataset/history tables intentionally scroll horizontally within their panel on small screens.
- Separate interaction regression at 1440x900 and 390x844 checked role selection, mission detail tabs, crew selection, **0% noise waveform**, evaluation and history; both passed. The browser test used payloads obtained from the running FastAPI test instance and injected them into Chromium because the managed Chromium policy blocks navigating to local URLs.
- Actual FastAPI HTTP responses were tested separately with direct client requests and FastAPI TestClient.

## Not verified in this environment

- Full Next.js `npm install`, `npm run typecheck`, `npm run build`, or browser rendering of the Next.js application: the npm registry was unavailable (`EAI_AGAIN`) and the package dependencies were not present.
- Browser-to-FastAPI network requests from a real Next.js tab: local URL navigation is blocked by the managed Chromium policy, so the browser interaction tests exercised the standalone DOM with API-derived mocked responses.
- Supabase, RBAC/RLS, TimeShield, astronaut clinical accuracy, spacecraft data feeds and live performance budgets.

## On your Windows machine - final acceptance gate

1. Run `run_preview_windows.bat`; verify `http://127.0.0.1:8000/api/health` and `/docs`.
2. Run `run_next_windows.bat`; open `http://127.0.0.1:3000`.
3. In `frontend`, run `npm run typecheck` and `npm run build`. Do not treat v3.1 as production-build verified until both pass.
4. Check 1440px desktop, 1024px tablet, 390px phone, and a narrow height viewport. Test drawer open/close, astronaut role persistence across Signal Lab/history, user selection, and tabs.
5. Signal Lab: test 0% and 80% Gaussian noise with backend online. Verify original waveform at 0% is visible and that changing noise clears stale output.
6. Disconnect backend: show explicitly labeled offline demo for bundled BIDMC only; uploaded recording should not fake an analysis result. Reconnect and rerun.
7. Verify API invalid CSV gives a visible validation error, not a prepared fixture. Test upload -> select -> analyze, evaluation, history.
8. Confirm browser console has no errors and measure end-to-end frontend-to-backend latency on the target machine.

**Release label: STABILIZED PROTOTYPE (conditional).** Backend and standalone UI are test-verified; final Next.js build and real browser E2E testing remain required. This is not clinical software.

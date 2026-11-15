# SignalTrust frontend/backend contract and expansion notes

## Current split

- `frontend/lib/types.ts` defines the TypeScript consumer models and `MissionService` interface.
- `frontend/lib/api.ts` is the single transport adapter used by the Next.js components.
- `backend/api.py` preserves existing PPG processing endpoints.
- `backend/demo_routes.py` provides **synthetic** mission, crew, metrics, trends and notices. It does not modify signal-processing algorithms.
- `standalone/app.js` is a zero-build browser integration preview that uses identical HTTP paths. It is not the source of truth for future UI expansion.

## Current API map

| Method | Path | Frontend use | Source |
|---|---|---|---|
| GET | `/api/health` | Backend status | Real backend feature flags |
| GET | `/api/demo/mission` | Mission header | Synthetic |
| GET | `/api/demo/overview` | Admin summary cards | Synthetic |
| GET | `/api/demo/crew` | Crew table / role filter | Synthetic |
| GET | `/api/demo/health?crew_id=` | Astronaut metrics | Synthetic |
| GET | `/api/demo/trends?metric=&crew_id=` | Mission chart | Synthetic |
| GET | `/api/demo/alerts?crew_id=` | Monitoring notices | Synthetic |
| GET | `/api/demo/settings` | Capability defaults | Synthetic |
| GET | `/api/datasets` | Dataset selector and management | Real available recording metadata |
| GET | `/api/datasets/{recording_id}` | Recording metadata | Real |
| POST | `/api/recordings/upload` | CSV import | Real, ephemeral |
| POST | `/api/analyses` | PPG processing | Real signal-processing code |
| GET | `/api/analyses/history` | Analysis history | Real, ephemeral |
| GET | `/api/analyses/{analysis_id}` | Analysis details | Real, ephemeral |
| POST | `/api/evaluations` | Controlled noise sweep | Real signal-processing code |

The Next.js frontend should never calculate the SQI or physiological estimates itself. Scientific chart components render backend data. The backend should never own the page layout. DB and auth are not implied by client-side role simulation.

## Example analysis call

```json
{"recording_id":"bidmc_01","start_s":0,"duration_s":10,"noise_percent":35,"noise_seed":42}
```

Response contains `analysis_id`, `window`, `quality`, `measurements`, `decision`, `waveform`, `processing`, `warnings`, and `processing_ms` as described in `API_CONTRACTS.md`.

## Extending health indicators without breaking the frontend

A metric result has `key`, `label`, `value`, `unit`, `trend`, `status`, `type`, `quality`, and `source`. A new UI indicator should preserve those concepts and identify the observation source. Future realistic health measurements may need `observed_at`, `source_device_id`, `method`, `confidence`, and a distinct clinical-interpretation authority; these are **proposals** and not existing API fields.

Examples:

- SpO₂ — needs sensor context, signal quality and reference limitations; not currently estimated from BIDMC by this app.
- Radiation — measured instrument telemetry and personal astronaut dosimetry are different quantities. Keep dose units/position/provenance separate.
- Sleep / workload — need actual relevant data and validated definitions; currently synthetic card values.
- Bone / immune indicators — placeholders, not simulated medical test results.
- TimeShield — proposed event-time vs arrival-time adapter, clock integrity, freshness metadata and offline synchronization; not currently connected.

### Accuracy and latency principles

1. Preserve input quality metadata through the pipeline, never silently impute missing samples as healthy readings.
2. Keep physically distinct signals and units separate (PPG vs ECG; instrument absorbed dose rate vs equivalent dose rate).
3. Use controlled ablation: raw threshold, filtered-only, quality-aware; independently track retention and error, not just accepted-window performance.
4. Cap waveform samples sent to the browser (current backend compact series default max 1,500), and request detailed windows only when needed.
5. Keep heavy Plotly libraries loaded client-side and separate from summary chart rendering.
6. Measure **end-to-end** latency separately from processing time before making speed claims. Report environment, data size, p50/p95, and method.
7. When moving to true streaming, revisit filter causality, phase delay and buffer/window length. Do not reuse offline `filtfilt` semantics as an online result.
8. Avoid polling all endpoints for every interaction; the frontend fetches initial overview once and updates narrowly for selected filters.

### Security before production

Current endpoints have **zero authorization**. Never deploy this as a real crew record system. Use verified JWT validation in FastAPI, Supabase Auth for identity, server-issued role claims and RLS policies for user/mission isolation. UI role switches are demonstrations only; never trust a client-provided crew ID as authorization.

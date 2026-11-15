# Architecture boundaries before TimeShield

The goal of v3.1 is to make the current prototype a stable baseline for a later event-time/provenance module. No TimeShield service, database, sequence, transaction outbox, or socket relay is implemented in this release.

## Current tested module boundaries

```text
Next.js page / standalone browser preview
   -> typed frontend service (`frontend/lib/api.ts`, `frontend/lib/bridge.ts`)
      -> FastAPI routes (`backend/api.py` + `backend/demo_routes.py`)
         -> Python analysis adapter (`backend/analysis.py`)
            -> existing team preprocessing, SQI and heart-rate functions
```

- The real analysis endpoint works only on PPG (`PLETH`) in the MVP. ECG remains unimplemented.
- Quality, pulse-rate, decision, waveform, and `processing_ms` come from the existing Python adapter.
- Crew, SpO2, sleep, radiation context, and mission readiness are synthetic demo data; no real telemetry.
- Recording upload and history are process-memory only, with no authentication or persistence.
- Frontend role switching and selected crew are **presentation state**, not real RBAC.
- A rejected or invalid API request must remain an error, not quietly become a synthetic result.
- The frontend never performs filtering in the browser. Signal-trace arrays come from the backend or a labeled precomputed fixture.

## Latency and accuracy boundaries

- `processing_ms` is backend compute time, not network round-trip or UI draw time.
- Plot arrays are capped/decimated by the current backend; later zoom workflows might need segment endpoints, but do not implement until needed.
- Filtering cannot guarantee clinical accuracy; compare original / filtered estimates and valid-observation retention against a documented reference before claims.
- Do not cache personal physiological assessments without provenance/freshness semantics once real telemetry exists.

## Proposed TimeShield integration point (NOT APPROVED CODE)

Keep **measurement quality** and **telemetry freshness** separate. When the team approves TimeShield, extend the typed API DTO with an optional `provenance` object, for example:

```json
{
  "event_time": "2026-11-15T10:00:10Z",
  "arrival_time": "2026-11-15T10:00:11Z",
  "sensor_id": "demo-sensor-01",
  "source_event_id": "event-000123",
  "revision": 2,
  "reconciliation_state": "RECONCILED",
  "freshness_state": "FRESH",
  "evidence_count": 15
}
```

This is a **proposal**, not an existing FastAPI contract and not a real physiological observation. Prior to integration, separately verify: source clock trust, stable event IDs, idempotent persistence, replay-window state, commit-safe outbox cursor and reconnect catch-up. PostgreSQL notifications are wake-up hints, not durable storage. Do not claim that TimeShield eliminates Earth-to-space communication delay.

**Next gate:** complete the Next.js production build and real browser API flow on an environment with npm installed, then review TimeShield's implementation independently before wiring it into SignalTrust.

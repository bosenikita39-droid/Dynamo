# SignalTrust local API — stable prototype contracts

Base URL: `http://127.0.0.1:8000`. Existing frontend runs separately on port 5173 (Vite) or 3000 (Next.js), with API base URL `http://127.0.0.1:8000`. No frontend API key required for this local demo.

## Endpoint map

| Method | Path | Function |
| --- | --- | --- |
| GET | `/api/health` | Backend status and explicit feature flags |
| GET | `/api/datasets` | List sample and uploaded recordings |
| GET | `/api/datasets/{id}` | Single recording metadata |
| POST | `/api/recordings/upload` | Multipart CSV file upload (`file`) |
| POST | `/api/analyses` | Run quality-aware PPG analysis |
| GET | `/api/analyses/history` | Last 30 in-process summaries |
| GET | `/api/analyses/{id}` | Full previous analysis result |
| POST | `/api/evaluations` | 0/25/60% synthetic noise sweep |
| GET | `/docs` | OpenAPI documentation |

All endpoints are **unauthenticated local-only**. This is not production security. **The repository includes a separate frontend and a standalone preview; the Python analysis module is unchanged.**

## Analysis request

```json
{
  "recording_id": "bidmc_01",
  "start_s": 0,
  "duration_s": 10,
  "noise_percent": 65,
  "noise_seed": 42
}
```

Rules: `recording_id` must exist; start >= 0; duration 5–60 seconds; noise 0–100; seed non-negative 32-bit integer. The selected interval needs at least 3 seconds of actual samples. The current Signal Lab UI requests a fixed 10-second window; the API itself supports the documented duration range.

## Analysis response (shape; values illustrate a tested run)

```json
{
  "analysis_id": "analysis_123456abcdef",
  "recording_id": "bidmc_01",
  "source": "Bundled public terrestrial clinical recording",
  "channel": "PLETH",
  "window": {"start_s": 0, "end_s": 9.992, "samples": 1250, "sampling_rate_hz": 125, "timestamp_gaps": 0},
  "processing": {"method": "Existing team Hampel + Butterworth bandpass (0.5-5 Hz)", "noise_percent": 65, "noise_seed": 42, "filter_mode": "zero-phase offline; NOT streaming real-time"},
  "quality": {"score": 85.0, "status": "HIGH", "missing_percent": 0, "spike_percent": 0, "flatline_percent": 8, "peak_count": 15, "plausible_intervals_percent": 100, "amplitude_quality_percent": 90},
  "measurements": {"raw_pulse_bpm": 153.06, "filtered_pulse_bpm": 92.59, "reference_pulse_bpm": 93.75, "bpm_difference": -60.47, "reference_type": "unmodified-signal algorithm estimate (NOT clinical ground truth)"},
  "decision": {"status": "NO_ALERT", "conventional": "ALERT", "filtered_only": "NO_ALERT", "explanation": "Quality checks passed; no demonstration threshold was crossed.", "thresholds_bpm": {"low": 50, "high": 120, "type": "illustrative, not clinical"}},
  "waveform": {"time_s": [0, 0.008], "raw": [0.4, 0.5], "filtered": [0.01, 0.02], "reference": [0.41, 0.49], "decimation_step": 1},
  "peaks": {"raw_s": [0.2], "filtered_s": [0.22]},
  "warnings": ["Research demonstration only: thresholds and SQI are not medically validated."],
  "processing_ms": 40.0
}
```

Waveform and peak arrays above are **abbreviated placeholders** to document structure. API responses include the actual backend-computed arrays. `filtered` may be `null` when the selected window contains missing samples or gaps, and a `DEFER` decision does not mean normal health. `reference_pulse_bpm` only appears under synthetic-noise injection and is itself an algorithmic estimate, not independent ECG or clinical truth.

## Evaluation request

```json
{"recording_id":"bidmc_01","start_s":0,"duration_s":10,"noise_seed":42}
```

Response: `{ "recording_id": "...", "experiment": "...", "seed": 42, "results": [ ... ], "limitations": [ ... ] }`, containing three result objects (noise 0,25,60) with `raw_bpm`, `filtered_bpm`, `reference_estimate_bpm`, `quality_score`, `quality_status`, `conventional`, `filtered_only`, `signaltrust`, and `processing_ms`.

## CSV format

```csv
Time [s],PLETH
0.000,0.42
0.008,0.43
0.016,0.44
```

CSV must contain 375–200,000 rows; time and PPG, and inferred sample frequency 20–1000 Hz. Stable cadence is required; genuine nonfinite PPG measurements are **not** interpolated. For short data, choose an interval with at least three seconds of samples.

## Errors

- HTTP `404` — unknown recording or analysis.
- HTTP `422` — invalid CSV, unsupported sample rate, malformed/invalid request, missing interval.
- CSV/parser errors: `{ "error": { "code": "INVALID_RECORDING", "message": "Human-readable problem" } }`.
- Pydantic/FastAPI validation errors: standard `{"detail":[...]}`.

## Future integration

The included Next.js frontend already calls these endpoints through `frontend/lib/api.ts`, and `frontend/lib/bridge.ts` only substitutes fixtures for network outages. Supabase Auth/RLS are **not** connected; when added, introduce a verified auth token boundary and user-scoped resource identifiers. Do not assume the current in-memory history is private or durable.

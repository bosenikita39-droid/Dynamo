"""Deterministic synthetic mission fixtures for the frontend integration prototype.

Not astronaut medical data, NASA telemetry, clinical thresholds or a live mission.
No authentication, persistence, or real patient data in this demo router.
"""
from __future__ import annotations
import math
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix='/api/demo', tags=['Demo mission data (synthetic only)'])

CREW = [
    {'id': 'crew-01', 'name': 'Crew Member 01', 'position': 'Mission Commander', 'status': 'NOMINAL', 'quality': 98, 'avatar': '01'},
    {'id': 'crew-02', 'name': 'Crew Member 02', 'position': 'Flight Engineer', 'status': 'REVIEW', 'quality': 84, 'avatar': '02'},
    {'id': 'crew-03', 'name': 'Crew Member 03', 'position': 'Mission Specialist', 'status': 'NOMINAL', 'quality': 96, 'avatar': '03'},
    {'id': 'crew-04', 'name': 'Crew Member 04', 'position': 'Biomedical Officer', 'status': 'NOMINAL', 'quality': 94, 'avatar': '04'},
    {'id': 'crew-05', 'name': 'Crew Member 05', 'position': 'Payload Specialist', 'status': 'REVIEW', 'quality': 79, 'avatar': '05'},
    {'id': 'crew-06', 'name': 'Crew Member 06', 'position': 'Mission Specialist', 'status': 'NOMINAL', 'quality': 97, 'avatar': '06'},
]

METRICS = [
    {'key': 'heart_rate', 'label': 'Heart Rate', 'value': 76, 'unit': 'BPM', 'trend': -2.4, 'status': 'NOMINAL', 'type': 'PHYSIOLOGICAL', 'quality': 96},
    {'key': 'spo2', 'label': 'Blood Oxygen', 'value': 98, 'unit': '%', 'trend': 0.4, 'status': 'NOMINAL', 'type': 'PHYSIOLOGICAL', 'quality': 94},
    {'key': 'respiration', 'label': 'Respiration', 'value': 16, 'unit': '/min', 'trend': -0.9, 'status': 'NOMINAL', 'type': 'PHYSIOLOGICAL', 'quality': 95},
    {'key': 'sleep', 'label': 'Sleep Duration', 'value': 7.2, 'unit': 'hrs', 'trend': 0.7, 'status': 'NOMINAL', 'type': 'BEHAVIORAL', 'quality': 91},
    {'key': 'radiation', 'label': 'Instrument Dose Rate', 'value': 3.2, 'unit': 'µGy/h', 'trend': 1.3, 'status': 'CONTEXT', 'type': 'ENVIRONMENT', 'quality': 87},
    {'key': 'stress', 'label': 'Stress Index', 'value': 28, 'unit': '/100', 'trend': -3.1, 'status': 'DEMO_ONLY', 'type': 'SIMULATED_INDEX', 'quality': 74},
    {'key': 'bone', 'label': 'Bone Health', 'value': None, 'unit': None, 'trend': None, 'status': 'NOT_CONNECTED', 'type': 'PLACEHOLDER', 'quality': None},
    {'key': 'immune', 'label': 'Immune Markers', 'value': None, 'unit': None, 'trend': None, 'status': 'NOT_CONNECTED', 'type': 'PLACEHOLDER', 'quality': None},
]

ALERTS = [
    {'id': 'notice-001', 'crew_id': 'crew-02', 'title': 'Measurement quality needs review', 'category': 'QUALITY', 'severity': 'AMBER', 'time': '09:42', 'message': 'Synthetic signal window had reduced confidence. Review or repeat the measurement.', 'status': 'OPEN'},
    {'id': 'notice-002', 'crew_id': 'crew-05', 'title': 'Intermittent SpO₂ readings', 'category': 'QUALITY', 'severity': 'AMBER', 'time': '08:17', 'message': 'Demo observation series contains missing values. No clinical interpretation is possible.', 'status': 'OPEN'},
    {'id': 'notice-003', 'crew_id': 'crew-01', 'title': 'Environmental telemetry note', 'category': 'ENVIRONMENT', 'severity': 'INFO', 'time': '07:31', 'message': 'Instrument radiation data is environmental context, not an individual astronaut dose.', 'status': 'ACKNOWLEDGED'},
]

def require_crew(crew_id: str) -> dict:
    match = next((c for c in CREW if c['id'] == crew_id), None)
    if not match:
        raise HTTPException(status_code=404, detail='Demo crew member not found')
    return match

@router.get('/mission')
def mission():
    return {
        'id': 'AURORA-01', 'name': 'AURORA / Research Mission', 'mode': 'DEMO',
        'orbit': 'Low Earth Orbit · Simulation', 'flight_day': 142,
        'crew_count': len(CREW), 'sensor_channels': 6, 'mission_status': 'SIMULATED',
        'data_disclaimer': 'All mission, crew, physiological and radiation context on this endpoint is synthetic demo data. No live NASA telemetry.',
    }

@router.get('/crew')
def crew():
    return {'items': CREW, 'data_source': 'SYNTHETIC_DEMO'}

@router.get('/health')
def health(crew_id: str = Query('crew-01')):
    require_crew(crew_id)
    shift = int(crew_id[-2:]) - 1
    metrics = []
    for row in METRICS:
        metric = dict(row)
        if isinstance(metric['value'], (int, float)) and shift:
            if metric['key'] in ('heart_rate', 'respiration', 'stress'):
                metric['value'] += (shift % 3) * 2
            if metric['key'] == 'spo2':
                metric['value'] = max(94, metric['value'] - (shift % 3))
        metric['source'] = 'SIMULATED'
        metrics.append(metric)
    return {'crew_id': crew_id, 'metrics': metrics, 'data_source': 'SYNTHETIC_DEMO', 'clinical_validation': False}

@router.get('/trends')
def trends(metric: str = Query('heart_rate'), crew_id: str = Query('crew-01'), points: int = Query(36, ge=6, le=180)):
    require_crew(crew_id)
    match = next((m for m in METRICS if m['key'] == metric), None)
    if match is None or match['value'] is None:
        raise HTTPException(status_code=404, detail='Metric has no simulated trend')
    scale = {'heart_rate': 8, 'spo2': 1.3, 'respiration': 2.4, 'sleep': 0.7,
             'radiation': 0.9, 'stress': 8}.get(metric, 2)
    base = float(match['value'])
    series = [{'t': i, 'value': round(base + math.sin(i * 0.43 + .3) * scale * .52 +
               math.cos(i * 0.14) * scale * .36 + math.sin(i * 1.71) * scale * .10, 2)} for i in range(points)]
    return {'metric': metric, 'crew_id': crew_id, 'unit': match['unit'], 'series': series,
            'data_source': 'SYNTHETIC_DEMO', 'period': 'illustrative sequence, not a time-based medical record'}

@router.get('/alerts')
def alerts(crew_id: str | None = None):
    if crew_id:
        require_crew(crew_id)
    rows = [a for a in ALERTS if not crew_id or a['crew_id'] == crew_id]
    return {'items': rows, 'data_source': 'SYNTHETIC_DEMO'}

@router.get('/overview')
def overview():
    return {'crew_total': 6, 'crew_nominal': 4, 'crew_review': 2, 'data_reliability_percent': 94.6,
            'active_monitoring_channels': 6, 'open_notices': 2, 'analysis_runs_today': 24,
            'data_source': 'SYNTHETIC_DEMO'}

@router.get('/settings')
def settings():
    return {'theme': 'mission-dark', 'demo_alert_threshold_bpm': 120,
            'demo_quality_threshold_percent': 75, 'signal_source': 'PPG',
            'retention': 'No persistent storage in local prototype',
            'data_source': 'SYNTHETIC_DEMO', 'read_only': True}

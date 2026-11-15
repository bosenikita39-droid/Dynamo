"""RadLab CSV adapter: historical instrument telemetry, NEVER individual dose.

Keeps supplied cumulative/gap scripts under docs/source_radlab for provenance.
No live API calls or assumed personal shielding geometry.
"""
from __future__ import annotations
import csv
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from collections import defaultdict
from math import sqrt, isfinite

CSV_PATH = Path(__file__).parent / 'sample_data' / 'radlab_iss_dostel_2022.csv'
# A configurable analysis assumption. Not a validated DosTel universal cadence.
DEFAULT_MAX_INTERVAL_SECONDS = 300
SOURCE = 'USER_SUPPLIED_NASA_RADLAB_CSV'
SOURCE_URL = 'https://visualization.osdr.nasa.gov/radlab/gui/data-api/'

def _time(value: str) -> datetime:
    dt = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # Explicit assumption for source CSV naive timestamps
    return dt.astimezone(timezone.utc)

@lru_cache(maxsize=1)
def load_records():
    data = defaultdict(list)
    invalid = 0
    conflicts = 0
    seen = {}
    with CSV_PATH.open(newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            try:
                identifier = (row.get('instrument_id') or '').strip()
                stamp = _time(row['timestamp'])
                rate = float(row['absorbed_dose_rate'])
                if not identifier or not isfinite(rate) or rate < 0:
                    raise ValueError('invalid instrument or dose rate')
                key = (identifier, stamp)
                if key in seen:
                    if seen[key] != rate:
                        conflicts += 1
                    continue  # conservative: do not integrate ambiguous duplicated timestamp
                seen[key] = rate
                data[identifier].append({'timestamp':stamp, 'rate':rate})
            except (ValueError, TypeError, KeyError, OverflowError):
                invalid += 1
    for rows in data.values():
        rows.sort(key=lambda r:r['timestamp'])
    return dict(data), invalid, conflicts

def analyze_instrument(instrument: str, max_interval_seconds: int = DEFAULT_MAX_INTERVAL_SECONDS):
    if not 1 <= max_interval_seconds <= 3600:
        raise ValueError('max_interval_seconds must be within 1..3600')
    records, invalid, conflicts = load_records()
    if instrument not in records:
        raise KeyError(instrument)
    rows = records[instrument]
    valid_time = 0.0
    covered_dose = 0.0
    excluded = 0
    gaps = []
    intervals = []
    for one,two in zip(rows,rows[1:]):
        dt = (two['timestamp']-one['timestamp']).total_seconds()
        if dt <= 0 or dt > max_interval_seconds:
            excluded += 1
            gaps.append({'start':one['timestamp'].isoformat(),'end':two['timestamp'].isoformat(),'seconds':dt,'reason':'MISSING_INTERVAL' if dt>max_interval_seconds else 'INVALID_INTERVAL'})
            continue
        dose_ugy = (one['rate']+two['rate'])/2 * dt/3600  # µGy/h * hours -> µGy
        valid_time += dt
        covered_dose += dose_ugy
        intervals.append({'start':one['timestamp'].isoformat(),'end':two['timestamp'].isoformat(),'seconds':dt,'absorbed_dose_ugy':round(dose_ugy,8)})
    span=(rows[-1]['timestamp']-rows[0]['timestamp']).total_seconds() if len(rows)>1 else 0.0
    coverage=round(valid_time/span*100,2) if span>0 else 0.0
    sample = [{'timestamp':row['timestamp'].isoformat(),'absorbed_dose_rate_ugy_h':round(row['rate'],6)} for row in rows]
    return {
        'instrument_id':instrument,'spacecraft':'ISS','data_source':SOURCE,'source_url':SOURCE_URL,
        'sample_origin':'User-provided export described as NASA RadLab; not independently re-fetched',
        'data_class':'HISTORICAL_SPACECRAFT_INSTRUMENT_TELEMETRY',
        'is_live':False,'is_personal_dose':False,
        'unit_rate':'µGy/h','unit_accumulated':'µGy',
        'first_timestamp':rows[0]['timestamp'].isoformat(),'last_timestamp':rows[-1]['timestamp'].isoformat(),
        'readings':len(rows),'observed_span_seconds':span,'covered_seconds':valid_time,
        'uncovered_seconds':round(span-valid_time,3),'coverage_percent':coverage,
        'valid_intervals':len(intervals),'excluded_intervals':excluded,
        'covered_interval_absorbed_dose_ugy':round(covered_dose,6),
        'full_period_dose_ugy':round(covered_dose,6) if span>0 and not excluded else None,
        'full_period_dose_status':'ESTIMATED_WITH_ASSUMPTIONS' if span>0 and not excluded else 'UNDETERMINED_MISSING_COVERAGE',
        'uncertainty_ugy':None,'uncertainty_status':'NOT_AVAILABLE_NO_CALIBRATION_UNCERTAINTY',
        'max_interval_seconds':max_interval_seconds,'invalid_rows':invalid,'conflicting_timestamp_rows':conflicts,
        'gap_intervals':gaps, 'series':sample,
        'disclaimer':'Environmental instrument readings, NOT an astronaut personal dose, organ dose, medical risk, or live monitoring. Missing intervals are not treated as zero. Trapezoid integration assumes linear rate between accepted observations.'
    }

def summary(max_interval_seconds: int = DEFAULT_MAX_INTERVAL_SECONDS):
    data,invalid,conflicts = load_records()
    return {
        'data_source':SOURCE,'source_url':SOURCE_URL,'is_live':False,
        'description':'Historical ISS DosTel instrument sample supplied by team (2022). No NASA API key or live connection.',
        'units':{'absorbed_dose_rate':'µGy/h','covered_interval_dose':'µGy'},
        'instruments':[
            {k:v for k,v in analyze_instrument(i,max_interval_seconds).items() if k!='series'}
            for i in sorted(data)
        ],
        'invalid_rows':invalid,'conflicts':conflicts,
        'disclaimer':'Instrument absorbed dose is not the personal dose absorbed by an astronaut.'
    }

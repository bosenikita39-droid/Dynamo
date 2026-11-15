"""Scientific-boundary, deterministic ordering, and UI contract regression checks."""
from datetime import datetime,timedelta,timezone
from fastapi.testclient import TestClient
from api import app
from radiation_service import analyze_instrument,load_records
from timeshield_service import process,make_event,ANCHOR

client=TestClient(app)

def test_radiation_dataset_instrument_provenance_and_units():
    r=client.get('/api/radiation/summary')
    assert r.status_code==200,r.text
    result=r.json()
    assert result['is_live'] is False
    assert result['data_source']=='USER_SUPPLIED_NASA_RADLAB_CSV'
    assert {x['instrument_id'] for x in result['instruments']}=={'DosTel1','DosTel2'}
    assert all('dose' in x['disclaimer'].lower() for x in result['instruments'])
    assert sum(x['readings'] for x in result['instruments'])==182
    for ins in result['instruments']:
        assert ins['coverage_percent']<=100
        assert ins['covered_interval_absorbed_dose_ugy']>=0
        assert ins['uncertainty_ugy'] is None
        assert ins['data_class']=='HISTORICAL_SPACECRAFT_INSTRUMENT_TELEMETRY'

def test_radiation_interval_math_and_conservation():
    x=analyze_instrument('DosTel1',300)
    rows=load_records()[0]['DosTel1']
    expected=sum((a['rate']+b['rate'])/2*(b['timestamp']-a['timestamp']).total_seconds()/3600
      for a,b in zip(rows,rows[1:]) if 0<(b['timestamp']-a['timestamp']).total_seconds()<=300)
    assert abs(x['covered_interval_absorbed_dose_ugy']-expected)<1e-5
    assert abs(x['covered_seconds']+x['uncovered_seconds']-x['observed_span_seconds'])<1e-7
    assert x['first_timestamp'].startswith('2022')
    assert x['is_personal_dose'] is False

def test_radiation_gap_excludes_intervals_not_invents_zero_or_personal_dose():
    strict=client.get('/api/radiation/instruments/DosTel1',params={'max_interval_seconds':1}).json()
    assert strict['covered_interval_absorbed_dose_ugy']==0
    assert strict['coverage_percent']==0
    assert strict['full_period_dose_ugy'] is None
    assert strict['uncovered_seconds']==strict['observed_span_seconds']
    assert strict['excluded_intervals']>0
    assert client.get('/api/radiation/instruments/UNKNOWN').status_code==404
    assert client.get('/api/radiation/summary?max_interval_seconds=0').status_code==422
    assert client.get('/api/radiation/summary?max_interval_seconds=3601').status_code==422

def test_event_time_late_reconciles_without_overwriting_newer_value():
    r=client.post('/api/timeshield/replay',json={'scenario':'late'})
    assert r.status_code==200,r.text
    x=r.json()
    assert x['counts']['late_reconciled']==1
    assert [s['value_bpm'] for s in x['ordered_timeline']]==[72,76,125]
    assert x['arrival_trace'][-1]['outcome']=='HISTORICAL_RECONCILIATION'
    assert x['arrival_trace'][-1]['current_value_bpm']==125
    assert x['assessment']['value_bpm']==125
    assert x['assessment']['decision_is_clinical'] is False
    assert x['durable_outbox_enabled'] is False

def test_idempotent_duplicate_and_blackout_stale():
    d=client.post('/api/timeshield/replay',json={'scenario':'duplicate'}).json()
    assert d['counts']['received']==4
    assert d['counts']['accepted_unique']==3
    assert d['counts']['duplicates_ignored']==1
    assert d['counts']['conflicts_rejected']==0
    b=client.post('/api/timeshield/replay',json={'scenario':'blackout'}).json()
    assert b['assessment']['freshness']=='STALE'
    assert b['assessment']['event_age_seconds']==21
    assert b['assessment']['value_bpm']==125

def test_quality_cannot_be_declared_normal_from_unreliable_measurement():
    out=process([make_event('e1',0,1,130,.3,seq=1)],now=ANCHOR+timedelta(seconds=2))
    assert out['assessment']['decision']=='DEFER_INSUFFICIENT_QUALITY'

def test_source_id_conflict_and_invalid_future_event():
    a=make_event('same',0,2,72,seq=1)
    b=make_event('same',1,3,81,seq=1)
    result=process([a,b])
    assert result['counts']['conflicts_rejected']==1
    assert result['counts']['accepted_unique']==1
    future=make_event('future',20,1,72,seq=1)
    try:process([future]);assert False,'expected validation'
    except ValueError:pass

def test_replay_contract_consistent_with_frontend_and_old_endpoints():
    r=client.get('/api/timeshield/scenarios')
    assert r.status_code==200
    for scenario in r.json()['scenarios']:
        payload=client.post('/api/timeshield/replay',json={'scenario':scenario})
        assert payload.status_code==200,payload.text
        assert payload.json()['scenario']==scenario
    assert client.post('/api/timeshield/replay',json={'scenario':'unknown'}).status_code==422
    assert client.get('/api/health').status_code==200
    assert client.post('/api/analyses',json={'recording_id':'bidmc_01','start_s':0,'duration_s':10}).status_code==200

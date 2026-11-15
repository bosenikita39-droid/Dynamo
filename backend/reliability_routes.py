"""Isolated historical RadLab and deterministic TimeShield API module."""
from fastapi import APIRouter,HTTPException,Query
from radiation_service import load_records,analyze_instrument,summary
from timeshield_service import ReplayRequest,replay_scenario,scenarios

router=APIRouter(tags=['Radiation and event-time research'])

@router.get('/api/radiation/summary')
def radiation_summary(max_interval_seconds:int=Query(300,ge=1,le=3600)):
    return summary(max_interval_seconds)

@router.get('/api/radiation/instruments/{instrument_id}')
def radiation_instrument(instrument_id:str,max_interval_seconds:int=Query(300,ge=1,le=3600)):
    try:return analyze_instrument(instrument_id,max_interval_seconds)
    except KeyError:raise HTTPException(status_code=404,detail='Unknown sample instrument')

@router.get('/api/timeshield/scenarios')
def time_scenarios():
    return {'scenarios':list(scenarios()),'data_source':'SYNTHETIC_DEMO','persistence_enabled':False}

@router.post('/api/timeshield/replay')
def time_replay(body:ReplayRequest):
    try:return replay_scenario(body.scenario)
    except KeyError:raise HTTPException(status_code=422,detail='Unknown demo replay scenario')

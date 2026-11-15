"""Pure deterministic event-time reconciliation teaching prototype.

No persistence, signatures, transactional outbox, LISTEN/NOTIFY, sockets or reliable
cross-process delivery claims. All events are synthetic, never clinical telemetry.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from json import dumps
from math import isfinite
from pydantic import BaseModel, Field

class Event(BaseModel):
    event_id: str = Field(min_length=1,max_length=90)
    sensor_id: str = Field(min_length=1,max_length=90)
    sequence: int = Field(ge=0)
    event_time: datetime
    arrival_time: datetime
    value: float = Field(ge=0,le=300)
    quality: float = Field(ge=0,le=1)

class ReplayRequest(BaseModel):
    scenario: str = Field(default='late')

# Fixed synthetic times are intentionally not linked to wall clock.
ANCHOR = datetime(2026,11,14,12,0,0,tzinfo=timezone.utc)
def make_event(eid: str, event_s: int, arrival_s: int, value: int,quality:float=0.95, seq:int=0)->Event:
    return Event(event_id=eid,sensor_id='synthetic-ppg-01',sequence=seq,event_time=ANCHOR+timedelta(seconds=event_s),arrival_time=ANCHOR+timedelta(seconds=arrival_s),value=value,quality=quality)

def scenarios():
    return {
        'ordered':[make_event('e1',0,1,72,seq=1),make_event('e2',5,6,76,seq=2),make_event('e3',10,11,125,seq=3)],
        'late':[make_event('e1',0,1,72,seq=1),make_event('e3',10,11,125,seq=3),make_event('e2',5,15,76,seq=2)],
        'duplicate':[make_event('e1',0,1,72,seq=1),make_event('e2',5,6,76,seq=2),make_event('e2',5,7,76,seq=2),make_event('e3',10,11,125,seq=3)],
        'blackout':[make_event('e1',0,1,72,seq=1),make_event('e2',5,29,76,seq=2),make_event('e3',10,30,125,seq=3)],
        'quality':[make_event('e1',0,1,72,seq=1),make_event('e2',5,6,130,quality=.30,seq=2),make_event('e3',10,11,76,seq=3)]
    }

def _utc(d):
    if d.tzinfo is None:raise ValueError('event and arrival timestamps must contain a timezone')
    return d.astimezone(timezone.utc)

def process(events:list[Event],now:datetime|None=None)->dict:
    """Replay in arrival order. Stored event-time records are canonical truth.

    Dedup uses source event_id, conflicting same-ID payload is rejected; revisions
    do not change event-time high water mark. Explicit demo alert threshold only.
    """
    if len(events)>500:raise ValueError('Too many events in demo replay (max 500)')
    if not events:raise ValueError('Replay requires at least one event')
    current_time=_utc(now) if now else max(_utc(e.arrival_time) for e in events)+timedelta(seconds=1)
    unique={}
    arrivals=[]
    late_count=0; duplicate_count=0; conflict_count=0
    highwater=None
    previous_current=None
    for event in sorted(events,key=lambda e:(_utc(e.arrival_time),e.event_id)):
        t=_utc(event.event_time); a=_utc(event.arrival_time)
        if t>a:raise ValueError('Event cannot be captured after its arrival in this simulation')
        key=(event.sensor_id,event.event_id)
        data=(event.sequence,t.isoformat(),event.value,event.quality)
        if key in unique:
            if unique[key][1] != data:
                conflict_count+=1; outcome='CONFLICT_REJECTED'
            else:
                duplicate_count+=1;outcome='DUPLICATE_IGNORED'
            arrivals.append({'event_id':event.event_id,'event_time':t.isoformat(),'arrival_time':a.isoformat(),'value_bpm':event.value,'outcome':outcome,'current_value_bpm':previous_current})
            continue
        late=highwater is not None and t<highwater
        if late:late_count+=1
        highwater=max(t,highwater) if highwater else t
        unique[key]=(event,data)
        ordered=sorted((x[0] for x in unique.values()),key=lambda x:(_utc(x.event_time),x.sequence,x.event_id))
        latest=ordered[-1]
        previous_current=latest.value
        arrivals.append({'event_id':event.event_id,'event_time':t.isoformat(),'arrival_time':a.isoformat(),'value_bpm':event.value,'outcome':'HISTORICAL_RECONCILIATION' if late else 'IN_ORDER','current_value_bpm':previous_current})
    canonical=sorted((x[0] for x in unique.values()),key=lambda x:(_utc(x.event_time),x.sequence,x.event_id))
    latest=canonical[-1]
    age=(current_time-_utc(latest.event_time)).total_seconds()
    freshness='FRESH' if age<=20 else 'STALE'  # illustrative local demo threshold, NOT clinical
    if latest.quality<0.75:decision='DEFER_INSUFFICIENT_QUALITY'
    else:decision='DEMO_THRESHOLD_EXCEEDED' if latest.value>=115 else 'NO_DEMO_THRESHOLD_ALERT'
    return {
        'scenario_data_source':'SYNTHETIC_DEMO','transport':'IN_MEMORY_DETERMINISTIC_REPLAY',
        'is_live':False,'persistence_enabled':False,'durable_outbox_enabled':False,
        'ordered_timeline':[{'event_id':x.event_id,'sensor_id':x.sensor_id,'sequence':x.sequence,'event_time':_utc(x.event_time).isoformat(),'value_bpm':x.value,'quality':x.quality} for x in canonical],
        'arrival_trace':arrivals,
        'counts':{'received':len(events),'accepted_unique':len(canonical),'duplicates_ignored':duplicate_count,'conflicts_rejected':conflict_count,'late_reconciled':late_count},
        'assessment':{'event_time':_utc(latest.event_time).isoformat(),'as_of':current_time.isoformat(),
            'event_age_seconds':round(age,3),'freshness':freshness,'reconciliation_occurred':late_count>0,
            'value_bpm':latest.value,'quality':latest.quality,'evidence_count':len(canonical),'decision':decision,
            'decision_is_clinical':False},
        'limitations':'Historical event-time order and deduplication only. Thresholds (115 BPM, 0.75 quality, 20 s freshness) are teaching examples, not medical criteria. Does NOT provide signature verification, ACID transactions, a durable outbox, sockets, cross-process exactly-once or low-link-latency guarantees.'
    }

def replay_scenario(scenario:str)->dict:
    options=scenarios()
    if scenario not in options:raise KeyError(scenario)
    result=process(options[scenario],now=ANCHOR+timedelta(seconds=31))
    result['scenario']=scenario
    return result

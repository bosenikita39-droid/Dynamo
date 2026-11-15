from io import BytesIO
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from api import app

client=TestClient(app)


def make_csv(*,invalid=False,missing=False):
    fs=125
    t=np.arange(1250)/fs
    if invalid:
        t[9]=t[8]-1
    ppg=0.5+0.2*np.sin(2*np.pi*1.25*t)
    if missing:
        ppg[100:115]=np.nan
    return pd.DataFrame({'Time [s]':t, 'PLETH':ppg}).to_csv(index=False).encode()


def test_health_and_public_sample():
    r=client.get('/api/health')
    assert r.status_code==200
    assert r.json()['auth_enabled'] is False
    d=client.get('/api/datasets')
    assert d.status_code==200
    assert any(x['id']=='bidmc_01' for x in d.json()['recordings'])
    assert client.get('/api/datasets/bidmc_01').json()['sampling_rate_hz']==125
    assert client.get('/api/datasets/does_not_exist').status_code==404


def test_zero_build_preview_is_served():
    response = client.get('/')
    assert response.status_code == 200
    assert 'SIGNAL' in response.text and 'app.js' in response.text
    assert client.get('/assets/app.js').status_code==404
    assert client.get('/docs').status_code==200


def test_dev_cors_for_existing_frontend_ports():
    for origin in ('http://localhost:5173', 'http://localhost:3000'):
        r=client.options('/api/analyses', headers={
            'Origin': origin,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type',
        })
        assert r.status_code==200
        assert r.headers['access-control-allow-origin']==origin


def test_analysis_roundtrip_and_history():
    body={'recording_id':'bidmc_01','start_s':0,'duration_s':10,'noise_percent':70,'noise_seed':42}
    r=client.post('/api/analyses',json=body)
    assert r.status_code==200,r.text
    a=r.json()
    assert a['window']['samples']==1250
    assert a['quality']['status'] in ['HIGH','MEDIUM','LOW']
    assert a['processing_ms'] >= 0
    assert a['measurements']['filtered_pulse_bpm'] is not None
    assert a['waveform']['filtered'] is not None
    assert a['waveform']['reference'] is not None
    assert a['processing']['noise_seed']==42
    same=client.post('/api/analyses',json=body).json()
    assert a['waveform']['raw']==same['waveform']['raw']
    assert client.get('/api/analyses/'+a['analysis_id']).status_code==200
    assert client.get('/api/analyses/history').json()['analyses'][0]['analysis_id']==same['analysis_id']
    assert client.get('/api/analyses/bad_id').status_code==404


def test_analysis_rejects_invalid_requests():
    assert client.post('/api/analyses',json={'recording_id':'not_found'}).status_code==404
    assert client.post('/api/analyses',json={'recording_id':'bidmc_01','duration_s':200}).status_code==422
    r=client.post('/api/analyses',json={'recording_id':'bidmc_01','start_s':1000})
    assert r.status_code==422 and r.json()['error']['code']=='INVALID_RECORDING'


def test_csv_upload_and_analysis():
    r=client.post('/api/recordings/upload',files={'file':('my_test.csv',make_csv(),'text/csv')})
    assert r.status_code==201,r.text
    ident=r.json()['id']
    analysis=client.post('/api/analyses',json={'recording_id':ident,'start_s':0,'duration_s':10})
    assert analysis.status_code==200,analysis.text
    assert analysis.json()['window']['samples']==1250
    assert analysis.json()['decision']['status'] in ('NO_ALERT','ISSUE','QUALIFY','DEFER')


def test_upload_rejects_malformed_inputs():
    assert client.post('/api/recordings/upload',files={'file':('bad.txt',b'bad','text/plain')}).status_code==422
    assert client.post('/api/recordings/upload',files={'file':('bad.csv',b'nonsense\n1\n2','text/csv')}).status_code==422
    assert client.post('/api/recordings/upload',files={'file':('bad_time.csv',make_csv(invalid=True),'text/csv')}).status_code==422
    r=client.post('/api/recordings/upload',files={'file':('big.csv',b'X'*(8*1024*1024+1),'text/csv')})
    assert r.status_code==422


def test_missing_values_never_become_valid_health_measurements():
    upload=client.post('/api/recordings/upload',files={'file':('missing.csv',make_csv(missing=True),'text/csv')})
    assert upload.status_code==201,upload.text
    a=client.post('/api/analyses',json={'recording_id':upload.json()['id'],'start_s':0,'duration_s':10}).json()
    assert a['decision']['status']=='DEFER'
    assert a['measurements']['filtered_pulse_bpm'] is None
    assert a['waveform']['filtered'] is None
    assert a['quality']['missing_percent']>0


def test_evaluation_api():
    r=client.post('/api/evaluations',json={'recording_id':'bidmc_01','start_s':0,'duration_s':10})
    assert r.status_code==200,r.text
    result=r.json()
    assert [x['noise_percent'] for x in result['results']]==[0,25,60]
    assert 'not independent' in result['limitations'][0].lower()


def test_demo_mission_endpoints_are_explicitly_synthetic():
    mission = client.get('/api/demo/mission')
    assert mission.status_code == 200
    assert mission.json()['mode'] == 'DEMO'
    assert 'synthetic' in mission.json()['data_disclaimer'].lower()
    overview = client.get('/api/demo/overview').json()
    assert overview['data_source'] == 'SYNTHETIC_DEMO'
    crew = client.get('/api/demo/crew').json()['items']
    assert len(crew) == 6
    health = client.get('/api/demo/health?crew_id=crew-01').json()
    assert len(health['metrics']) == 8
    assert all(m['source']=='SIMULATED' for m in health['metrics'])
    assert client.get('/api/demo/health?crew_id=invalid').status_code == 404
    assert client.get('/api/demo/trends?metric=bone&crew_id=crew-01').status_code == 404


def test_preview_html_javascript_and_styles_are_reachable():
    assert client.get('/styles.css').status_code == 200
    assert client.get('/app.js').status_code == 200

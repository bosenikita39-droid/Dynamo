"""Regression tests for the contracts consumed by the Mission Control UI.

No TimeShield, auth or database assumptions are introduced here.
"""
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)


def test_zero_noise_has_observable_original_ppg_even_without_reference_copy():
    analysis = client.post('/api/analyses', json={
        'recording_id': 'bidmc_01', 'start_s': 0, 'duration_s': 10,
        'noise_percent': 0, 'noise_seed': 42,
    })
    assert analysis.status_code == 200, analysis.text
    wave = analysis.json()['waveform']
    assert wave['reference'] is None  # optional unmodified noise-experiment reference
    assert wave['raw'] and len(wave['raw']) == len(wave['time_s'])
    # The UI must use reference ?? raw for the Original Waveform.
    assert all(isinstance(v, (int, float)) for v in wave['raw'][:10])


def test_demo_health_routes_remain_explicitly_synthetic_and_scoped_by_requested_id():
    for ident in ('crew-01', 'crew-02'):
        response = client.get('/api/demo/health', params={'crew_id': ident})
        assert response.status_code == 200
        data = response.json()
        assert data['crew_id'] == ident
        assert data['data_source'] == 'SYNTHETIC_DEMO'
        assert all(m['source'] == 'SIMULATED' for m in data['metrics'])
    assert client.get('/api/demo/alerts?crew_id=crew-02').status_code == 200
    assert client.get('/api/demo/alerts?crew_id=bad').status_code == 404


def test_trend_and_settings_contracts_for_future_health_indicators():
    for metric in ('heart_rate','spo2','respiration','radiation','sleep','stress'):
        response=client.get('/api/demo/trends',params={'metric':metric,'crew_id':'crew-01'})
        assert response.status_code==200, (metric,response.text)
        body=response.json()
        assert body['data_source']=='SYNTHETIC_DEMO'
        assert len(body['series']) >= 6
    settings=client.get('/api/demo/settings').json()
    assert settings['read_only'] is True
    assert settings['data_source']=='SYNTHETIC_DEMO'


def test_frontend_origin_and_error_contract():
    cors=client.options('/api/analyses',headers={
        'Origin':'http://127.0.0.1:3000',
        'Access-Control-Request-Method':'POST',
        'Access-Control-Request-Headers':'content-type',
    })
    assert cors.status_code==200
    assert cors.headers['access-control-allow-origin']=='http://127.0.0.1:3000'
    unknown=client.post('/api/analyses',json={'recording_id':'not-present'})
    assert unknown.status_code==404
    assert unknown.json()['detail']=='Recording not found'

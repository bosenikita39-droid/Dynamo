"""Local hackathon API. No authentication or persistent storage in this phase."""
from collections import deque
from threading import Lock
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from data_store import RecordingStore, DatasetError, MAX_CSV_BYTES
from models import AnalyzeRequest, EvaluationRequest
from analysis import analyze, evaluate
from demo_routes import router as demo_router
from reliability_routes import router as reliability_router
from pathlib import Path
from fastapi.staticfiles import StaticFiles

app=FastAPI(title='SignalTrust Prototype API',version='0.1.0',description='Research-only offline PPG analysis API')
# Restricted local development origins; do not use wildcard credentials.
app.add_middleware(CORSMiddleware,allow_origins=[
    'http://localhost:5173', 'http://127.0.0.1:5173',
    'http://localhost:3000', 'http://127.0.0.1:3000',
], allow_credentials=False, allow_methods=['GET','POST'], allow_headers=['Content-Type'])
store=RecordingStore()
history=deque(maxlen=30)
history_lock=Lock()


@app.exception_handler(DatasetError)
async def dataset_error(request: Request, exc: DatasetError):
    return JSONResponse(status_code=422,content={'error':{'code':'INVALID_RECORDING','message':str(exc)}})


@app.get('/api/health')
def health():
    return {'status':'ok','mode':'local-in-memory','auth_enabled':False,
            'storage_enabled':False,'signal':'PPG','clinical_validation':False}


@app.get('/api/datasets')
def datasets():
    return {'recordings':store.list()}


@app.get('/api/datasets/{recording_id}')
def dataset(recording_id: str):
    rec=store.get(recording_id)
    if rec is None:raise HTTPException(status_code=404,detail='Recording not found')
    return rec.meta()


@app.post('/api/recordings/upload',status_code=201)
async def upload(file: UploadFile = File(...)):
    if not (file.filename or '').lower().endswith('.csv'):
        raise DatasetError('Only .csv files are supported in this prototype.')
    content=await file.read(MAX_CSV_BYTES+1)
    if len(content)>MAX_CSV_BYTES:raise DatasetError('CSV exceeds 8 MiB size limit.')
    return store.upload(content,file.filename or 'uploaded.csv').meta()


@app.post('/api/analyses')
def run_analysis(body: AnalyzeRequest):
    rec=store.get(body.recording_id)
    if rec is None:raise HTTPException(status_code=404,detail='Recording not found')
    result=analyze(rec,body.start_s,body.duration_s,body.noise_percent,body.noise_seed)
    with history_lock:
        history.appendleft(result)
    return result


@app.get('/api/analyses/history')
def list_history():
    with history_lock:
        return {'analyses':[{'analysis_id':x['analysis_id'], 'recording_id':x['recording_id'],
                             'window':x['window'],'quality':x['quality'],
                             'decision':x['decision'],'processing_ms':x['processing_ms']}
                            for x in history]}


@app.get('/api/analyses/{analysis_id}')
def analysis_detail(analysis_id: str):
    with history_lock:
        result=next((x for x in history if x['analysis_id']==analysis_id),None)
    if result is None:raise HTTPException(status_code=404,detail='Analysis not found')
    return result


@app.post('/api/evaluations')
def run_evaluation(body: EvaluationRequest):
    rec=store.get(body.recording_id)
    if rec is None:raise HTTPException(status_code=404,detail='Recording not found')
    return evaluate(rec,body.start_s,body.duration_s,body.noise_seed)

# The backend deliberately does not serve or replace the user's frontend.
# Run the original application separately on port 5173 (Vite) or 3000 (Next.js).


# Synthetic mission endpoints are separate from the real PPG processing routes.
app.include_router(demo_router)
app.include_router(reliability_router)

# Standalone zero-build browser preview. Next.js frontend runs separately when installed.
_preview_dir = Path(__file__).resolve().parent.parent / 'standalone'
if (_preview_dir / 'index.html').exists():
    app.mount('/', StaticFiles(directory=str(_preview_dir), html=True), name='standalone-preview')

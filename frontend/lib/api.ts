import type {MissionService,Recording,Analysis,Evaluation,HistoryItem,Metric,Crew,Alert,Mission,Overview,RadiationSummary,RadiationInstrument,TimeReplay} from './types';
const BASE=(process.env.NEXT_PUBLIC_API_BASE_URL||'http://127.0.0.1:8000').replace(/\/$/,'');
export class ApiError extends Error {constructor(public status:number,public code:string,message:string){super(message);this.name='ApiError';}}
export async function request<T>(path:string,options?:RequestInit):Promise<T>{
  let response:Response;
  try {response=await fetch(BASE+path,{...options,cache:'no-store'});} catch {throw new ApiError(0,'OFFLINE','Could not reach the SignalTrust API. Start FastAPI on port 8000.');}
  const payload=await response.json().catch(()=>null);
  if(!response.ok){const msg=payload?.error?.message||payload?.detail?.map?.((x:{msg:string})=>x.msg).join('; ')||payload?.detail||`HTTP ${response.status}`;
    throw new ApiError(response.status,payload?.error?.code||'REQUEST_FAILED',typeof msg==='string'?msg:'Request failed');}
  return payload as T;
}
const get=<T>(path:string)=>request<T>(path);
const post=<T>(path:string,data:unknown)=>request<T>(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
// Transport boundary: change this adapter when the real FastAPI contract evolves.
// Pages only consume MissionService. No auth token or Supabase calls are simulated as secure.
export const api:MissionService={
  mission:()=>get<Mission>('/api/demo/mission'),overview:()=>get<Overview>('/api/demo/overview'),
  crew:async()=>(await get<{items:Crew[]}>('/api/demo/crew')).items,
  health:async(crewId)=>(await get<{metrics:Metric[]}>(`/api/demo/health?crew_id=${encodeURIComponent(crewId)}`)).metrics,
  alerts:async(crewId)=>(await get<{items:Alert[]}>(`/api/demo/alerts${crewId?'?crew_id='+encodeURIComponent(crewId):''}`)).items,
  trends:async(metric,crewId)=>(await get<{series:{t:number;value:number}[]}>(`/api/demo/trends?metric=${encodeURIComponent(metric)}&crew_id=${encodeURIComponent(crewId)}`)).series,
  recordings:async()=>(await get<{recordings:Recording[]}>('/api/datasets')).recordings,
  upload:async(file)=>{const form=new FormData();form.append('file',file);return request<Recording>('/api/recordings/upload',{method:'POST',body:form});},
  analyze:(args)=>post<Analysis>('/api/analyses',args),
  evaluation:(args)=>post<Evaluation>('/api/evaluations',args),
  history:async()=>(await get<{analyses:HistoryItem[]}>('/api/analyses/history')).analyses,
  analysis:(id)=>get<Analysis>('/api/analyses/'+encodeURIComponent(id)),
};
export const API_BASE=BASE;

// TimeShield / radiation are isolated, versioned additions; existing processing APIs stay intact.
export const reliabilityApi={
 radiationSummary:(maxGap=300)=>get<RadiationSummary>(`/api/radiation/summary?max_interval_seconds=${maxGap}`),
 radiationInstrument:(id:string,maxGap=300)=>get<RadiationInstrument>(`/api/radiation/instruments/${encodeURIComponent(id)}?max_interval_seconds=${maxGap}`),
 timeScenarios:()=>get<{scenarios:string[];data_source:string}>('/api/timeshield/scenarios'),
 timeReplay:(scenario:string)=>post<TimeReplay>('/api/timeshield/replay',{scenario}),
};

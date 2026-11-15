import {api,ApiError} from './api';
import type {Mission,Overview,Crew,Metric,Alert,Recording,Analysis,Evaluation,HistoryItem} from './types';

// API-first service boundary. The existing FastAPI endpoints are unchanged.
// Any fallback data are precomputed, distinctly labelled demo fixtures.
export type FeedSource='API / BIDMC'|'OFFLINE DEMO';
async function fixture<T>(path:string):Promise<T>{const r=await fetch('/mock/'+path+'.json',{cache:'no-store'});if(!r.ok)throw new Error('Demo fixture unavailable: '+path);return await r.json() as T;}
async function fallback<T>(call:()=>Promise<T>,path:string,transform?:(x:unknown)=>T):Promise<{data:T;source:FeedSource}>{
 try{return {data:await call(),source:'API / BIDMC'}}catch(error){
  if(!(error instanceof ApiError) || error.status!==0)throw error;
  const raw=await fixture<unknown>(path);
  return {data:transform?transform(raw):raw as T,source:'OFFLINE DEMO'};
 }
}
export const bridge={
 mission:()=>fallback<Mission>(api.mission,'mission'),
 overview:()=>fallback<Overview>(api.overview,'overview'),
 crew:()=>fallback<Crew[]>(api.crew,'crew',x=>(x as {items:Crew[]}).items),
 health:(id:string)=>fallback<Metric[]>(()=>api.health(id),'health_'+id,x=>(x as {metrics:Metric[]}).metrics),
 alerts:()=>fallback<Alert[]>(()=>api.alerts(),'alerts',x=>(x as {items:Alert[]}).items),
 datasets:()=>fallback<Recording[]>(api.recordings,'datasets',x=>(x as {recordings:Recording[]}).recordings),
 analysis:(noise:number,recording_id='bidmc_01')=>recording_id==='bidmc_01'?fallback<Analysis>(()=>api.analyze({recording_id,start_s:0,duration_s:10,noise_percent:noise,noise_seed:42}), 'analysis_'+[0,35,80].reduce((prev,n)=>Math.abs(n-noise)<Math.abs(prev-noise)?n:prev,0)):api.analyze({recording_id,start_s:0,duration_s:10,noise_percent:noise,noise_seed:42}).then(data=>({data,source:'API / BIDMC' as const})),
 evaluation:()=>fallback<Evaluation>(()=>api.evaluation({recording_id:'bidmc_01',start_s:0,duration_s:10,noise_seed:42}),'evaluation'),
 history:async()=>{try{return {data:await api.history(),source:'API / BIDMC' as const}}catch(error){if(!(error instanceof ApiError) || error.status!==0)throw error;return {data:[] as HistoryItem[],source:'OFFLINE DEMO' as const}}},
 upload:api.upload,
};

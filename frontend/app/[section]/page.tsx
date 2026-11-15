import {notFound} from 'next/navigation';
import MissionApp from '@/components/MissionV3';
import {PageKey} from '@/lib/types';
const pages:PageKey[]=['admin','astronaut','signal-lab','datasets','evaluation','history','settings'];
export default async function SectionPage({params}:{params:Promise<{section:string}>}){
  const {section}=await params;
  if(!pages.includes(section as PageKey))notFound();
  return <MissionApp section={section as PageKey}/>;
}

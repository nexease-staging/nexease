"use client";
import {useQuery} from '@tanstack/react-query';
import {apiRequest} from '@/lib/api/client';
export default function WorkerStatus(){
 const q=useQuery({queryKey:['worker-health'],refetchInterval:60000,queryFn:async()=>(await apiRequest<{worker_active:boolean;pending:number;failed:number}>('/business/worker-health/')).data});
 if(!q.data?.pending)return null;
 return <div role="status" className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-950">{q.data.pending} email(s) waiting. {q.data.worker_active?'The worker is active; queued messages will be processed in order.':'No recent worker heartbeat. Ask the administrator to start the background worker for this environment.'} Do not resend a pending document. A connected mailbox alone does not process the queue.</div>
}

"use client";
import Link from 'next/link';
import {useQuery} from '@tanstack/react-query';
import {apiRequest} from '@/lib/api/client';
import {useAuth} from '@/features/auth/auth-context';
import {hasPermission} from '@/lib/authorization/permissions';
export default function EmployeePayables(){
 const {authentication}=useAuth();const allowed=hasPermission(authentication?.role.permissions??[],'payroll.read');
 const q=useQuery({queryKey:['employee-payables'],enabled:allowed,queryFn:async()=>(await apiRequest<{total:string;rows:{employee_id:string;name:string;month:string;net:string;paid:string;outstanding:string}[]}>('/business/employee-payables/')).data});
 if(!allowed)return null;
 return <section className="nx-panel"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-semibold">Employee salary payable</h2><Link href="/payroll" className="nx-button nx-secondary">Open payroll</Link></div><p className="my-3 text-sm text-slate-500">Approved payroll less recorded salary payments. Separate from supplier balances; attendance alone does not post a liability.</p>{q.error?<p role="alert">{q.error.message}</p>:q.isPending?<p>Loading salary balances…</p>:<><p className="my-4 text-2xl font-semibold">₹{q.data?.total??'0.00'}</p><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr>{['Employee','Month','Net salary','Paid','Balance'].map(x=><th className="p-3" key={x}>{x}</th>)}</tr></thead><tbody>{q.data?.rows.map(x=><tr key={x.employee_id+x.month}>{[x.name,x.month,x.net,x.paid,x.outstanding].map((v,i)=><td className="border-t p-3" key={i}>{v}</td>)}</tr>)}</tbody></table></div>{!q.data?.rows.length&&<p>No unpaid approved salaries.</p>}</>}</section>
}

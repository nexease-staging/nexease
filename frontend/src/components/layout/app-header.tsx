"use client";
import {useState,useEffect,useRef} from 'react';
import {useRouter} from 'next/navigation';
import Link from 'next/link';
import {Menu,UserRound,LogOut,CreditCard,Settings} from 'lucide-react';
import {useQuery} from '@tanstack/react-query';
import {useAuth} from '@/features/auth/auth-context';
import {getConfig} from '@/features/business/workspace';
import {hasPermission} from '@/lib/authorization/permissions';
import QuickCreate from '@/components/layout/quick-create';
import {CommandPaletteTrigger} from '@/components/layout/command-palette';
import NotificationMenu from '@/features/notifications/components/notification-menu';
import NexDialog from '@/components/nex-dialog';
import DeviceNotificationSettings from '@/components/mobile/device-notification-settings';
export default function AppHeader({onOpenMobile}:{onOpenMobile:()=>void}) {
 const router=useRouter();const {authentication,signOut}=useAuth();
 const config=useQuery({queryKey:['business-config'],queryFn:getConfig,enabled:!!authentication});
 const [open,setOpen]=useState(false),[profile,setProfile]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const box=useRef<HTMLDivElement>(null),trigger=useRef<HTMLButtonElement>(null);
 useEffect(()=>{const close=(e:PointerEvent)=>{if(!box.current?.contains(e.target as Node))setOpen(false)};const key=(e:KeyboardEvent)=>{if(e.key==='Escape'){setOpen(false);trigger.current?.focus()}};document.addEventListener('pointerdown',close);document.addEventListener('keydown',key);return()=>{document.removeEventListener('pointerdown',close);document.removeEventListener('keydown',key)}},[]);
 if(!authentication)return null;
 const {user,organization,role}=authentication;
 const initials=((user.first_name?.[0]||'')+(user.last_name?.[0]||'')).toUpperCase()||'U';
 async function logout(){setBusy(true);setError('');try{await signOut();router.replace('/login');router.refresh()}catch{setError('Could not confirm server sign-out. Please reconnect and try again.')}finally{setBusy(false)}}
 return <header className="nx-app-header sticky top-0 z-30 flex h-16 shrink-0 items-center gap-2 border-b border-slate-200 bg-white px-3 sm:px-6">
 <button type="button" aria-label="Open navigation" onClick={onOpenMobile} className="rounded-lg p-2 lg:hidden"><Menu size={21}/></button>
 <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{organization.name}</p><p className="truncate text-xs text-slate-500">{role.name}</p></div>
 <CommandPaletteTrigger/><QuickCreate variant="header"/><NotificationMenu/>
 <div ref={box} className="relative"><button ref={trigger} type="button" aria-label="Open account menu" aria-expanded={open} aria-controls="account-menu" onClick={()=>setOpen(!open)} className="flex size-10 items-center justify-center overflow-hidden rounded-full border border-emerald-200 bg-emerald-50 font-bold text-emerald-800">
 {config.data?.logo?<img src={config.data.logo} alt={organization.name+' logo'} className="h-full w-full object-contain"/>:initials}</button>
 {open&&<div id="account-menu" className="fixed right-3 top-[calc(4.5rem+env(safe-area-inset-top))] z-50 w-[min(20rem,calc(100vw-1.5rem))] max-h-[calc(100dvh-6rem)] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-3 shadow-xl sm:absolute sm:right-0 sm:top-12">
 <div className="border-b p-2"><p className="font-semibold">{user.full_name||`${user.first_name} ${user.last_name}`}</p><p className="break-all text-xs text-slate-500">{user.email}</p></div>
 <button className="nx-account-item" onClick={()=>{setOpen(false);setProfile(true)}}><UserRound size={18}/>My profile</button>
 <Link className="nx-account-item" href="/subscription" onClick={()=>setOpen(false)}><CreditCard size={18}/>Subscription & usage</Link>
 {hasPermission(role.permissions,'organizations.update')&&<Link className="nx-account-item" href="/settings/invoices" onClick={()=>setOpen(false)}><Settings size={18}/>Business logo & invoice settings</Link>}
 <button className="nx-account-item text-red-700" disabled={busy} onClick={()=>void logout()}><LogOut size={18}/>{busy?'Signing out…':'Log out'}</button>{error&&<p role="alert">{error}</p>}
 </div>}</div>
 {profile&&<NexDialog title="My profile" onClose={()=>setProfile(false)}><dl className="space-y-4"><div><dt>Name</dt><dd className="font-semibold">{user.full_name||`${user.first_name} ${user.last_name}`}</dd></div><div><dt>Email</dt><dd className="break-all">{user.email}</dd></div><div><dt>Organization</dt><dd>{organization.name}</dd></div><div><dt>Role</dt><dd>{role.name}</dd></div></dl><DeviceNotificationSettings/></NexDialog>}
 </header>;
}

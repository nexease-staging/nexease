"use client";
import {useEffect, useState, type ReactNode} from 'react';
import {Capacitor} from '@capacitor/core';
import {usePathname, useRouter} from 'next/navigation';
import {useAuth} from '@/features/auth/auth-context';
export default function NativeStart({children}:{children:ReactNode}) {
 const {status}=useAuth(); const path=usePathname(); const router=useRouter();
 const [native,setNative]=useState(false);
 useEffect(()=>setNative(Capacitor.isNativePlatform()),[]);
 const entry=native && (path==='/' || path==='/login' || path==='/login/');
 useEffect(()=>{if(!native&&path==='/'&&status==='authenticated'){router.replace('/dashboard');return;}if(!entry||status==='loading')return;if(status==='authenticated')router.replace('/home');else if(path==='/')router.replace('/login');},[entry,status,path,router,native]);
 if(entry&&(status==='loading'||status==='authenticated'||path==='/'))return <main className="nx-mobile-welcome">Opening your workspace…</main>;
 return children;
}

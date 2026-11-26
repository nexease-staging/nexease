"use client";
import { Suspense } from "react";
import EWayBills from '@/features/business/eway-bills';
export default function Page(){return <Suspense fallback={null}><EWayBills/></Suspense>;}

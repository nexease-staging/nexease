"use client";
import { Suspense } from "react";
import SalesDocuments from '@/features/business/sales-documents';
export default function Page(){return <Suspense fallback={null}><SalesDocuments mode="challan"/></Suspense>;}

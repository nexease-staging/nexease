"use client";
import { Suspense } from "react";
import EInvoices from "@/features/business/einvoices";
export default function Page() { return <Suspense fallback={null}><EInvoices /></Suspense>; }

"use client";
import {useState} from 'react';
import InvoiceDialog from '@/features/invoices/components/invoice-dialog';
export default function DirectInvoice(){const [open,setOpen]=useState(false);return <section className="nx-panel mb-6 flex items-center justify-between gap-4"><div><h2 className="text-xl font-semibold">Quick invoice</h2><p className="text-sm text-slate-500">Create a direct invoice with just a customer, items and tax treatment.</p></div><button className="nx-button" onClick={()=>setOpen(true)}>New direct invoice</button><InvoiceDialog open={open} onClose={()=>setOpen(false)} initialMode="direct"/></section>}

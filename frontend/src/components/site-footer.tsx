import Link from "next/link";
import {ArrowUpRight, Camera, Mail, MessageCircle} from "lucide-react";

export default function SiteFooter(){
 const columns=[
  {title:"Software",links:[["Billing & invoices","/#features"],["Inventory & purchases","/#features"],["Workforce & payroll","/#features"],["AI assistance","/#features"],["Plans & pricing","/pricing"]]},
  {title:"Services",links:[["Accounting & bookkeeping","/pricing"],["GST compliance support","/pricing"],["Payroll support","/pricing"],["Finance automation","/pricing"],["Request a quotation","/#contact"]]},
  {title:"Resources",links:[["Create your organisation","/signup"],["Log in","/login"],["Compliance calendar","/deadlines"],["Download price list","/NexEase_Pricing.pdf"],["Frequently asked questions","/#questions"]]},
 ];
 return <footer className="nx-site-footer">
  <div className="nx-footer-grid">
   <section><Link href="/" className="nx-footer-brand"><img src="/nexease-brand-icon.png" width="44" height="44" alt=""/>NexEase</Link><h2>Your finances. Simplified.</h2><p>Software, accounting, compliance support and automation for your everyday business.</p>
    <a href="https://wa.me/919209753378" target="_blank" rel="noopener noreferrer"><MessageCircle size={19}/>+91 92097 53378 <span className="sr-only">WhatsApp</span></a>
    <a href="mailto:nexease.contact@gmail.com"><Mail size={18}/>nexease.contact@gmail.com</a>
    <a href="https://www.instagram.com/nexease.ai/" target="_blank" rel="noopener noreferrer"><Camera size={18}/>@nexease.ai</a>
   </section>
   {columns.map(c=><section key={c.title}><h2>{c.title}</h2>{c.links.map(([label,href])=><Link key={label} href={href}>{label}<ArrowUpRight size={13}/></Link>)}</section>)}
  </div>
  <div className="nx-footer-wordmark" aria-hidden="true">Nex<span>Ease</span></div>
  <div className="nx-footer-bottom"><span>© {new Date().getFullYear()} NexEase. All rights reserved.</span><span>Professional services are scoped and quoted separately from software.</span></div>
 </footer>;
}

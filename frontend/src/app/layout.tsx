import PageHelp from "@/components/page-help";
import type { Metadata, Viewport } from "next";
import "./globals.css";
import Providers from "@/app/providers";
export const metadata:Metadata={title:"NexEase | Business Management",description:"Inventory, finance and workforce in one workspace."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en" suppressHydrationWarning><body><Providers>{children}<PageHelp/></Providers></body></html>;}

export const viewport:Viewport={width:"device-width",initialScale:1,viewportFit:"cover",themeColor:"#116957"};

import "@fontsource-variable/bricolage-grotesque";
import type { Metadata } from "next";
import Link from "next/link";
import { ArrowUpRight, Check, Globe } from "lucide-react";
import SiteFooter from "@/components/site-footer";
import SiteNav from "@/components/marketing/site-nav";
import { AndroidButton, ConnectorButton } from "@/components/marketing/download-buttons";
import { downloads } from "@/config/downloads";

export const metadata: Metadata = {
  title: "Download NexEase | Tally Connector and Android app",
  description: "Download the NexEase Tally Connector for Windows and the NexEase Android app to keep TallyPrime in sync with your phone.",
};

export default function DownloadPage() {
  return (
    <main className="nx-marketing nxw min-h-screen">
      <SiteNav />
      <section className="nxw-section nxw-dl-page">
        <div className="nxw-wrap">
          <h1 className="nxw-h1-sm">Download NexEase</h1>
          <p className="nxw-lead">Install the connector on the computer where Tally runs, and the app on your phone. Both use the same NexEase workspace.</p>
          <div className="nxw-dl-grid">
            <article className="nxw-dl-card">
              <h2>Tally Connector for Windows</h2>
              <p>Keeps TallyPrime and NexEase in sync every 30 seconds, both ways.</p>
              <ConnectorButton />
              <ol>
                <li>In TallyPrime: F1 → Settings → Connectivity → Client/Server configuration. Act as Both, ODBC Yes, port 9000. Restart Tally.</li>
                <li>Open the downloaded file. If Windows SmartScreen appears, choose More info → Run anyway.</li>
                <li>In NexEase, open Finance → Tally sync → Connect and copy the pairing code into the connector.</li>
                <li>Tick “Start with Windows” and keep Tally open with your company loaded.</li>
              </ol>
              <p className="nxw-fine">{downloads.connector.needs}. <a href={downloads.connector.checksum}>SHA-256 checksum</a></p>
            </article>
            <article className="nxw-dl-card">
              <h2>NexEase for Android</h2>
              <p>Dashboard, parties, Tally reports, billing and sharing on your phone.</p>
              <AndroidButton />
              <ol>
                <li>Open the downloaded .apk and allow installs from this source when Android asks.</li>
                <li>If an older NexEase app is installed, uninstall it first.</li>
                <li>Log in with your NexEase account.</li>
              </ol>
              <p className="nxw-fine">{downloads.android.needs}.</p>
            </article>
            <article className="nxw-dl-card nxw-dl-web">
              <h2><Globe size={20} />No download needed</h2>
              <p>NexEase also runs in any modern browser on a computer, iPhone or Android phone.</p>
              <ul className="nxw-ticks"><li><Check size={16} />Chrome, Edge, Safari and Firefox</li><li><Check size={16} />Add it to your home screen for an app-like icon</li></ul>
              <Link href="/login" className="nxw-text-cta">Open NexEase in the browser <ArrowUpRight size={17} /></Link>
            </article>
          </div>
        </div>
      </section>
      <SiteFooter />
    </main>
  );
}

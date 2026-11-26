import Link from "next/link";

export default function SiteNav() {
  return (
      <nav className="nxw-nav">
        <div className="nxw-wrap nxw-nav-row">
          <Link href="/" className="nxw-brand"><img src="/nexease-brand-icon.png" width="34" height="34" alt="" />NexEase</Link>
          <div className="nxw-nav-links">
            <Link href="/#tally">Tally connector</Link><Link href="/#features">Features</Link><Link href="/#mobile">Mobile app</Link><Link href="/pricing">Pricing</Link><Link href="/deadlines">Deadlines</Link><Link href="/#questions">Questions</Link>
          </div>
          <div className="nxw-nav-cta">
            <Link href="/login" className="nxw-login">Log in</Link>
            <Link href="/download" className="nxw-nav-dl">Download</Link>
            <Link href="/signup" className="nxw-nav-start">Start free</Link>
          </div>
        </div>
      </nav>
  );
}

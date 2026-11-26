/**
 * The hero picture: a TallyPrime day book on the left, NexEase on a phone on the right, and a
 * voucher travelling along the wire between them — the one thing NexEase does that matters
 * most to a Tally user. Pure HTML/CSS (one looping animation, off for reduced motion).
 * Demo data only.
 */
const daybook = [
  ["27-11-26", "Sales", "Krishna Hardware", "23,600.00"],
  ["27-11-26", "Receipt", "Patil Builders", "1,18,000.00"],
  ["26-11-26", "Purchase", "Tata Steel Distributors", "64,310.00"],
  ["26-11-26", "Payment", "Om Sai Transport", "8,500.00"],
  ["25-11-26", "Sales", "Metro Constructions", "41,890.00"],
];

export default function Relay() {
  return (
    <figure className="nxw-relay" aria-label="A sales voucher entered in TallyPrime appears in NexEase on a phone within seconds. Illustration with demo data.">
      <div className="nxw-tally" aria-hidden="true">
        <div className="nxw-tally-bar"><span>TallyPrime</span><span>Sharma Traders</span></div>
        <div className="nxw-tally-title">Day Book <small>1-Nov-26 to 27-Nov-26</small></div>
        <table>
          <thead><tr><th>Date</th><th>Vch type</th><th>Particulars</th><th>Amount</th></tr></thead>
          <tbody>
            {daybook.map(([d, t, p, a], i) => (
              <tr key={p} data-hot={i === 0 || undefined}><td>{d}</td><td>{t}</td><td>{p}</td><td>{a}</td></tr>
            ))}
          </tbody>
        </table>
        <div className="nxw-tally-foot">Connector on this PC · port 9000</div>
      </div>

      <div className="nxw-wire" aria-hidden="true">
        <span className="nxw-wire-line" />
        <span className="nxw-chip nxw-chip-out">Sales · ₹23,600</span>
        <span className="nxw-chip nxw-chip-in">Receipt · NexEase</span>
        <span className="nxw-wire-label">every 30 seconds, both ways</span>
      </div>

      <div className="nxw-phone" aria-hidden="true">
        <div className="nxw-phone-screen">
          <div className="nxw-phone-top"><b>Sharma Traders</b><span className="nxw-live">In sync · now</span></div>
          <div className="nxw-phone-kpis">
            <div><small>Receivable</small><b>₹3,68,072</b></div>
            <div><small>Sales this month</small><b>₹9,41,226</b></div>
          </div>
          <div className="nxw-phone-new">
            <small>Just in from Tally</small>
            <b>Sales · Krishna Hardware</b>
            <span>₹23,600.00</span>
          </div>
          <ul className="nxw-phone-list">
            <li><span>Patil Builders</span><b>₹1,18,000</b></li>
            <li><span>Metro Constructions</span><b>₹41,890</b></li>
          </ul>
          <div className="nxw-phone-share"><span>Share statement</span><span className="nxw-wa">WhatsApp</span></div>
        </div>
      </div>
      <figcaption>Illustration with demo data.</figcaption>
    </figure>
  );
}

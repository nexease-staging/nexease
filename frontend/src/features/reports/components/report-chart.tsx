"use client";

import { useEffect, useRef, useState } from "react";
import { formatValue, periodLabel, type ReportChart as Chart, type ReportColumn, type ReportRow } from "../api";

/* Categorical slots in fixed order (validated: CVD ΔE 12.6, normal 28.1 on white). The table
 * below every chart is the contrast relief for the lighter slots. */
const SERIES = ["#257de0", "#f47230", "#00b894"];
const compact = new Intl.NumberFormat("en-IN", { notation: "compact", maximumFractionDigits: 1 });

function niceMax(value: number) {
  if (value <= 0) return 1;
  const power = 10 ** Math.floor(Math.log10(value));
  const step = [1, 2, 2.5, 5, 10].find((s) => s * power >= value / 4) ?? 10;
  return Math.ceil(value / (step * power)) * step * power;
}

function useWidth() {
  const ref = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(640);
  useEffect(() => {
    const node = ref.current;
    if (!node || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(280, Math.round(entry.contentRect.width))));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

interface Tip { x: number; y: number; title: string; lines: Array<{ label: string; value: string; color: string }> }

export default function ReportChart({ chart, rows, columns, title }: { chart: Chart; rows: ReportRow[]; columns: ReportColumn[]; title: string }) {
  const [box, width] = useWidth();
  const [tip, setTip] = useState<Tip | null>(null);
  const data = chart.limit ? rows.slice(0, chart.limit) : rows;
  const label = (key: string) => columns.find((c) => c.key === key)?.label ?? key;
  const type = (key: string) => columns.find((c) => c.key === key)?.type ?? "money";
  const isPeriod = chart.x === "period";
  const series = chart.y.map((key, i) => ({ key, label: label(key), color: SERIES[i % SERIES.length] }));
  if (data.length < 2 && !isPeriod) return null;
  const tipFor = (row: ReportRow, x: number, y: number): Tip => ({
    x, y, title: isPeriod ? periodLabel(String(row[chart.x])) : String(row[chart.x]),
    lines: series.map((s) => ({ label: s.label, value: formatValue(row[s.key], type(s.key)), color: s.color })),
  });
  const legend = series.length > 1 ? (
    <div className="nxr-legend">{series.map((s) => <span key={s.key}><i style={{ background: s.color }} />{s.label}</span>)}</div>
  ) : null;

  // Ranked categories read best as horizontal bars with the name beside each bar.
  if (chart.type === "bar" && !isPeriod) {
    const s = series[0];
    const max = Math.max(...data.map((r) => Number(r[s.key]) || 0), 0) || 1;
    const rowH = 30, labelW = Math.min(220, Math.round(width * 0.36)), valueW = 92;
    const barW = Math.max(40, width - labelW - valueW - 16);
    const maxChars = Math.max(6, Math.floor((labelW - 10) / 6.4));
    const height = data.length * rowH;
    return (
      <figure className="nxr-chart" aria-label={`${title}: top ${data.length} by ${s.label.toLowerCase()}`}>
        <figcaption>Top {data.length} by {s.label.toLowerCase()}</figcaption>
        <div ref={box} className="relative" onMouseLeave={() => setTip(null)}>
          <svg width={width} height={height} role="img" aria-hidden="true">
            {data.map((row, i) => {
              const value = Math.max(Number(row[s.key]) || 0, 0);
              const w = Math.max(2, (value / max) * barW);
              const y = i * rowH + 6;
              const name = String(row[chart.x] || "—");
              return (
                <g key={i} onMouseMove={(e) => setTip(tipFor(row, e.nativeEvent.offsetX, y))}>
                  <title>{name}</title>
                  <rect x={0} y={i * rowH} width={width} height={rowH} fill="transparent" />
                  <text x={labelW - 8} y={y + 13} textAnchor="end" className="nxr-axis-label">{name.length > maxChars ? name.slice(0, maxChars - 1) + "…" : name}</text>
                  <path d={(() => { const r = Math.min(4, w / 2); return `M${labelW},${y} h${w - r} a${r},${r} 0 0 1 ${r},${r} v${18 - 2 * r} a${r},${r} 0 0 1 -${r},${r} h-${w - r} z`; })()} fill={s.color} />
                  <text x={labelW + w + 6} y={y + 13} className="nxr-value-label">₹{compact.format(Number(row[s.key]) || 0)}</text>
                </g>
              );
            })}
          </svg>
          {tip ? <Tooltip tip={tip} /> : null}
        </div>
      </figure>
    );
  }

  const height = 220, left = 56, right = 12, top = 12, bottom = 28;
  const innerW = width - left - right, innerH = height - top - bottom;
  const values = data.flatMap((r) => series.map((s) => Number(r[s.key]) || 0));
  const max = niceMax(Math.max(...values, 0));
  const min = Math.min(...values, 0) < 0 ? -niceMax(-Math.min(...values)) : 0;
  const y = (v: number) => top + innerH - ((v - min) / (max - min || 1)) * innerH;
  const band = innerW / Math.max(data.length, 1);
  const ticks = Array.from({ length: 5 }, (_, i) => min + ((max - min) / 4) * i);
  const every = Math.ceil(data.length / Math.max(1, Math.floor(innerW / 64)));

  return (
    <figure className="nxr-chart" aria-label={`${title} chart`}>
      {legend}
      <div ref={box} className="relative" onMouseLeave={() => setTip(null)}>
        <svg width={width} height={height} role="img" aria-hidden="true">
          {ticks.map((t) => (
            <g key={t}>
              <line x1={left} x2={width - right} y1={y(t)} y2={y(t)} className={t === 0 ? "nxr-baseline" : "nxr-grid"} />
              <text x={left - 6} y={y(t) + 4} textAnchor="end" className="nxr-axis-label">₹{compact.format(t)}</text>
            </g>
          ))}
          {data.map((row, i) => (i % every === 0 ? (
            <text key={i} x={left + band * i + band / 2} y={height - 8} textAnchor="middle" className="nxr-axis-label">{periodLabel(String(row[chart.x]))}</text>
          ) : null))}
          {chart.type === "line" ? (
            <>
              {series.map((s) => (
                <polyline key={s.key} fill="none" stroke={s.color} strokeWidth={2} strokeLinejoin="round"
                  points={data.map((row, i) => `${left + band * i + band / 2},${y(Number(row[s.key]) || 0)}`).join(" ")} />
              ))}
              {tip ? <line x1={tip.x} x2={tip.x} y1={top} y2={top + innerH} className="nxr-crosshair" /> : null}
              {data.map((row, i) => {
                const cx = left + band * i + band / 2;
                return (
                  <g key={i}>
                    {tip && Math.abs(tip.x - cx) < 1 ? series.map((s) => <circle key={s.key} cx={cx} cy={y(Number(row[s.key]) || 0)} r={4} fill={s.color} stroke="var(--nx-surface, #fff)" strokeWidth={2} />) : null}
                    <rect x={left + band * i} y={top} width={band} height={innerH} fill="transparent" onMouseMove={() => setTip(tipFor(row, cx, top))} />
                  </g>
                );
              })}
            </>
          ) : (
            data.map((row, i) => {
              const groupW = Math.min(band * 0.72, 18 * series.length + 2 * (series.length - 1));
              const barW = (groupW - 2 * (series.length - 1)) / series.length;
              const x0 = left + band * i + (band - groupW) / 2;
              return (
                <g key={i} onMouseMove={() => setTip(tipFor(row, left + band * i + band / 2, top))}>
                  <rect x={left + band * i} y={top} width={band} height={innerH} fill="transparent" />
                  {series.map((s, j) => {
                    const v = Number(row[s.key]) || 0;
                    const y0 = y(0), y1 = y(v), h = Math.abs(y0 - y1);
                    const x = x0 + j * (barW + 2);
                    if (h < 0.5) return null;
                    const r = Math.min(4, h, barW / 2);
                    // Rounded data end, square at the baseline.
                    const d = v >= 0
                      ? `M${x},${y0} v-${h - r} a${r},${r} 0 0 1 ${r},-${r} h${barW - 2 * r} a${r},${r} 0 0 1 ${r},${r} v${h - r} z`
                      : `M${x},${y0} v${h - r} a${r},${r} 0 0 0 ${r},${r} h${barW - 2 * r} a${r},${r} 0 0 0 ${r},-${r} v-${h - r} z`;
                    return <path key={s.key} d={d} fill={s.color} />;
                  })}
                </g>
              );
            })
          )}
        </svg>
        {tip ? <Tooltip tip={tip} /> : null}
      </div>
    </figure>
  );
}

function Tooltip({ tip }: { tip: Tip }) {
  return (
    <div className="nxr-tip" role="status" style={{ left: tip.x, top: tip.y }}>
      <strong>{tip.title}</strong>
      {tip.lines.map((l) => <span key={l.label}><i style={{ background: l.color }} />{l.label}<b>{l.value}</b></span>)}
    </div>
  );
}

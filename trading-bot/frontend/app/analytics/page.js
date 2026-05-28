"use client";
import React from "react";
import { useAuth } from "../components/AuthContext";
import { useGetStrategyPerformanceAnalyticsQuery } from "../lib/apiSlice";

const cardStyle = {
  background: "var(--bg-card)",
  border: "1px solid var(--border)",
  borderRadius: "14px",
  padding: "14px",
};

function fmt(v, d = 2) {
  const n = Number(v);
  return Number.isFinite(n) ? n.toFixed(d) : "—";
}

export default function AnalyticsPage() {
  const { user } = useAuth();
  const { data, isLoading, error } = useGetStrategyPerformanceAnalyticsQuery();
  if (!user) return null;

  const totals = data?.totals || {};
  const bySetup = data?.by_setup_type || {};
  const bySession = data?.by_session || {};
  const bySymbol = data?.by_symbol || {};

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <div style={cardStyle}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>Strategy Performance Analytics</h2>
        <p style={{ marginTop: 6, color: "var(--text-sub)", fontSize: 12 }}>
          Grouped analytics from closed trades: setup type, session, symbol, and suggested status.
        </p>
      </div>

      {isLoading ? <div style={cardStyle}>Loading analytics...</div> : null}
      {error ? <div style={{ ...cardStyle, color: "var(--loss)" }}>Failed to load analytics</div> : null}

      {!!data && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(120px,1fr))", gap: 10 }}>
            <MetricCard label="Total Trades" value={totals.total_trades} />
            <MetricCard label="Win Rate" value={`${fmt(totals.win_rate)}%`} />
            <MetricCard label="Avg RR" value={fmt(totals.average_rr, 3)} />
            <MetricCard label="Avg Profit" value={fmt(totals.average_profit, 2)} />
            <MetricCard label="Status" value={totals.suggested_status || "—"} />
          </div>

          <GroupSection title="By Setup Type" groups={bySetup} />
          <GroupSection title="By Session" groups={bySession} />
          <GroupSection title="By Symbol" groups={bySymbol} />
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div style={cardStyle}>
      <div style={{ color: "var(--text-sub)", fontSize: 11, textTransform: "uppercase" }}>{label}</div>
      <div style={{ marginTop: 4, fontSize: 18, fontWeight: 800 }}>{String(value ?? "—")}</div>
    </div>
  );
}

function GroupSection({ title, groups }) {
  const entries = Object.entries(groups || {});
  return (
    <div style={cardStyle}>
      <h3 style={{ marginTop: 0, marginBottom: 10, fontSize: 16, fontWeight: 800 }}>{title}</h3>
      <SimpleTable
        headers={["group", "trades", "win_rate", "avg_rr", "avg_profit", "max_dd", "status"]}
        rows={entries.map(([name, v]) => [
          name,
          v.total_trades,
          `${fmt(v.win_rate)}%`,
          fmt(v.average_rr, 3),
          fmt(v.average_profit, 2),
          fmt(v.max_drawdown, 4),
          v.suggested_status || "—",
        ])}
      />
    </div>
  );
}

function SimpleTable({ headers, rows }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {headers.map((h) => (
              <th key={h} style={thStyle}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr><td colSpan={headers.length} style={tdStyle}>No data</td></tr>
          ) : rows.map((r, i) => (
            <tr key={i}>
              {r.map((c, j) => <td key={j} style={tdStyle}>{String(c ?? "—")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const thStyle = { textAlign: "left", fontSize: 11, color: "var(--text-sub)", padding: "8px 6px", borderBottom: "1px solid var(--border)" };
const tdStyle = { fontSize: 12, padding: "8px 6px", borderBottom: "1px solid var(--divider)" };


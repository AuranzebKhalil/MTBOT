"use client";
import React, { useState } from "react";
import { useRunBacktestMutation, useGetBacktestStatusQuery, useGetBacktestResultsQuery } from "../lib/apiSlice";
import { useAuth } from "../components/AuthContext";
import { useBot } from "../components/BotContext";
 
const ALL_STRATEGIES = [
  { id: "SMC_VOLUME", name: "SMC Volume Flow" },
  { id: "SMC_SWEEP", name: "SMC Sweep Reclaim" },
  { id: "SMC_VSA", name: "SMC VSA Shift" },
  { id: "SMC_TREND", name: "SMC Continuation" },
  { id: "SMC_MSS", name: "SMC Market Structure Shift" },
  { id: "SMC_MITIGATION", name: "SMC Mitigation" },
  { id: "SMC_REVERSAL", name: "SMC Exhaustion Reversal" },
  { id: "SMC_BREAKER", name: "SMC Breaker" },
  { id: "HYBRID_REVERSION", name: "Hybrid Reversion" },
  { id: "HYBRID_SR", name: "Hybrid S/R" },
  { id: "HYBRID_BREAKOUT", name: "Hybrid Breakout" },
  { id: "HYBRID_MASTER", name: "Hybrid Master Switcher" },
  { id: "MAD_TREND_LOOP", name: "MAD Trend Loop" },
];

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

function toDisplay(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  try {
    return JSON.stringify(value);
  } catch {
    return "—";
  }
}

function extractErrorMessage(err) {
  if (err?.status === "PARSING_ERROR") {
    const raw = err?.data;
    if (typeof raw === "string" && raw.trim()) {
      const statusText = typeof err?.originalStatus === "number" ? `HTTP ${err.originalStatus}` : "server";
      return `${statusText} error: ${raw.trim()}`;
    }
    if (typeof err?.error === "string" && err.error.trim()) {
      if (err.error.toLowerCase().includes("not valid json")) {
        return "Server returned a non-JSON error response. Please check backend logs.";
      }
      return `Response parsing error: ${err.error}`;
    }
  }
  if (err?.status === "FETCH_ERROR" && typeof err?.error === "string") {
    return `Network error: ${err.error}`;
  }
  const detail = err?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => toDisplay(item.msg ?? item)).join(" | ");
  }
  return err?.message || "Backtest request failed.";
}

function toLocalInputValue(date) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

export default function BacktestPage() {
  const { user } = useAuth();
  const { isRunning } = useBot();
  const [runBacktest, { isLoading: isStarting }] = useRunBacktestMutation();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [diagnosticTab, setDiagnosticTab] = useState("funnel");
  const [showMore, setShowMore] = useState(false);
  
  const [activeJobId, setActiveJobId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const { data: backtestStatus } = useGetBacktestStatusQuery(undefined, {
    pollingInterval: (isProcessing || activeJobId) ? 1000 : 0,
    skip: !isProcessing && !activeJobId,
  });

  const { data: backtestResults, isFetching: isFetchingResults } = useGetBacktestResultsQuery(activeJobId, {
    skip: !activeJobId || backtestStatus?.progress < 100,
  });

  // Watch for backtest completion
  React.useEffect(() => {
    if (backtestStatus?.progress === 100 && backtestStatus?.job_id && isProcessing) {
      setActiveJobId(backtestStatus.job_id);
      setIsProcessing(false);
    }
  }, [backtestStatus, isProcessing]);

  // Handle results arrival
  React.useEffect(() => {
    if (backtestResults) {
      setResult(backtestResults);
      setActiveJobId(null);
    }
  }, [backtestResults]);

  const isLoading = isProcessing || (backtestStatus?.is_running && backtestStatus?.progress < 100) || isFetchingResults;

  const [form, setForm] = useState({
    symbol: "XAUUSD",
    date_from: "2026-04-29T08:58",
    date_to: "2026-05-09T08:58",
    risk_per_trade_pct: 0.01,
    max_trades_per_day: 5,
    max_daily_loss_pct: 0.05,
    max_consecutive_losses: 3,
    fixed_spread_points: 55,
    monte_carlo_enabled: false,
    mc_runs: 50,
    walk_forward_enabled: false,
    rolling_walk_forward_enabled: false,
    apply_recommended_filters: false,
    include_rejections: false,
    compare_gates: false,
    gate_profile: "balanced",
    ai_mode: "disabled",
    ai_threshold: 0.52,
    solo_strategy: "all",
    recommended_only: false,
    enabled_strategies: ["SMC_VOLUME", "SMC_TREND", "SMC_MSS", "HYBRID_REVERSION", "HYBRID_SR", "HYBRID_BREAKOUT", "HYBRID_MASTER", "MAD_TREND_LOOP"],
  });

  const onChange = (key, value) => setForm((p) => ({ ...p, [key]: value }));
  const isNotEnoughCandlesError = typeof error === "string" && error.toLowerCase().includes("not enough candles");

  const expandDateRange = (days) => {
    const fromDate = new Date(form.date_from);
    if (Number.isNaN(fromDate.getTime())) return;
    const expandedFrom = new Date(fromDate.getTime() - days * 24 * 60 * 60 * 1000);
    setForm((prev) => ({ ...prev, date_from: toLocalInputValue(expandedFrom) }));
    setError("");
  };

  const downloadCSV = () => {
    if (!result) return;
    const headers = ["time", "symbol", "strategy", "setup", "grade", "ai_conf", "structure", "entry", "exit", "rr", "pnl", "type", "stage", "rule", "reason"];
    const tradeRows = (result.trades || []).map((t) => [
      t.exit_time || t.entry_time, t.symbol, t.strategy, t.setup || "", t.grade || "",
      t.ai_conf ?? "", t.structure ?? "", t.entry_price || "", t.exit_price || "", t.rr || "", t.net_pnl || "", "TRADE", "", "", ""
    ]);
    const rejectRows = (result.rejected_signals || []).map((r) => [
      r.time, r.symbol, r.setup, r.grade, r.ai_conf, r.structure, "", "", "", "", "REJECTED", r.stage, r.rule, r.reason
    ]);
    const csvContent = [headers.join(","), ...tradeRows.map(r => r.join(",")), ...rejectRows.map(r => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `backtest_${form.symbol}.csv`;
    link.click();
  };

  const downloadDiagnostics = () => {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `diagnostics_${form.symbol}.json`;
    link.click();
  };

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    const fromDate = new Date(form.date_from);
    const toDate = new Date(form.date_to);
    if (fromDate >= toDate) {
      setError("date_from must be earlier than date_to.");
      return;
    }
    try {
      let enabled = form.solo_strategy === "all" ? form.enabled_strategies : [form.solo_strategy];
      if (form.recommended_only) {
        enabled = ["SMC_VOLUME", "SMC_SWEEP", "HYBRID_REVERSION", "SMC_TREND", "SMC_MSS"];
      }

      const payload = {
        ...form,
        date_from: fromDate.toISOString(),
        date_to: toDate.toISOString(),
        initial_balance: 10000,
        risk_per_trade: 0.01,
        enabled_strategies: enabled,
      };
      const res = await runBacktest(payload).unwrap();
      if (res.status === "started") {
        setIsProcessing(true);
      } else {
        setResult(res); // Fallback for synchronous results if backend supports both
      }
    } catch (err) {
      setResult(null);
      setError(extractErrorMessage(err));
    }
  };
  const summary = result?.summary || {};
  const trades = result?.trades || [];
  const rejected = result?.rejected_signals || [];
  const equity = result?.equity_curve || [];
  const debug = result?.debug_metrics || result?.diagnostics || {};

  if (!user) return null;

  return (
    <RenderGuard>
      <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <div style={cardStyle}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800 }}>Backtest</h2>
          <p style={{ marginTop: 6, color: "var(--text-sub)", fontSize: 12 }}>
            Runs backend backtest runner and shows strategy funnel, performance, and trade details.
          </p>
          
          <form onSubmit={submit} style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(140px,1fr))", gap: 10, marginTop: 16 }}>
            <div style={fieldWrapStyle}>
              <label style={fieldLabelStyle}>Symbol</label>
              <input value={form.symbol} onChange={(e) => onChange("symbol", e.target.value)} style={inputStyle} />
            </div>
            <div style={fieldWrapStyle}>
              <label style={fieldLabelStyle}>Date From (UTC)</label>
              <input type="datetime-local" required value={form.date_from} onChange={(e) => onChange("date_from", e.target.value)} style={inputStyle} />
            </div>
            <div style={fieldWrapStyle}>
              <label style={fieldLabelStyle}>Date To (UTC)</label>
              <input type="datetime-local" required value={form.date_to} onChange={(e) => onChange("date_to", e.target.value)} style={inputStyle} />
            </div>
            <div style={fieldWrapStyle}>
              <label style={fieldLabelStyle}>Options</label>
              <label style={{ ...inputStyle, display: "flex", alignItems: "center", gap: 8 }}>
                <input type="checkbox" checked={form.include_rejections} onChange={(e) => onChange("include_rejections", e.target.checked)} />
                Rejections
              </label>
            </div>

            <div style={{ display: "flex", gap: 10, gridColumn: "span 4", alignItems: "center", marginTop: 8 }}>
              <div style={{ display: "flex", gap: 12, alignItems: "center", flex: 1 }}>
                <button type="submit" disabled={isLoading || isRunning} style={{ ...btnStyle, flex: 1, background: "var(--accent)", color: "#000", border: "none" }}>
                  {isLoading ? `Running (${backtestStatus?.progress ?? 0}%)` : isRunning ? "Stop Bot To Run Backtest" : "Run Backtest"}
                </button>
                <button 
                  type="button" 
                  onClick={() => {
                    const newState = !form.recommended_only;
                    onChange("recommended_only", newState);
                    if (newState) onChange("solo_strategy", "all");
                  }} 
                  style={{ 
                    ...btnStyle, width: "auto", padding: "0 20px", 
                    background: form.recommended_only ? "var(--win)" : "rgba(255,255,255,0.05)",
                    color: form.recommended_only ? "black" : "white",
                    border: form.recommended_only ? "none" : "1px solid var(--border)",
                    fontSize: 12, fontWeight: 700
                  }}
                >
                  {form.recommended_only ? "★ Recommended ON" : "Run Recommended"}
                </button>
              </div>

              <div style={{ position: "relative" }}>
                <button type="button" onClick={() => setShowMore(!showMore)} style={{ ...btnStyle, background: "rgba(255,255,255,0.05)", width: 120 }}>
                  More {showMore ? "▴" : "▾"}
                </button>
                {showMore && (
                  <div style={dropdownStyle}>
                    <div style={fieldWrapStyle}>
                      <label style={fieldLabelStyle}>Gate Profile</label>
                      <select value={form.gate_profile} onChange={(e) => onChange("gate_profile", e.target.value)} style={inputStyle}>
                        <option value="strict" style={optionStyle}>Strict (Live Proof)</option>
                        <option value="balanced" style={optionStyle}>Balanced (Research)</option>
                        <option value="research" style={optionStyle}>Research (Diagnostic)</option>
                      </select>
                    </div>
                    <div style={{ ...fieldWrapStyle, marginTop: 12 }}>
                      <label style={fieldLabelStyle}>AI Mode</label>
                      <select value={form.ai_mode} onChange={(e) => onChange("ai_mode", e.target.value)} style={inputStyle}>
                        <option value="disabled" style={optionStyle}>Disabled</option>
                        <option value="fallback" style={optionStyle}>Fallback</option>
                        <option value="live_model" style={optionStyle}>Live Model</option>
                      </select>
                    </div>
                    <div style={{ ...fieldWrapStyle, marginTop: 12 }}>
                      <label style={fieldLabelStyle}>Solo Strategy Mode</label>
                      <select value={form.solo_strategy} onChange={(e) => onChange("solo_strategy", e.target.value)} style={inputStyle}>
                        <option value="all" style={optionStyle}>Off</option>
                        {ALL_STRATEGIES.map(s => <option key={s.id} value={s.id} style={optionStyle}>{s.name}</option>)}
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </form>

          {isLoading && (
            <div style={{ marginTop: 12, height: 4, background: "rgba(255,255,255,0.05)", borderRadius: 2, overflow: "hidden" }}>
              <div style={{ height: "100%", background: "var(--accent)", width: `${backtestStatus?.progress ?? 0}%`, transition: "width 0.3s ease-out" }} />
            </div>
          )}
          {error && <p style={{ color: "var(--loss)", marginTop: 12, fontSize: 13 }}>{toDisplay(error)}</p>}
        </div>

        {!!result && (
          <>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(120px,1fr))", gap: 10 }}>
              <MetricCard label="Trades" value={summary.total_trades ?? trades.length} />
              <MetricCard label="Win Rate" value={`${fmt(summary.win_rate, 2)}%`} />
              <MetricCard label="Avg RR" value={fmt(summary.average_rr, 2)} />
              <MetricCard label="Max DD" value={`${fmt(summary.max_drawdown, 2)}%`} />
              <MetricCard label="Best Setup" value={summary.best_setup_type || "—"} />
            </div>

            {result.diagnostics && (
              <div style={cardStyle}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <h3 style={{ ...h3, margin: 0 }}>Strategy Diagnostics</h3>
                  <div style={{ display: "flex", gap: 8 }}>
                    {["funnel", "performance", "rejections"].map(t => (
                      <button key={t} onClick={() => setDiagnosticTab(t)} style={{ ...smallBtnStyle, background: diagnosticTab === t ? "var(--accent)" : "rgba(255,255,255,0.05)", color: diagnosticTab === t ? "black" : "white", border: "none" }}>{t}</button>
                    ))}
                  </div>
                </div>

                {diagnosticTab === "funnel" && (
                  <SimpleTable 
                    headers={["strategy", "status", "raw", "s_filter", "struct", "ai", "risk", "exec"]}
                    rows={Object.entries(result.diagnostics.strategy_performance || {}).map(([sid, p]) => [
                      sid, p.status,
                      p.raw_signals, p.funnel.after_strategy_filter, p.funnel.after_structure_gate, p.funnel.after_ai_gate, p.funnel.after_risk_manager, p.executed_trades
                    ])}
                  />
                )}

                {diagnosticTab === "performance" && (
                  <SimpleTable 
                    headers={["strategy", "trades", "win %", "net pnl", "pf", "avg rr", "rec"]}
                    rows={Object.entries(result.diagnostics.strategy_performance || {}).map(([sid, p]) => [
                      sid, p.executed_trades, `${p.win_rate}%`, fmt(p.net_pnl, 2), p.profit_factor, p.avg_rr,
                      <span style={{ color: p.recommendation === "KEEP" ? "var(--win)" : p.recommendation === "DISABLE" ? "var(--loss)" : "var(--accent)", fontWeight: 700 }}>{p.recommendation}</span>
                    ])}
                  />
                )}

                {diagnosticTab === "rejections" && (
                  <SimpleTable 
                    headers={["strategy", "top rejection rule", "reason"]}
                    rows={Object.entries(result.diagnostics.strategy_performance || {}).map(([sid, p]) => [
                      sid, p.top_rejection_rule, <div style={{ fontSize: 10, color: "var(--text-sub)" }}>{p.top_rejection_reason}</div>
                    ])}
                  />
                )}
              </div>
            )}

            <div style={cardStyle}>
              <h3 style={h3}>Trades ({trades.length})</h3>
              <SimpleTable
                headers={["time", "symbol", "strategy", "setup", "grade", "rr", "pnl"]}
                rows={trades.map((t) => [
                  t.exit_time || t.entry_time, t.symbol, t.strategy, t.setup || "—", t.grade || "—", fmt(t.rr, 2), fmt(t.net_pnl, 2)
                ])}
              />
            </div>
          </>
        )}
      </div>
    </RenderGuard>
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

function SimpleTable({ headers, rows }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead><tr>{headers.map((h) => <th key={h} style={thStyle}>{h}</th>)}</tr></thead>
        <tbody>
          {rows.length === 0 ? <tr><td colSpan={headers.length} style={tdStyle}>No data</td></tr> : rows.map((r, i) => (
            <tr key={i}>{r.map((c, j) => <td key={j} style={tdStyle}>{toDisplay(c)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

class RenderGuard extends React.Component {
  state = { hasError: false, message: "" };
  static getDerivedStateFromError(error) { return { hasError: true, message: error?.message || "Render error" }; }
  render() {
    if (this.state.hasError) return <div style={cardStyle}><h3>UI Error</h3><p style={{ color: "var(--loss)" }}>{this.state.message}</p></div>;
    return this.props.children;
  }
}

const h3 = { marginTop: 0, marginBottom: 10, fontSize: 16, fontWeight: 800 };
const inputStyle = { background: "#121212", border: "1px solid var(--border)", color: "var(--text-main)", borderRadius: 8, padding: "10px 12px", fontSize: 12, outline: "none" };
const optionStyle = { background: "#121212", color: "var(--text-main)" };
const fieldWrapStyle = { display: "flex", flexDirection: "column", gap: 6 };
const fieldLabelStyle = { fontSize: 11, fontWeight: 700, color: "var(--text-sub)", textTransform: "uppercase" };
const btnStyle = { ...inputStyle, cursor: "pointer", fontWeight: 700 };
const smallBtnStyle = { background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)", color: "var(--text-main)", borderRadius: 8, padding: "6px 10px", cursor: "pointer", fontSize: 11, fontWeight: 700 };
const thStyle = { textAlign: "left", fontSize: 11, color: "var(--text-sub)", padding: "8px 6px", borderBottom: "1px solid var(--border)" };
const tdStyle = { fontSize: 12, padding: "8px 6px", borderBottom: "1px solid var(--divider)" };
const dropdownStyle = { position: "absolute", top: "calc(100% + 8px)", right: 0, width: 320, background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 12, padding: 16, zIndex: 100, boxShadow: "0 10px 30px rgba(0,0,0,0.5)", backdropFilter: "blur(10px)" };

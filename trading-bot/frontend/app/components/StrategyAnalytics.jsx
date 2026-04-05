"use client";
import React from "react";
import { BarChart3, TrendingUp, Target, Award } from "lucide-react";
import { useBot } from "./BotContext";
import { useMediaQuery } from "../lib/useMediaQuery";

export default function StrategyAnalytics() {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const isSmallMobile = useMediaQuery("(max-width: 480px)");
  const { strategyAnalytics } = useBot();

  if (!strategyAnalytics || Object.keys(strategyAnalytics).length === 0) {
    return (
      <div className="glass-panel" style={{ padding: "40px", textAlign: "center", opacity: 0.5, fontWeight: "600" }}>
        AWAITING ENOUGH HISTORICAL DATA FOR ADVANCED ANALYTICS...
      </div>
    );
  }

  const stratEntries = Object.entries(strategyAnalytics);
  const topPerformer = stratEntries.length > 1 ? stratEntries.reduce((a, b) => (a[1].performance?.win_rate || 0) > (b[1].performance?.win_rate || 0) ? a : b) : null;
  const underPerformer = stratEntries.length > 1 ? stratEntries.reduce((a, b) => (a[1].performance?.win_rate || 0) < (b[1].performance?.win_rate || 0) ? a : b) : null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: isMobile ? "16px" : "24px", marginBottom: "32px" }}>
      {stratEntries.length > 1 && (
        <div style={{ display: "flex", flexDirection: isMobile ? "column" : "row", gap: isMobile ? "12px" : "24px", alignItems: "stretch" }}>
            <div className="glass-panel" style={{ flex: 1, padding: isMobile ? "12px 16px" : "16px 24px", display: "flex", alignItems: "center", gap: "12px", border: "1px solid rgba(50, 215, 75, 0.2)", background: "rgba(50, 215, 75, 0.03)" }}>
               <TrendingUp size={16} color="var(--success)" />
               <div style={{ display: "flex", flexDirection: "column" }}>
                 <span style={{ fontSize: "9px", fontWeight: "900", color: "var(--success)", textTransform: "uppercase", letterSpacing: "1px" }}>Model Alpha: Top Performer</span>
                 <span style={{ fontSize: isMobile ? "13px" : "14px", fontWeight: "700", color: "var(--text-main)" }}>{topPerformer[0]} <span style={{ color: "var(--success)", fontSize: "11px", fontWeight: "800" }}>({topPerformer[1].performance?.win_rate || 0}% Win)</span></span>
               </div>
            </div>
            <div className="glass-panel" style={{ flex: 1, padding: isMobile ? "12px 16px" : "16px 24px", display: "flex", alignItems: "center", gap: "12px", border: "1px solid rgba(255, 69, 58, 0.2)", background: "rgba(255, 69, 58, 0.03)" }}>
               <BarChart3 size={16} color="var(--loss)" />
               <div style={{ display: "flex", flexDirection: "column" }}>
                 <span style={{ fontSize: "9px", fontWeight: "900", color: "var(--loss)", textTransform: "uppercase", letterSpacing: "1px" }}>Optimization Required: Underperformer</span>
                 <span style={{ fontSize: isMobile ? "13px" : "14px", fontWeight: "700", color: "var(--text-main)" }}>{underPerformer[0]} <span style={{ color: "var(--loss)", fontSize: "11px", fontWeight: "800" }}>({underPerformer[1].performance?.win_rate || 0}% Win)</span></span>
               </div>
            </div>
        </div>
      )}
      <div style={{ display: "flex", flexWrap: "wrap", gap: isMobile ? "16px" : "24px" }}>
      {Object.entries(strategyAnalytics).map(([name, stats]) => {
        const p = stats.performance || {};
        const d = stats.diagnostics || {};
        const r = stats.rejections || {};
        
        return (
          <div key={name} className="glass-panel" style={{ padding: isMobile ? "16px" : "24px", width: "100%", border: "1px solid var(--border)", position: "relative", overflow: "hidden" }}>
            <div style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "3px",
              height: "100%",
              background: p.win_rate > 50 ? "var(--success)" : "var(--accent-purple)"
            }}></div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: isMobile ? "16px" : "20px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <span style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "1px" }}>
                   Institutional Alpha Score
                </span>
                <h4 style={{ fontSize: isMobile ? "16px" : "18px", fontWeight: "700", color: "var(--text-main)", margin: 0, letterSpacing: "-0.5px" }}>
                  {name.replace(/Strategy Family: /g, "")}
                </h4>
              </div>
              <div style={{ 
                width: "40px", height: "40px", borderRadius: "10px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)", 
                display: "flex", alignItems: "center", justifyContent: "center", color: p.win_rate > 50 ? "var(--success)" : "var(--primary)"
              }}>
                <Award size={18} />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: isSmallMobile ? "1fr 1fr" : isMobile ? "1fr 1fr" : "1fr 1fr 1fr", gap: isMobile ? "12px" : "15px", marginBottom: "20px" }}>
              <StatItem label="Win Rate" value={`${p.win_rate || 0}%`} />
              <StatItem label="Avg RR" value={p.avg_rr || 0} />
              <StatItem label="Total trades" value={p.total_trades || 0} />
              <StatItem label="Wins" value={p.wins || 0} color="var(--success)" />
              <StatItem label="Losses" value={p.losses || 0} color="var(--loss)" />
              <StatItem label="Avg Profit" value={`$${p.avg_profit || 0}`} />
              <StatItem label="TP1 Hit %" value={`${d.stage1_hit_rate || 0}%`} />
              <StatItem label="TP2 Hit %" value={`${d.stage2_hit_rate || 0}%`} />
              <StatItem label="Hold Time (m)" value={p.avg_hold_time_min || 0} />
            </div>

            {/* Rejection Breakdown */}
            {r.reasons_breakdown && Object.keys(r.reasons_breakdown).length > 0 && (
              <div style={{ marginTop: "15px", padding: "12px", background: "var(--divider)", borderRadius: "8px", border: "1px solid var(--border)" }}>
                <span style={{ fontSize: "9px", fontWeight: "700", color: "var(--text-secondary)", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>Rejection Patterns</span>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {Object.entries(r.reasons_breakdown).map(([reason, count]) => (
                    <div key={reason} style={{ fontSize: "10px", background: "var(--primary-light)", color: "var(--primary)", padding: "2px 8px", borderRadius: "4px", border: "1px solid var(--primary-glow)", whiteSpace: "normal", wordBreak: "break-word" }}>
                      {reason}: {count}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: "20px", height: "4px", width: "100%", background: "rgba(255,255,255,0.05)", borderRadius: "2px", overflow: "hidden" }}>
               <div style={{ height: "100%", width: `${p.win_rate || 0}%`, background: p.win_rate > 50 ? "var(--success)" : "var(--accent-purple)", boxShadow: "0 0 10px rgba(0,0,0,0.5)" }}></div>
            </div>
          </div>
        );
      })}
      </div>
    </div>
  );
}

function StatItem({ label, value, color }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      <span style={{ fontSize: "8px", fontWeight: "600", color: "var(--text-secondary)", textTransform: "uppercase" }}>{label}</span>
      <span style={{ fontSize: "15px", fontWeight: "700", color: color || "var(--text-main)" }}>{value}</span>
    </div>
  );
}


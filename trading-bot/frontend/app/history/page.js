"use client";
import React from "react";
import { useAuth } from "../components/AuthContext";
import { useBot } from "../components/BotContext";
import { useMediaQuery } from "../lib/useMediaQuery";
import { TrendingUp, TrendingDown, Clock, Hash, Zap, Trash2 } from "lucide-react";

export default function History() {
  const { user } = useAuth();
  const { history, deleteTradeHistoryItem } = useBot();
  const isMobile = useMediaQuery("(max-width: 768px)");

  if (!user) return null;

  return (
    <div className="animate-fade-in">
      <div
        className="glass-panel"
        style={{ padding: isMobile ? "20px" : "30px", minHeight: "600px", border: isMobile ? "none" : "1px solid var(--border)", background: isMobile ? "transparent" : "var(--bg-card)" }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: isMobile ? "column" : "row",
            justifyContent: "space-between",
            alignItems: isMobile ? "flex-start" : "center",
            marginBottom: "25px",
            gap: isMobile ? "8px" : "0"
          }}
        >
          <h2 style={{ fontSize: isMobile ? "20px" : "24px", fontWeight: "800", color: "var(--text-main)" }}>
            Closed Deal Logs
          </h2>
          <div style={{ fontSize: "12px", color: "var(--text-sub)", fontWeight: "600" }}>
            {history.length} TRADES ANALYZED (30D)
          </div>
        </div>

        {isMobile ? (
          /* Mobile Card View */
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {history.map((trade, i) => (
              <div key={trade.id ?? i} className="glass-panel" style={{ padding: "16px", borderRadius: "16px", border: "1px solid var(--border)", background: "rgba(255,255,255,0.02)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                     <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: trade.type === "BUY" ? "rgba(50, 215, 75, 0.1)" : "rgba(255, 69, 58, 0.1)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        {trade.type === "BUY" ? <TrendingUp size={16} color="var(--success)" /> : <TrendingDown size={16} color="var(--loss)" />}
                     </div>
                     <div style={{ display: "flex", flexDirection: "column" }}>
                        <span style={{ fontWeight: "800", fontSize: "14px" }}>{trade.symbol}</span>
                        <span style={{ fontSize: "10px", color: "var(--text-sub)" }}>{trade.type} • {trade.strategy}</span>
                     </div>
                  </div>
                  <div style={{ textAlign: "right", display: "flex", alignItems: "center", gap: "12px" }}>
                    <span style={{ fontWeight: "900", color: trade.profit >= 0 ? "var(--profit)" : "var(--loss)", fontSize: "16px" }}>
                      {trade.profit >= 0 ? "+" : ""}${trade.profit.toFixed(2)}
                    </span>
                    <button 
                      onClick={() => deleteTradeHistoryItem(trade.id)}
                      style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--loss)", padding: "4px", display: "flex", alignItems: "center" }}
                      title="Delete Trade"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
                
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", borderTop: "1px solid var(--divider)", paddingTop: "12px" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "8px", fontWeight: "700", color: "var(--text-sub)", textTransform: "uppercase" }}>Ticket ID</span>
                    <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-main)", fontFamily: "monospace" }}>#{trade.id}</span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <span style={{ fontSize: "8px", fontWeight: "700", color: "var(--text-sub)", textTransform: "uppercase" }}>Lot Size</span>
                    <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-main)" }}>{trade.volume.toFixed(2)}</span>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "2px", gridColumn: "span 2" }}>
                    <span style={{ fontSize: "8px", fontWeight: "700", color: "var(--text-sub)", textTransform: "uppercase" }}>Execution Time</span>
                    <span style={{ fontSize: "12px", fontWeight: "700", color: "var(--text-main)" }}>{trade.time}</span>
                  </div>
                </div>
              </div>
            ))}
            {history.length === 0 && (
              <div style={{ padding: "40px 0", textAlign: "center", opacity: 0.5, fontSize: "12px" }}>
                 No historical deals found.
              </div>
            )}
          </div>
        ) : (
          /* Desktop Table View */
          <table
            style={{
              width: "100%",
              textAlign: "left",
              borderCollapse: "collapse",
            }}
          >
            <thead>
              <tr
                style={{
                  color: "var(--text-sub)",
                  fontSize: "12px",
                  textTransform: "uppercase",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <th style={{ padding: "15px" }}>Ticket ID</th>
                <th>Asset</th>
                <th>Direction</th>
                <th>Lot Size</th>
                <th>Strategy</th>
                <th>Reason</th>
                <th>Realized P/L</th>
                <th>Execution Time</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {history.length > 0 ? (
                history.map((trade, i) => (
                  <tr
                    key={trade.id}
                    style={{
                      borderBottom: "1px solid var(--divider)",
                      fontSize: "14px",
                      transition: "0.2s",
                    }}
                    className="history-row"
                  >
                    <td
                      style={{
                        padding: "18px 15px",
                        fontFamily: "monospace",
                        color: "var(--text-sub)",
                      }}
                    >
                      #{trade.id}
                    </td>
                    <td style={{ fontWeight: "700", color: "var(--text-main)" }}>{trade.symbol}</td>
                    <td
                      style={{
                        color:
                          trade.type === "BUY" ? "var(--profit)" : "var(--loss)",
                        fontWeight: "800",
                        fontSize: "12px",
                      }}
                    >
                      {trade.type}
                    </td>
                    <td style={{ color: "var(--text-main)" }}>{trade.volume.toFixed(2)}</td>
                    <td
                      style={{
                        color: "var(--brand-accent, #6366f1)",
                        fontWeight: "700",
                        fontSize: "12px",
                        textTransform: "uppercase",
                      }}
                    >
                      {trade.strategy || "Manual"}
                    </td>
                    <td
                      style={{
                        fontSize: "12px",
                        color: "var(--text-sub)",
                        maxWidth: "250px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                      }}
                      title={trade.rationale}
                    >
                      {trade.rationale || "N/A"}
                    </td>
                    <td
                      style={{
                        color:
                          trade.profit >= 0 ? "var(--profit)" : "var(--loss)",
                        fontWeight: "700",
                      }}
                    >
                      {trade.profit >= 0 ? "+" : ""}${trade.profit.toFixed(2)}
                    </td>
                    <td
                      style={{ color: "var(--text-sub)", fontSize: "13px" }}
                    >
                      {trade.time}
                    </td>
                    <td style={{ padding: "0 15px", textAlign: "right", verticalAlign: "middle" }}>
                      <button 
                         onClick={() => deleteTradeHistoryItem(trade.id)}
                         style={{ background: "transparent", border: "none", cursor: "pointer", color: "var(--loss)", padding: "4px", opacity: 0.7, transition: "opacity 0.2s", display: "inline-flex", alignItems: "center" }}
                         onMouseEnter={(e) => e.currentTarget.style.opacity = 1}
                         onMouseLeave={(e) => e.currentTarget.style.opacity = 0.7}
                         title="Delete Trade"
                      >
                         <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td
                    colSpan="9"
                    style={{
                      padding: "100px",
                      textAlign: "center",
                      color: "var(--text-sub)",
                    }}
                  >
                    No historical deals found in the current account.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

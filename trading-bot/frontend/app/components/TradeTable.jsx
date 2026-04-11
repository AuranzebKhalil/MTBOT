import { useBot } from "./BotContext";
import { AlertCircle, TrendingUp, TrendingDown, Target, Zap, X } from "lucide-react";
import AssetIcon from "./AssetIcon";
import { useMediaQuery } from "../lib/useMediaQuery";

const fmt = (val, decimals = 2) => {
  const n = parseFloat(val);
  return isNaN(n) ? "—" : n.toFixed(decimals);
};

export default function TradeTable({ trades, selectedSymbol }) {
  const { recentRejections, handleCloseTrade } = useBot();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const safeList = Array.isArray(trades) ? trades : [];

  return (
    <div
      className="glass-panel no-lift"
      style={{ padding: isMobile ? "16px" : "25px", marginTop: "20px", border: isMobile ? "none" : "1px solid var(--border)", background: isMobile ? "transparent" : "var(--bg-card)" }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "25px",
        }}
      >
        <h2 style={{ fontSize: isMobile ? "16px" : "18px", fontWeight: "800" }}>
          Active Positions
        </h2>
        {!isMobile && (
          <div
            style={{
              padding: "8px 16px",
              borderRadius: "10px",
              background: "var(--glass-bg)",
              border: "1px solid var(--glass-border)",
              fontSize: "11px",
              fontWeight: "700",
              color: "var(--text-sub)",
              letterSpacing: "0.5px",
            }}
          >
            {selectedSymbol || "ALL ASSETS"}
          </div>
        )}
      </div>

      {isMobile ? (
        /* Mobile Card View */
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {safeList.map((trade, i) => {
            const pnl = parseFloat(trade.pnl ?? trade.profit ?? 0);
            return (
              <div key={trade.id ?? i} className="glass-panel" style={{ padding: "16px", borderRadius: "16px", border: "1px solid var(--border)", background: "rgba(255,255,255,0.02)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                     <div style={{ width: "32px", height: "32px", borderRadius: "8px", background: trade.type === "BUY" ? "rgba(50, 215, 75, 0.1)" : "rgba(255, 69, 58, 0.1)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        {trade.type === "BUY" ? <TrendingUp size={16} color="var(--success)" /> : <TrendingDown size={16} color="var(--loss)" />}
                     </div>
                     <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <AssetIcon symbol={trade.symbol} size={16} />
                        <div style={{ display: "flex", flexDirection: "column" }}>
                           <span style={{ fontWeight: "800", fontSize: "14px" }}>{trade.symbol}</span>
                           <span style={{ fontSize: "10px", color: "var(--text-sub)" }}>{trade.type} • {trade.strategy_name || trade.strategy || "Manual"}</span>
                        </div>
                     </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <span style={{ fontWeight: "900", color: pnl >= 0 ? "var(--profit)" : "var(--loss)", fontSize: "16px" }}>
                      {pnl >= 0 ? "+" : ""}${fmt(pnl)}
                    </span>
                  </div>
                </div>
                
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", borderTop: "1px solid var(--divider)", paddingTop: "12px" }}>
                  <MobileStat label="Entry" value={`$${fmt(trade.entry_price ?? trade.entry, (trade.entry_price ?? trade.entry) < 10 ? 5 : 2)}`} />
                  <MobileStat label="Volume" value={`${fmt(trade.volume, 2)} LOT`} />
                  <MobileStat label="SL / TP" value={`${trade.sl ? fmt(trade.sl, trade.sl < 10 ? 5 : 2) : "—"} / ${trade.tp ? fmt(trade.tp, trade.tp < 10 ? 5 : 2) : "—"}`} />
                  <MobileStat label="AI Score" value={`${fmt((trade.ai_score || 0) * 100, 0)}%`} color={trade.ai_score > 0.7 ? "var(--success)" : "var(--text-main)"} />
                </div>
                
                <button 
                  onClick={() => handleCloseTrade(trade.ticket_id)}
                  style={{ 
                    marginTop: '16px', 
                    width: '100%', 
                    padding: '12px', 
                    borderRadius: '12px', 
                    background: 'rgba(255, 69, 58, 0.1)', 
                    border: '1px solid rgba(255, 69, 58, 0.2)', 
                    color: 'var(--loss)', 
                    fontWeight: '800', 
                    fontSize: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '8px'
                  }}
                >
                  <X size={14} /> HALT POSITION
                </button>
              </div>
            );
          })}
          {safeList.length === 0 && (
            <div style={{ padding: "40px 0", textAlign: "center", opacity: 0.5, fontSize: "12px" }}>
               No active positions.
            </div>
          )}
        </div>
      ) : (
        /* Desktop Table View */
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr
              style={{
                color: "var(--text-sub)",
                fontSize: "12px",
                fontWeight: "700",
                textAlign: "left",
                textTransform: "uppercase",
                letterSpacing: "1px",
              }}
            >
              <th style={{ paddingBottom: "15px" }}>SYMBOL</th>
              <th style={{ paddingBottom: "15px" }}>SIDE</th>
              <th style={{ paddingBottom: "15px" }}>VOL/PROG</th>
              <th style={{ paddingBottom: "15px" }}>ENTRY</th>
              <th style={{ paddingBottom: "15px" }}>STRATEGY</th>
              <th style={{ paddingBottom: "15px" }}>AI/METADATA</th>
              <th style={{ paddingBottom: "15px" }}>SL / TP</th>
              <th style={{ paddingBottom: "15px" }}>PROFIT</th>
              <th style={{ paddingBottom: "15px", textAlign: "right" }}>ACTION</th>
            </tr>
          </thead>
          <tbody>
            {safeList.map((trade, i) => {
              const pnl = parseFloat(trade.pnl ?? trade.profit ?? 0);
              const entry = trade.entry_price ?? trade.entry;
              const sl = trade.sl;
              const tp = trade.tp;
              
              const stage1 = trade.stage1_executed;
              const stage2 = trade.stage2_executed;
              const strategyName = trade.strategy_name || trade.strategy || "Manual";

              return (
                <tr
                  key={trade.id ?? i}
                  className="history-row"
                  style={{ borderTop: "1px solid var(--glass-border)" }}
                >
                  <td style={{ padding: "18px 0", fontWeight: "700", fontFamily: "var(--font-mono)", fontSize: "13px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                       <AssetIcon symbol={trade.symbol} size={16} />
                       <div style={{ display: "flex", flexDirection: "column" }}>
                         <span>{trade.symbol || "—"}</span>
                         <span style={{ fontSize: "9px", color: "var(--text-secondary)", opacity: 0.6 }}>{trade.type} EXECUTION</span>
                       </div>
                    </div>
                  </td>
                  <td style={{ padding: "18px 0" }}>
                    <span style={{ color: trade.type === "BUY" ? "var(--success)" : "var(--loss)", fontWeight: "800", fontSize: "13px" }}>
                      {trade.type || "—"}
                    </span>
                  </td>
                  <td style={{ fontWeight: "700", fontSize: "14px", color: "var(--text-main)" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <span>{fmt(trade.volume, 2)} <span style={{ fontSize: "10px", opacity: 0.5 }}>LOT</span></span>
                      <div style={{ display: "flex", gap: "4px" }}>
                         <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: stage1 ? "var(--success)" : "rgba(255,255,255,0.1)" }} title="Stage 1 Partial"></div>
                         <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: stage2 ? "var(--success)" : "rgba(255,255,255,0.1)" }} title="Stage 2 Partial"></div>
                      </div>
                    </div>
                  </td>
                  <td style={{ fontWeight: "600", color: "var(--text-main)", fontFamily: "var(--font-mono)" }}>
                    {entry != null ? `$${fmt(entry, entry < 10 ? 5 : 2)}` : "—"}
                  </td>
                  <td style={{ fontSize: "12px", fontWeight: "700", color: "var(--primary)", textTransform: "uppercase" }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span>{strategyName}</span>
                      <span style={{ fontSize: "9px", color: "var(--text-secondary)", fontWeight: "500" }}>{trade.session || "ASIA"} SESSION</span>
                    </div>
                  </td>
                  <td style={{ fontSize: "11px" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                      <span style={{ fontWeight: "700", color: trade.ai_score > 0.7 ? "var(--success)" : "var(--text-main)" }}>AI: {fmt(trade.ai_score * 100, 0)}%</span>
                      <span style={{ color: "var(--text-secondary)", opacity: 0.7, fontSize: "9px", textTransform: "uppercase" }}>{trade.regime || "SIDEWAYS"}</span>
                    </div>
                  </td>
                  <td style={{ fontSize: "11px", color: "var(--text-sub)", fontWeight: "500", fontFamily: "var(--font-mono)" }}>
                    <div style={{ display: "flex", flexDirection: "column" }}>
                      <span style={{ color: "var(--loss)", opacity: 0.8 }}>SL: {sl ? fmt(sl, sl < 10 ? 5 : 2) : "—"}</span>
                      <span style={{ color: "var(--success)", opacity: 0.8 }}>TP: {tp ? fmt(tp, tp < 10 ? 5 : 2) : "—"}</span>
                    </div>
                  </td>
                  <td>
                    <span style={{ fontWeight: "800", color: pnl >= 0 ? "var(--profit)" : "var(--loss)", fontSize: "15px" }}>
                      {pnl >= 0 ? "+" : ""}${fmt(pnl)}
                    </span>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    <button 
                      onClick={() => handleCloseTrade(trade.ticket_id)}
                      title="Terminate on MT5"
                      style={{ 
                        background: 'rgba(255, 69, 58, 0.1)', 
                        border: '1px solid rgba(255, 69, 58, 0.1)', 
                        width: '32px', 
                        height: '32px', 
                        borderRadius: '8px', 
                        display: 'inline-flex', 
                        alignItems: 'center', 
                        justifyContent: 'center', 
                        color: 'var(--loss)',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      className="hover-lift"
                    >
                      <X size={16} strokeWidth={2.5} />
                    </button>
                  </td>
                </tr>
              );
            })}
            {safeList.length === 0 && (
              <tr>
                <td
                  colSpan="8"
                  style={{
                    padding: "80px 0",
                    textAlign: "center",
                    color: "var(--text-sub)",
                    fontSize: "14px",
                    fontWeight: "500",
                  }}
                >
                  No active positions.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      {/* REJECTED SIGNALS SECTION */}
      {recentRejections.length > 0 && (
        <div style={{ marginTop: "40px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px" }}>
             <AlertCircle size={18} color="var(--loss)" />
             <h2 style={{ fontSize: isMobile ? "14px" : "16px", fontWeight: "800", margin: 0 }}>Recent Rejections</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {recentRejections.map((rej, i) => (
              <div key={i} style={{ 
                background: "rgba(255, 69, 58, 0.05)", 
                border: "1px solid rgba(255, 69, 58, 0.1)", 
                borderRadius: isMobile ? "12px" : "12px", 
                padding: isMobile ? "12px" : "16px",
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                justifyContent: "space-between",
                alignItems: isMobile ? "flex-start" : "center",
                gap: isMobile ? "8px" : "0"
              }}>
                <div style={{ display: "flex", flexDirection: isMobile ? "column" : "row", alignItems: isMobile ? "flex-start" : "center", gap: isMobile ? "4px" : "20px" }}>
                  <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                    <AssetIcon symbol={rej.symbol} size={14} />
                    <span style={{ fontFamily: "var(--font-mono)", fontWeight: "700", fontSize: "13px" }}>{rej.symbol}</span>
                    <span style={{ fontWeight: "800", color: rej.direction === "BUY" ? "var(--success)" : "var(--loss)", fontSize: "11px" }}>{rej.direction}</span>
                  </div>
                  {!isMobile && <span style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-secondary)" }}>{rej.strategy}</span>}
                  <span style={{ fontSize: "11px", fontWeight: "700", color: "var(--loss)", background: "rgba(255, 69, 58, 0.1)", padding: "4px 8px", borderRadius: "6px" }}>{rej.reason}</span>
                </div>
                <span style={{ fontSize: "10px", color: "var(--text-secondary)", opacity: 0.6 }}>{new Date(rej.time).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function MobileStat({ label, value, color }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
      <span style={{ fontSize: "8px", fontWeight: "700", color: "var(--text-sub)", textTransform: "uppercase" }}>{label}</span>
      <span style={{ fontSize: "12px", fontWeight: "700", color: color || "var(--text-main)" }}>{value}</span>
    </div>
  );
}

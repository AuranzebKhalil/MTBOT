"use client";
import React from "react";
import { useBot } from "./BotContext";
import { useTheme } from "./ThemeContext";
import { ChevronRight, Maximize2 } from "lucide-react";

export default function StrategyExplanation({ symbol, onOpenTerminal }) {
  const { symbolData } = useBot();
  const { theme } = useTheme();

  const decision = symbolData[symbol]?.last_decision || {
    direction: "WAIT",
    strategy: "Scanning",
    reason: "Monitoring market structure...",
    score: 0,
    flow: [],
  };

  return (
    <div
      style={{
        padding: "12px 20px",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        background: theme === 'dark' ? "rgba(0,0,0,0.15)" : "rgba(0,122,255,0.03)",
        borderTop: "1px solid var(--divider)",
      }}
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-main)", fontSize: "12px", fontWeight: "800" }}>
          <div style={{ width: "4px", height: "12px", background: "var(--primary)", borderRadius: "2px" }}></div>
          TERMINAL
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", position: "relative" }}>
           <div style={{ width: "6px", height: "6px", background: "var(--primary)", borderRadius: "50%", boxShadow: "0 0 8px var(--primary)" }} className="animate-pulse-slow"></div>
           <span style={{ fontSize: "10px", color: "var(--text-secondary)", fontWeight: "600", textTransform: "uppercase", letterSpacing: "0.5px" }}>
             Scanning Order Flow...
           </span>
        </div>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <div style={{ 
            padding: "4px 12px", borderRadius: "6px", 
            background: "rgba(50, 215, 75, 0.05)", border: "1px solid rgba(50, 215, 75, 0.15)",
            display: "flex", alignItems: "center", gap: "6px",
            color: "var(--success)", fontSize: "10px", fontWeight: "900"
        }}>
           <div style={{ width: "6px", height: "6px", background: "var(--success)", borderRadius: "50%", boxShadow: "0 0 8px var(--success)" }}></div>
           LIVE SYNC
        </div>
        <button 
          onClick={onOpenTerminal}
          style={{ 
            background: 'rgba(255,255,255,0.03)', 
            border: '1px solid var(--divider)', 
            color: 'var(--text-secondary)', 
            cursor: 'pointer',
            padding: "6px",
            borderRadius: "6px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}
          className="hover-lift"
        >
          <Maximize2 size={14} />
        </button>
      </div>
    </div>
  );
}

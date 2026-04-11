"use client";
import React from "react";
import AuralithChart from "./AuralithChart";
import StrategyExplanation from "./StrategyExplanation";
import { useBot } from "./BotContext";
import { useTheme } from "./ThemeContext";
import {
  Activity,
  Settings,
  Maximize2,
  ChevronDown,
  TrendingUp,
} from "lucide-react";
import { useMediaQuery } from "../lib/useMediaQuery";
import AssetIcon from "./AssetIcon";

export default function QuantGrid({ onOpenTerminal }) {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const { activeSymbols } = useBot();
  const { theme } = useTheme();

  const gridStyle = {
    display: "grid",
    gap: isMobile ? "16px" : "24px",
    width: "100%",
    height: "100%",
    gridTemplateColumns: isMobile ? "1fr" : (activeSymbols.length === 1 ? "1fr" : "1fr 1fr"),
    gridTemplateRows: isMobile ? "auto" : (activeSymbols.length <= 2 ? "1fr" : "1fr 1fr"),
    minHeight: isMobile ? "400px" : "800px",
  };

  return (
    <div style={gridStyle}>
      {activeSymbols.slice(0, 4).map((symbol) => (
        <div
          key={symbol}
          className="glass-panel"
          style={{
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            height: "100%",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            background: theme === 'dark' 
              ? "linear-gradient(180deg, rgba(13, 17, 23, 0.4) 0%, rgba(13, 17, 23, 0.8) 100%)"
              : "linear-gradient(180deg, rgba(255, 255, 255, 0.9) 0%, rgba(244, 247, 250, 0.95) 100%)",
            backdropFilter: "blur(20px)",
            position: "relative",
            boxShadow: theme === 'dark' ? "0 10px 40px rgba(0,0,0,0.5)" : "0 10px 40px rgba(0,122,255,0.05)",
          }}
        >
          {/* Subtle Border Glow */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: "1px",
              background:
                "linear-gradient(90deg, transparent, var(--primary), transparent)",
              opacity: 0.3,
            }}
          ></div>

          {/* Internal Header */}
          <div
            style={{
              padding: "20px 24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderBottom: "1px solid var(--divider)",
              background: "rgba(255,255,255,0.02)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
               <div style={{ width: "40px", display: "flex", justifyContent: "center" }}>
                 <AssetIcon symbol={symbol} size={18} />
               </div>
              <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                <div
                  style={{ display: "flex", alignItems: "center", gap: "8px" }}
                >
                  <span
                    style={{
                      fontSize: "16px",
                      fontWeight: "700",
                      color: "var(--text-main)",
                      letterSpacing: "-0.5px",
                    }}
                  >
                    {symbol}
                  </span>
                  <div
                    style={{
                      padding: "3px 8px",
                      borderRadius: "6px",
                      background: "rgba(50, 215, 75, 0.1)",
                      color: "var(--success)",
                      fontSize: "9px",
                      fontWeight: "700",
                      border: "1px solid rgba(50, 215, 75, 0.2)",
                      textTransform: "uppercase",
                      letterSpacing: "0.5px"
                    }}
                  >
                    ALGO ACTIVE
                  </div>
                </div>
                <span
                  style={{
                    fontSize: "10px",
                    color: "var(--text-secondary)",
                    opacity: 0.7,
                    fontWeight: "600",
                    letterSpacing: "0.2px"
                  }}
                >
                  M5 Timeframe • Neural Engine v4.5
                </span>
              </div>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
              <ChartHeaderIcon icon={<Activity size={15} />} />
              <ChartHeaderIcon icon={<Settings size={15} />} />
              <div
                style={{
                  width: "1px",
                  height: "16px",
                  background: "var(--divider)",
                }}
              ></div>
              <ChartHeaderIcon
                icon={<Maximize2 size={15} />}
                onClick={() => onOpenTerminal(symbol)}
              />
            </div>
          </div>

          {/* Chart Area */}
          <div
            style={{
              flex: 1,
              minHeight: 0,
              position: "relative",
            }}
          >
            <AuralithChart symbol={symbol} />
          </div>

          {/* Terminal Footer */}
          <div style={{ height: "68px", flexShrink: 0 }}>
            <StrategyExplanation
              symbol={symbol}
              onOpenTerminal={() => onOpenTerminal(symbol)}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function ChartHeaderIcon({ icon, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        color: "var(--text-secondary)",
        cursor: "pointer",
        opacity: 0.7,
        transition: "all 0.2s ease",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.color = "var(--text-main)";
        e.currentTarget.style.opacity = 1;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.color = "var(--text-secondary)";
        e.currentTarget.style.opacity = 0.7;
      }}
    >
      {icon}
    </div>
  );
}

function PairIcon({ symbol }) {
  // Use Lucide for consistent, non-breaking icons
  const isCrypto =
    symbol.includes("USD") ||
    symbol.includes("BTC") ||
    symbol.includes("ETH") ||
    symbol.includes("SOL");

  return (
    <div
      style={{
        width: "32px",
        height: "32px",
        borderRadius: "10px",
        background: isCrypto
          ? "linear-gradient(135deg, rgba(0, 122, 255, 0.15) 0%, rgba(0, 122, 255, 0.05) 100%)"
          : "linear-gradient(135deg, rgba(50, 215, 75, 0.15) 0%, rgba(50, 215, 75, 0.05) 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: isCrypto
          ? "1px solid rgba(0, 122, 255, 0.2)"
          : "1px solid rgba(50, 215, 75, 0.2)",
      }}
    >
      {isCrypto ? (
        <TrendingUp size={16} color="var(--primary)" />
      ) : (
        <Activity size={16} color="var(--success)" />
      )}
    </div>
  );
}

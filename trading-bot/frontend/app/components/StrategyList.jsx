"use client";
import React, { useState } from "react";
import {
  ShieldCheck,
  Crosshair,
  Zap,
  Activity,
  Eye,
  Radar,
  ArrowRightLeft,
  Banknote,
  TrendingDown,
  Layers,
  X,
  TrendingUp,
  CheckCircle,
  AlertTriangle,
  BarChart2,
  Clock,
  Plus,
  Trash2,
} from "lucide-react";
import { useBot } from "./BotContext";
import { useTheme } from "./ThemeContext";
import { useMediaQuery } from "../lib/useMediaQuery";

const strategies = [
  {
    id: "SMC_SWEEP",
    name: "SRR - Sweep Reclaim Reversal",
    prob: "High",
    freq: "Daily",
    type: "Reversal",
    icon: Banknote,
    color: "#00ffbd",
    description:
      "Our primary reversal framework. Trades stop-hunt moves that sweep institutional liquidity and immediately reclaim structure with M1 confirmation.",
    entry:
      "M15 bias alignment + M5 liquidity sweep + M1 structural reclaim close + M1 MSS confirm.",
    exit: "TP at 1:2 R/R min. SL placed beyond the sweep wick extreme.",
    steps: [
      "Identify liquidity pools on M5/M15",
      "Wait for stop-hunt wick",
      "Monitor M1 for structural reclaim close",
      "Confirm with M1 MSS before entry",
    ],
    risk: "Low-Medium",
    note: "High-probability institutional 'Change of Mind' footprint.",
    image: "/strategies/srr.png",
  },
  {
    id: "SMC_TREND",
    name: "CR - Continuation Retest",
    prob: "High",
    freq: "High",
    type: "Trend",
    icon: Zap,
    color: "#5b86e5",
    description:
      "The main trend-following engine. Captures momentum after clean M15 structural breaks and returns to fresh value zones.",
    entry:
      "M15 trend BOS + fresh M5 OB/FVG + M1 Rejection candle confirmation at the touch.",
    exit: "TP at next structural high/low. SL at previous swing point or behind OB.",
    steps: [
      "Confirm HTF BOS Trend",
      "Wait for return to fresh (unmitigated) zone",
      "Identify M1 rejection or engulfing candle",
      "Execute on momentum confirmation",
    ],
    risk: "Low",
    note: "High-frequency setup for trending markets.",
    image: "/strategies/mss.png",
  },
  {
    id: "SMC_MSS",
    name: "MSS - Market Structure Shift",
    prob: "High",
    freq: "Daily",
    type: "Reversal",
    icon: ShieldCheck,
    color: "#34ace0",
    description:
      "Captures the early stages of a trend reversal by identifying the first break of a minor swing point with major displacement.",
    entry:
      "M1 CHOCH break with >2.0x avg candle displacement + HTF Bias alignment.",
    exit: "TP at major swing high/low. SL at expansion candle extreme.",
    steps: [
      "Detect trend exhaustion near HTF zone",
      "Wait for displacement break with 2.0x body size",
      "Verify structural follow-through",
      "Execute on candle close or shadow retest",
    ],
    risk: "Low-Medium",
    note: "The most reliable early-entry signal for trend changes.",
    image: "/strategies/mss.png",
  },
  {
    id: "SMC_MITIGATION",
    name: "FTM - First Touch Mitigation",
    prob: "Medium-High",
    freq: "1-2/day",
    type: "Precision",
    icon: Activity,
    color: "#6c5ce7",
    description:
      "Trades the first return into a fresh imbalance zone (FVG) created by aggressive institutional displacement candles.",
    entry:
      "Strong FVG creation (M15) + First return to 50% equilibrium + M1 momentum confirmation.",
    exit: "TP at start of move. SL beyond FVG boundary.",
    steps: [
      "Scan for fresh, large FVG zones",
      "Ensure 1.8x+ displacement on creation",
      "Wait for first touch of 50% midpoint",
      "Execute on M1 bullish/bearish confirmation",
    ],
    risk: "Medium",
    note: "Freshwater zones have the highest order-fill probability.",
    image: "/strategies/ftm.png",
  },
  {
    id: "SMC_BREAKER",
    name: "BB - Breaker Block Retest",
    prob: "Medium",
    freq: "1-2/day",
    type: "SMC",
    icon: Layers,
    color: "#ffb142",
    description:
      "Trades failed order blocks that have turned into support/resistance levels during aggressive moves.",
    entry:
      "Failed OB break with displacement + return to the 'Breaker' zone + M1 rejection.",
    exit: "TP at 1.5 R/R. SL beyond the breaker zone boundary.",
    steps: [
      "Locate failed/broken OB",
      "Confirm aggressive break through the zone",
      "Wait for breaker retest touch",
      "Execute on M1 price rejection candle",
    ],
    risk: "Medium",
    note: "Institutions using failed zones to mitigate remaining orders.",
    image: "/strategies/srr.png",
  },
  {
    id: "HYBRID_SR",
    name: "Advanced S/R Reversal",
    prob: "High",
    freq: "2-3/day",
    type: "Structure",
    icon: Layers,
    color: "#fdcb6e",
    description: "Focuses on high-timeframe (M15) support and resistance zones. Requires high displacement from the level.",
    entry: "Interaction with M15 zone + 1.5x displacement move away from the level.",
    exit: "TP at opposite zone. SL 1x ATR beyond the zone.",
    steps: ["Identify M15 key structural zones", "Wait for zone interaction", "Confirm 1.5x displacement rejection", "Execute on follow-through close"],
    risk: "Medium",
    note: "Modern adaptation of classic floor trading principles.",
    image: "/strategies/srr.png",
  },
  {
    id: "HYBRID_MASTER",
    name: "Hybrid Master Switcher",
    prob: "Dynamic",
    freq: "Adaptive",
    type: "AI Master",
    icon: ShieldCheck,
    color: "#00d2ff",
    description: "The core engine. Dynamically switches between structural SMC frameworks based on real-time market regime audits.",
    entry: "Automatic selection based on ADX and structural context.",
    exit: "Varies by active sub-strategy.",
    steps: ["Detect Market Regime (ADX/ATR)", "Assign best-fit structural strategy", "Execute with AI confirmation", "Manage with dynamic risk"],
    risk: "Very Low",
    note: "Optimal for hands-off multi-condition trading.",
    image: "/strategies/mss.png",
  },
  {
    id: "MAD_TREND_LOOP",
    name: "MAD - Trend Loop (Lyro RS)",
    prob: "High",
    freq: "High",
    type: "Score Logic",
    icon: Activity,
    color: "#ff00ff",
    description: "Mean Absolute Deviation score logic. Retired from primary execution due to lower structural confluence.",
    entry: "Combined signal of MAD crossover and ALMA momentum score sequence.",
    exit: "Close when strategy reverses signal.",
    steps: ["Compute MAD bounds", "Evaluate momentum loop", "Trigger on composite score", "Execute automatically"],
    risk: "Medium",
    note: "Legacy prop indicator logic. Disabled by default.",
    image: "/strategies/ftm.png",
  },
  {
    id: "SMC_REVERSAL",
    name: "ER - Exhaustion Reversal",
    prob: "Sniper",
    freq: "Weekly",
    type: "Reversal",
    icon: Radar,
    color: "#ee5a24",
    description: "Indicator-based reversals. Removed to reduce noise on lower timeframes.",
    entry: "M15 RSI extreme + M1 CHOCH break.",
    exit: "TP at 1:3 R/R. SL at extreme.",
    steps: ["Price enters HTF zone", "M5/M15 RSI Overextended", "LTF CHOCH validation", "Execute on engulfment"],
    risk: "Medium",
    note: "Removed in April 2026 Refactor.",
    image: "/strategies/er.png",
  },
  {
    id: "SMC_VSA",
    name: "VSA - Absorption Shift",
    prob: "Medium",
    freq: "2-4/day",
    type: "Volume",
    icon: ArrowRightLeft,
    color: "#ff9f43",
    description: "Volume-based absorption. Removed in favor of pure structural footprints.",
    entry: "High-volume spike (3x avg) + Price rejection at zone.",
    exit: "TP at liquidity pool. SL at wick.",
    steps: ["Identify key S/R zone", "Monitor for 3.0x volume spikes", "Confirm price rejection", "Execute on session flow"],
    risk: "Medium",
    note: "Removed in April 2026 Refactor.",
    image: "/strategies/vsa.png",
  },
  {
    id: "SMC_VOLUME",
    name: "VOL - Order Flow/POC",
    prob: "High",
    freq: "High",
    type: "Volume",
    icon: TrendingUp,
    color: "#747d8c",
    description: "Point of Control mapping. Retired due to high fakeout rate without structural confirmation.",
    entry: "Price interaction with POC + Session bias.",
    exit: "Target 1:1.5 R/R. SL beyond POC.",
    steps: ["Calculate Session POC", "Wait for price interaction", "Analyze volume delta", "Execute with session flow"],
    risk: "Low",
    note: "Removed in April 2026 Refactor.",
    image: "/strategies/vsa.png",
  },
  {
    id: "HYBRID_REVERSION",
    name: "Mean Reversion (BB/RSI)",
    prob: "High",
    freq: "Daily",
    type: "Reversal",
    icon: Activity,
    color: "#a29bfe",
    description: "Pure indicator reversion. Retired as M1 signals are prone to volatility noise.",
    entry: "Price outside BB + RSI extremes.",
    exit: "TP at Middle BB.",
    steps: ["Confirm low ADX", "Wait for BB boundary", "Verify RSI extreme", "Execute on rejection"],
    risk: "Low",
    note: "Removed in April 2026 Refactor.",
    image: "/strategies/er.png",
  },
  {
    id: "HYBRID_BREAKOUT",
    name: "Momentum Breakout",
    prob: "High",
    freq: "1-2/day",
    type: "Momentum",
    icon: Zap,
    color: "#00b894",
    description: "Range breakouts. Retired to avoid chasing fake liquidity sweeps.",
    entry: "Close outside consolidation + volume spike.",
    exit: "1:1.5 R/R.",
    steps: ["Identify consolidation", "Monitor volume", "Wait for range exit", "Execute on close"],
    risk: "Medium-High",
    note: "Removed in April 2026 Refactor.",
    image: "/strategies/ftm.png",
  },
];

function AddStrategyModal({ isOpen, onClose, onAdd }) {
  const [formData, setFormData] = useState({
    name: "",
    type: "SMC",
    description: "",
    logic: "",
  });
  const isMobile = useMediaQuery("(max-width: 768px)");

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onAdd(formData);
    onClose();
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "var(--glass-bg)",
        backdropFilter: "blur(10px)",
        zIndex: 1001,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: isMobile ? "10px" : "20px",
      }}
    >
      <div
        className="glass-panel"
        style={{
          padding: isMobile ? "20px" : "30px",
          maxWidth: "500px",
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
        }}
      >
        <h3
          style={{ marginBottom: "20px", fontSize: isMobile ? "18px" : "20px" }}
        >
          Deploy Custom Stratagem
        </h3>
        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "15px" }}
        >
          <div>
            <label style={{ fontSize: "11px", color: "var(--text-sub)" }}>
              Strategy Name
            </label>
            <input
              type="text"
              className="glass-panel"
              style={{
                width: "100%",
                padding: "10px",
                background: "var(--divider)",
                marginTop: "5px",
              }}
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              placeholder="e.g. Volume Absorption Setup"
              required
            />
          </div>
          <div>
            <label style={{ fontSize: "11px", color: "var(--text-sub)" }}>
              Short Description
            </label>
            <input
              type="text"
              className="glass-panel"
              style={{
                width: "100%",
                padding: "10px",
                background: "var(--divider)",
                marginTop: "5px",
              }}
              value={formData.description}
              onChange={(e) =>
                setFormData({ ...formData, description: e.target.value })
              }
              placeholder="Detect smart money absorbing liquidity..."
              required
            />
          </div>
          <div>
            <label style={{ fontSize: "11px", color: "var(--text-sub)" }}>
              Institutional Logic (English)
            </label>
            <textarea
              className="glass-panel"
              style={{
                width: "100%",
                padding: "10px",
                background: "var(--divider)",
                marginTop: "5px",
                minHeight: "100px",
                color: "var(--text-main)",
              }}
              value={formData.logic}
              onChange={(e) =>
                setFormData({ ...formData, logic: e.target.value })
              }
              placeholder="Describe the entry conditions and logic here..."
              required
            />
          </div>
          <div style={{ display: "flex", gap: "10px", marginTop: "10px" }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                flex: 1,
                padding: "12px",
                borderRadius: "10px",
                background: "var(--divider)",
                color: "var(--text-main)",
                fontSize: "13px",
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              style={{ flex: 1, padding: "12px", fontSize: "13px" }}
            >
              Deploy
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function StrategyModal({ strategy, onClose, isActive, onToggle }) {
  const isMobile = useMediaQuery("(max-width: 768px)");
  if (!strategy) return null;
  const Icon = strategy.icon;

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "var(--glass-bg)",
        backdropFilter: "blur(8px)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: isMobile ? "0" : "20px",
        animation: "fadeIn 0.2s ease",
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--bg-card)",
          border: isMobile ? "none" : `1px solid ${strategy.color}40`,
          borderRadius: isMobile ? "0" : "24px",
          padding: isMobile ? "30px 20px" : "40px",
          maxWidth: "700px",
          width: "100%",
          height: isMobile ? "100%" : "auto",
          maxHeight: isMobile ? "100%" : "90vh",
          overflowY: "auto",
          boxShadow: "var(--shadow-glow)",
          position: "relative",
        }}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: "20px",
            right: "20px",
            background: "var(--divider)",
            border: "1px solid var(--glass-border)",
            borderRadius: "50%",
            width: "36px",
            height: "36px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            color: "var(--text-sub)",
            transition: "all 0.2s",
            zIndex: 10,
          }}
        >
          <X size={16} />
        </button>

        {/* Header */}
        <div
          style={{
            display: "flex",
            flexDirection: isMobile ? "column" : "row",
            alignItems: isMobile ? "center" : "flex-start",
            textAlign: isMobile ? "center" : "left",
            gap: isMobile ? "15px" : "20px",
            marginBottom: "30px",
          }}
        >
          <div
            style={{
              background: `${strategy.color}18`,
              border: `1px solid ${strategy.color}40`,
              padding: isMobile ? "12px" : "16px",
              borderRadius: "16px",
              color: strategy.color,
              flexShrink: 0,
            }}
          >
            <Icon size={isMobile ? 24 : 28} />
          </div>
          <div>
            <div
              style={{
                fontSize: "10px",
                color: strategy.color,
                fontWeight: "800",
                letterSpacing: "2px",
                textTransform: "uppercase",
                marginBottom: "6px",
              }}
            >
              {strategy.type} STRATEGY
            </div>
            <h2
              style={{
                fontSize: isMobile ? "20px" : "22px",
                fontWeight: "900",
                lineHeight: 1.2,
                marginBottom: "8px",
              }}
            >
              {strategy.name}
            </h2>
            <p
              style={{
                color: "var(--text-sub)",
                fontSize: "14px",
                lineHeight: 1.6,
              }}
            >
              {strategy.description}
            </p>

            {/* Radio Switch in Header */}
            <div
              onClick={onToggle}
              style={{
                marginTop: "15px",
                display: "flex",
                alignItems: "center",
                gap: "12px",
                cursor: "pointer",
                padding: "8px 16px",
                background: "var(--divider)",
                borderRadius: "12px",
                border: "1px solid var(--glass-border)",
                width: "fit-content",
                transition: "all 0.2s",
              }}
            >
              <div
                style={{
                  width: "40px",
                  height: "20px",
                  background: isActive ? strategy.color : "#1a1c22",
                  borderRadius: "20px",
                  position: "relative",
                  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                  border: `1px solid ${isActive ? "transparent" : "var(--glass-border)"}`,
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    top: "2px",
                    left: isActive ? "22px" : "2px",
                    width: "14px",
                    height: "14px",
                    background: isActive ? "white" : "var(--text-sub)",
                    borderRadius: "50%",
                    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                    boxShadow: isActive ? `0 0 10px ${strategy.color}` : "none",
                  }}
                />
              </div>
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "800",
                  color: isActive ? "white" : "var(--text-sub)",
                  letterSpacing: "1px",
                }}
              >
                {isActive ? "STRATEGY ENGAGED" : "STRATEGY HALTED"}
              </span>
            </div>
          </div>
        </div>

        {/* Strategy Image View */}
        {strategy.image && (
          <div
            style={{
              width: "100%",
              borderRadius: "16px",
              overflow: "hidden",
              marginBottom: "30px",
              border: `1px solid ${strategy.color}30`,
              boxShadow: `0 10px 40px ${strategy.color}15`,
              background: "var(--divider)",
              position: "relative",
            }}
          >
            <div
              style={{
                position: "absolute",
                top: "12px",
                left: "12px",
                background: "rgba(0,0,0,0.6)",
                backdropFilter: "blur(4px)",
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "10px",
                fontWeight: "700",
                color: "white",
                zIndex: 1,
                border: "1px solid rgba(255,255,255,0.1)",
              }}
            >
              LIVE FRAMEWORK EXAMPLE
            </div>
            <img
              src={strategy.image}
              alt={strategy.name}
              style={{
                width: "100%",
                height: "auto",
                display: "block",
                filter: "contrast(1.1) brightness(0.9)",
              }}
            />
          </div>
        )}

        {/* Stats Row */}
        <div
          style={{
            display: "flex",
            flexDirection: isMobile ? "column" : "row",
            gap: "12px",
            marginBottom: "30px",
          }}
        >
          {[
            {
              icon: TrendingUp,
              label: "Win Probability",
              value: strategy.prob,
              color: "#00ffbd",
            },
            {
              icon: Clock,
              label: "Frequency",
              value: strategy.freq,
              color: "#5b86e5",
            },
            {
              icon: BarChart2,
              label: "Risk Level",
              value: strategy.risk.split(" ")[0],
              color: "#ff9f43",
            },
          ].map((stat, i) => (
            <div
              key={i}
              style={{
                flex: 1,
                background: "var(--divider)",
                borderRadius: "12px",
                padding: "14px",
                border: "1px solid var(--glass-border)",
                textAlign: "center",
                display: isMobile ? "flex" : "block",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              {!isMobile && (
                <stat.icon
                  size={16}
                  style={{ color: stat.color, marginBottom: "6px" }}
                />
              )}
              <div style={{ textAlign: isMobile ? "left" : "center" }}>
                <div
                  style={{
                    fontSize: "10px",
                    color: "var(--text-sub)",
                    letterSpacing: "0.5px",
                  }}
                >
                  {stat.label}
                </div>
                {isMobile && (
                  <div
                    style={{
                      fontSize: "16px",
                      fontWeight: "900",
                      color: stat.color,
                    }}
                  >
                    {stat.value}
                  </div>
                )}
              </div>
              {!isMobile && (
                <div
                  style={{
                    fontSize: "18px",
                    fontWeight: "900",
                    color: stat.color,
                  }}
                >
                  {stat.value}
                </div>
              )}
              {isMobile && (
                <stat.icon size={16} style={{ color: stat.color }} />
              )}
            </div>
          ))}
        </div>

        {/* Step-by-Step Process */}
        <div style={{ marginBottom: "25px" }}>
          <h3
            style={{
              fontSize: "13px",
              fontWeight: "800",
              letterSpacing: "1.5px",
              textTransform: "uppercase",
              color: strategy.color,
              marginBottom: "16px",
            }}
          >
            ⚙️ How It Works
          </h3>
          <div
            style={{ display: "flex", flexDirection: "column", gap: "10px" }}
          >
            {strategy.steps.map((step, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: "14px",
                  alignItems: "flex-start",
                }}
              >
                <div
                  style={{
                    minWidth: "26px",
                    height: "26px",
                    borderRadius: "50%",
                    background: `${strategy.color}20`,
                    border: `1px solid ${strategy.color}50`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "11px",
                    fontWeight: "900",
                    color: strategy.color,
                    flexShrink: 0,
                  }}
                >
                  {i + 1}
                </div>
                <span
                  style={{
                    fontSize: "13px",
                    color: "var(--text-main)",
                    lineHeight: 1.6,
                    paddingTop: "3px",
                  }}
                >
                  {step}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Entry & Exit */}
        <div
          style={{
            display: "flex",
            flexDirection: isMobile ? "column" : "row",
            gap: "12px",
            marginBottom: "25px",
          }}
        >
          <div
            style={{
              flex: 1,
              background: "rgba(0, 255, 189, 0.04)",
              border: "1px solid rgba(0, 255, 189, 0.15)",
              borderRadius: "12px",
              padding: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "8px",
              }}
            >
              <CheckCircle size={14} color="#00ffbd" />
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "800",
                  color: "#00ffbd",
                  letterSpacing: "1px",
                }}
              >
                ENTRY
              </span>
            </div>
            <p
              style={{
                fontSize: "12px",
                color: "var(--text-sub)",
                lineHeight: 1.6,
              }}
            >
              {strategy.entry}
            </p>
          </div>
          <div
            style={{
              flex: 1,
              background: "rgba(255, 71, 87, 0.04)",
              border: "1px solid rgba(255, 71, 87, 0.15)",
              borderRadius: "12px",
              padding: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                marginBottom: "8px",
              }}
            >
              <AlertTriangle size={14} color="#ff4757" />
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "800",
                  color: "#ff4757",
                  letterSpacing: "1px",
                }}
              >
                EXIT
              </span>
            </div>
            <p
              style={{
                fontSize: "12px",
                color: "var(--text-sub)",
                lineHeight: 1.6,
              }}
            >
              {strategy.exit}
            </p>
          </div>
        </div>

        {/* Institutional Note */}
        <div
          style={{
            background: `${strategy.color}08`,
            border: `1px solid ${strategy.color}25`,
            borderRadius: "12px",
            padding: "16px",
            display: "flex",
            gap: "12px",
          }}
        >
          <span style={{ fontSize: "18px" }}>🏛️</span>
          <div>
            <div
              style={{
                fontSize: "11px",
                fontWeight: "800",
                color: strategy.color,
                letterSpacing: "1px",
                marginBottom: "4px",
              }}
            >
              INSTITUTIONAL INSIGHT
            </div>
            <p
              style={{
                fontSize: "13px",
                color: "var(--text-sub)",
                lineHeight: 1.6,
              }}
            >
              {strategy.note}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function StrategyList({ isExpanded }) {
  const [selectedStrategy, setSelectedStrategy] = useState(null);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const {
    customStrategies,
    addCustomStrategy,
    removeCustomStrategy,
    strategySettings,
    updateStrategySetting,
  } = useBot();
  const isMobile = useMediaQuery("(max-width: 768px)");

  return (
    <>
      <div
        className="glass-panel"
        style={{
          padding: isMobile ? "20px" : "30px",
          minHeight: "100%",
          border: isMobile ? "none" : "1px solid var(--border)",
          background: isMobile ? "transparent" : "var(--bg-card)",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: isMobile ? "column" : "row",
            justifyContent: "space-between",
            alignItems: isMobile ? "flex-start" : "flex-start",
            marginBottom: "25px",
            gap: isMobile ? "20px" : "0",
          }}
        >
          <div>
            <h2
              style={{
                fontSize: isMobile ? "18px" : "18px",
                fontWeight: "800",
              }}
            >
              Active AI Stratagems
            </h2>
            <p
              style={{
                fontSize: "11px",
                color: "var(--text-sub)",
                marginTop: "4px",
              }}
            >
              Master-level Smart Money Frameworks
            </p>
          </div>
          <div
            style={{
              display: "flex",
              gap: "10px",
              alignItems: "center",
              width: isMobile ? "100%" : "auto",
            }}
          >
            <button
              onClick={() => setIsAddOpen(true)}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
                background: "var(--divider)",
                border: "1px solid var(--glass-border)",
                padding: isMobile ? "10px" : "8px 16px",
                borderRadius: "10px",
                fontSize: "12px",
                fontWeight: "700",
                color: "var(--primary)",
                flex: isMobile ? 1 : "none",
              }}
            >
              <Plus size={14} /> ADD
            </button>
            <div
              style={{
                fontSize: "11px",
                color: "var(--profit)",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                fontWeight: "700",
              }}
            >
              <ShieldCheck size={14} /> LIVE SYNC
            </div>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: isMobile
              ? "1fr"
              : "repeat(auto-fill, minmax(300px, 1fr))",
            gap: isMobile ? "10px" : "12px",
          }}
        >
          {/* Active Core Strategies (Validated High Probability: SRR, CR, MSS) */}
          {strategies
            .filter(s => ["SMC_SWEEP", "SMC_TREND", "SMC_MSS"].includes(s.id))
            .map((s, idx) => (
            <StrategyCard
              key={idx}
              strategy={s}
              onClick={() => setSelectedStrategy(s)}
              isActive={strategySettings[s.id]?.enabled ?? true}
              onToggle={(e) => {
                e.stopPropagation();
                const currentStatus = strategySettings && strategySettings[s.id] ? strategySettings[s.id].enabled : true;
                updateStrategySetting(s.id, {
                  enabled: !currentStatus,
                });
              }}
            />
          ))}

          {/* User Strategies */}
          {customStrategies
            .filter(s => !["CRT Volatility Breakout", "LSR Liquidity Sweep", "2BR Institutional Reversal"].includes(s.name))
            .map((s, idx) => (
            <StrategyCard
              key={`custom-${idx}`}
              strategy={{
                ...s,
                icon: Activity,
                freq: "Personal",
                prob: "Custom",
                steps: [s.logic],
                entry: "Manual Detection",
                exit: "Manual/Logic",
                note: "User defined institutional logic.",
              }}
              onClick={() => setSelectedStrategy(s)}
              isActive={strategySettings[s.id]?.enabled ?? true}
              onToggle={(e) => {
                e.stopPropagation();
                const currentStatus = strategySettings && strategySettings[s.id] ? strategySettings[s.id].enabled : true;
                updateStrategySetting(s.id, {
                  enabled: !currentStatus,
                });
              }}
              onDelete={(e) => {
                e.stopPropagation();
                removeCustomStrategy(s.id);
              }}
            />
          ))}
        </div>

        {/* Disabled Strategies Section */}
        <div style={{ marginTop: "50px", marginBottom: "20px" }}>
           <h2
              style={{
                fontSize: isMobile ? "16px" : "16px",
                fontWeight: "800",
                color: "var(--text-sub)",
                display: "flex",
                alignItems: "center",
                gap: "10px"
              }}
            >
              <X size={16} /> 
              Disabled or Removed Strategies (Low Probability)
            </h2>
            <p
              style={{
                fontSize: "11px",
                color: "var(--text-sub)",
                marginTop: "4px",
                opacity: 0.7
              }}
            >
              The following internal strategies have been phased out due to market noise or low conviction.
            </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: isMobile
              ? "1fr"
              : "repeat(auto-fill, minmax(300px, 1fr))",
            gap: isMobile ? "10px" : "12px",
            opacity: 0.5
          }}
        >
          {strategies
            .filter(s => !["SMC_SWEEP", "SMC_TREND", "SMC_MSS"].includes(s.id))
            .map((s, idx) => (
            <StrategyCard
              key={`disabled-${idx}`}
              strategy={{...s, prob: "N/A"}}
              onClick={() => setSelectedStrategy(s)}
              isActive={false} // Always show as off
              onToggle={(e) => {
                e.stopPropagation();
                // Logic kept simple, but effectively disabled in backend
                alert("This strategy is currently hard-disabled in the backend engine for safety.");
              }}
            />
          ))}
        </div>
      </div>

      <StrategyModal
        strategy={selectedStrategy}
        onClose={() => setSelectedStrategy(null)}
        isActive={selectedStrategy ? (strategySettings[selectedStrategy.id]?.enabled ?? true) : true}
        onToggle={() => {
          if (selectedStrategy) {
            const currentStatus = strategySettings && strategySettings[selectedStrategy.id] ? strategySettings[selectedStrategy.id].enabled : true;
            console.log(`Toggling Modal Strategy ${selectedStrategy.id} from ${currentStatus} to ${!currentStatus}`);
            updateStrategySetting(selectedStrategy.id, {
              enabled: !currentStatus,
            });
          }
        }}
      />

      <AddStrategyModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onAdd={addCustomStrategy}
      />
    </>
  );
}

function StrategyCard({ strategy, onClick, onDelete, isActive, onToggle }) {
  const Icon = strategy.icon || Activity;
  return (
    <div
      onClick={onClick}
      style={{
        background: "rgba(255,255,255,0.02)",
        border: "1px solid var(--glass-border)",
        padding: "16px",
        borderRadius: "14px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        cursor: "pointer",
        transition: "all 0.2s ease",
        position: "relative",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.background = `${strategy.color}10`;
        e.currentTarget.style.border = `1px solid ${strategy.color}40`;
        e.currentTarget.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = "rgba(255,255,255,0.02)";
        e.currentTarget.style.border = "1px solid var(--glass-border)";
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        <div
          style={{
            color: strategy.color,
            background: `${strategy.color}15`,
            padding: "10px",
            borderRadius: "10px",
          }}
        >
          <Icon size={18} />
        </div>
        <div>
          <p
            style={{ fontSize: "13px", fontWeight: "700", marginBottom: "3px" }}
          >
            {strategy.name}
          </p>
          <p
            style={{
              fontSize: "10px",
              color: "var(--text-sub)",
              textTransform: "uppercase",
              letterSpacing: "1px",
            }}
          >
            {strategy.type} • {strategy.freq}
          </p>
          <div
            onClick={onToggle}
            style={{
              marginTop: "8px",
              display: "flex",
              alignItems: "center",
              gap: "8px",
              cursor: "pointer",
              padding: "4px 0", // larger hit area
              zIndex: 10,
              position: "relative",
            }}
          >
            <div
              style={{
                width: "28px",
                height: "14px",
                background: isActive ? strategy.color : "#1a1c22",
                borderRadius: "14px",
                position: "relative",
                transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                border: `1px solid ${isActive ? "transparent" : "rgba(255,255,255,0.1)"}`,
                flexShrink: 0,
              }}
            >
              <div
                style={{
                  position: "absolute",
                  top: "2px",
                  left: isActive ? "16px" : "2px",
                  width: "8px",
                  height: "8px",
                  background: "white",
                  borderRadius: "50%",
                  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                  boxShadow: isActive ? `0 0 5px ${strategy.color}80` : "none",
                }}
              />
            </div>
            <span
              style={{
                fontSize: "10px",
                fontWeight: "800",
                color: isActive ? "white" : "var(--text-sub)",
                letterSpacing: "0.5px",
                transition: "all 0.2s",
              }}
            >
              {isActive ? "ACTIVE" : "OFF"}
            </span>
          </div>
        </div>
      </div>
      <div style={{ textAlign: "right", minWidth: "55px" }}>
        <span
          style={{
            display: "block",
            fontSize: "16px",
            fontWeight: "800",
            color: strategy.color,
          }}
        >
          {strategy.prob}
        </span>
        <span
          style={{
            fontSize: "9px",
            color: "var(--text-sub)",
            textTransform: "uppercase",
            letterSpacing: "1px",
          }}
        >
          WR
        </span>
      </div>
      {onDelete && (
        <button
          onClick={onDelete}
          style={{
            position: "absolute",
            top: "-5px",
            right: "-5px",
            background: "var(--loss)",
            color: "white",
            border: "none",
            borderRadius: "50%",
            width: "20px",
            height: "20px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "10px",
            cursor: "pointer",
            boxShadow: "0 4px 10px rgba(0,0,0,0.3)",
          }}
        >
          <X size={12} />
        </button>
      )}
    </div>
  );
}

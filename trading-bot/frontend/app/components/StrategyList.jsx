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
    name: "SRR - Sweep Reclaim Reversal",
    prob: "High",
    freq: "Daily",
    type: "Reversal",
    icon: Banknote,
    color: "#00ffbd",
    description:
      "Our primary reversal framework. Trades stop-hunt moves that sweep institutional liquidity and immediately reclaim structure.",
    entry:
      "M15 bias alignment + M5 liquidity sweep of equal highs/lows + M1 candle close back through the swept level + FVG/OB retest.",
    exit: "TP at 1:2 R/R min. SL placed beyond the sweep wick extreme.",
    steps: [
      "Identify major liquidity pools (equal highs/lows) on M5/M15",
      "Wait for a fast 'stop-hunt' wick to clear the pool",
      "Monitor M1 for a structural shift (BOS) back into the range",
      "Confirm institutional activity via Relative Activity filter",
      "Execution on first touch of the reclaim-zone (FVG or OB)",
    ],
    risk: "Low-Medium (Requires Triple-Timeframe Sync)",
    note: "This family merges Liquidity Sweep, ILC, and PDF into a single high-expectancy reversal engine.",
  },
  {
    name: "CR - Continuation Retest",
    prob: "High",
    freq: "High",
    type: "Trend",
    icon: Zap,
    color: "#5b86e5",
    description:
      "The main trend-following engine. Captures momentum after clean structural breaks and low-volatility pullbacks.",
    entry:
      "M15/M5 structural agreement + Clean M1 Break of Structure (BOS) + high-quality retest of the break zone or fresh OB.",
    exit: "TP at next structural high/low. SL at previous swing point (1:1.5 min R/R).",
    steps: [
      "Confirm M15 Macro Bias is trending (HH/HL or LL/LH)",
      "Wait for M1/M5 Break of Structure in the trend direction",
      "Identify a fresh Order Block or FVG created by the break",
      "Wait for a controlled, low-activity pullback to the zone",
      "Rejection candle confirms continuation → Enter with flow",
    ],
    risk: "Low — Highest frequency institutional setup",
    note: "Merges Structure Break, SSC, and OBM into a unified trend-continuation framework.",
  },
  {
    name: "MR - Manipulation Reversal",
    prob: "Medium-High",
    freq: "2-4/day",
    type: "Trap",
    icon: ArrowRightLeft,
    color: "#ff9f43",
    description:
      "Capitalizes on false breakouts and range-traps. Enters as retail breakout traders are squeezed out by smart money.",
    entry:
      "Institutional impulse candle creates a range → price breaks out → price closes back INSIDE the range on the very next candle.",
    exit: "TP at the opposite side of the manipulation range. SL beyond the trap wick.",
    steps: [
      "Large impulse candle establishes a 'Dealing Range'",
      "Next candle attempts to drive price beyond the range",
      "Smart money absorbs the move (Relative Activity spike)",
      "Price snaps back and closes deep inside the original range",
      "Entry at the close of the snap-back candle",
    ],
    risk: "Medium",
    note: "Consolidates CRT, LTR, and SMR into one 'Manipulation' family. High pain for retail, high gain for Quant.",
  },
  {
    name: "FTM - First Touch Mitigation",
    prob: "Medium",
    freq: "1-2/day",
    type: "Precision",
    icon: Activity,
    color: "#6c5ce7",
    description:
      "Trades the first high-quality return into a fresh imbalance zone created by institutional displacement.",
    entry:
      "Massive displacement creates a supply/demand zone + first-time return to that zone + rejection confirmation on M1.",
    exit: "TP at the start of the displacement move. SL beyond the zone boundary.",
    steps: [
      "Scan for 'Fresh' (unmitigated) supply and demand zones",
      "The zone must be created by a strong 'Rally-Base-Drop' move",
      "Wait for price to return for its FIRST touch of the zone",
      "Rejection candle (long wick) confirms orders are being filled",
      "Entry at rejection close (Skip if price drifts slowly through)",
    ],
    risk: "Medium — Freshwater zones have the highest probability",
    note: "Replaces the old SND and PDF mitigation modules with a stricter 'Freshness' filter.",
  },
  {
    name: "ER - Exhaustion Reversal",
    prob: "Sniper",
    freq: "Weekly",
    type: "High Qual",
    icon: Radar,
    color: "#ee5a24",
    description:
      "A rare, high-threshold sniper setup for catching reversals after a final unstable push into a deep HTF zone.",
    entry:
      "Deep HTF Supply/Demand zone touch + extreme blow-off Relative Activity + full candle engulfment on M1/M5.",
    exit: "TP at 1:3 R/R. SL at the absolute extreme of the exhaustion wick.",
    steps: [
      "Price enters a major M30 or H1 institutional interest zone",
      "Final stab into the zone with extreme tick activity (>3x avg)",
      "Immediate engulfing candle removes the exhaustion candle",
      "Macro Confluence Score (MCS) must be > 3 for this setup",
      "Entry at close of engulfing bar",
    ],
    risk: "Low Reward/Risk (due to sniper threshold)",
    note: "The evolution of the IER strategy. Only trades when blood and panic are at extremes.",
  },
  {
    name: "2BR - Two-Bar Reversal",
    prob: "High",
    freq: "Daily",
    type: "Reversal",
    icon: ArrowRightLeft,
    color: "#ff4757",
    description:
      "Detects abrupt institutional sentiment shifts using high-volume reversals on adjacent bars.",
    entry:
      "Bar 1 (Impact) followed by Bar 2 (Reaction) with >1.2x average volume. Bar 2 must engulf or heavily retrace Bar 1.",
    exit: "TP at next structural level. SL beyond the extremes of the 2-bar pattern.",
    steps: [
      "Identify a significant impulse bar (Bar 1) with high volume",
      "Wait for the immediate Next bar (Bar 2) to reverse the move",
      "Volume on Bar 2 should be equally high or higher than Bar 1",
      "Enter at the close of Bar 2 once reversal is confirmed",
    ],
    risk: "Medium — High probability when at major S/R levels",
    note: "Classic VSA footprint of an institutional 'Change of Mind'.",
  },
  {
    name: "NSND - No Supply / No Demand",
    prob: "Medium-High",
    freq: "High",
    type: "Test",
    icon: Radar,
    color: "#747d8c",
    description:
      "Identifies the lack of institutional interest in a counter-trend move before a continuation.",
    entry:
      "Low volume candle (less than previous two) with a small body/spread during a trend pullback.",
    exit: "Target 1.5 - 2 R/R. SL below/above the test candle.",
    steps: [
      "Observe a trend pullback or temporary reversal",
      "Identify a small-bodied candle with very low relative volume",
      "Low volume indicates institutions are not supporting the pullback",
      "Wait for a confirmation candle in the trend direction",
      "Entry at confirmation close",
    ],
    risk: "Low — Best used as a secondary confirmation for other setups",
    note: "The ultimate 'test' used by professional operators before they push price.",
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
        style={{ padding: isMobile ? "20px" : "30px", maxWidth: "500px", width: "100%", maxHeight: "90vh", overflowY: "auto" }}
      >
        <h3 style={{ marginBottom: "20px", fontSize: isMobile ? "18px" : "20px" }}>Deploy Custom Stratagem</h3>
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
                fontSize: "13px"
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

function StrategyModal({ strategy, onClose }) {
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
            zIndex: 10
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
          </div>
        </div>

        {/* Stats Row */}
        <div style={{ display: "flex", flexDirection: isMobile ? "column" : "row", gap: "12px", marginBottom: "30px" }}>
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
                justifyContent: "space-between"
              }}
            >
              {!isMobile && <stat.icon
                size={16}
                style={{ color: stat.color, marginBottom: "6px" }}
              />}
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
                 {isMobile && <div style={{ fontSize: "16px", fontWeight: "900", color: stat.color }}>{stat.value}</div>}
              </div>
              {!isMobile && <div
                style={{
                  fontSize: "18px",
                  fontWeight: "900",
                  color: stat.color,
                }}
              >
                {stat.value}
              </div>}
               {isMobile && <stat.icon size={16} style={{ color: stat.color }} />}
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
        <div style={{ display: "flex", flexDirection: isMobile ? "column" : "row", gap: "12px", marginBottom: "25px" }}>
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
  const { customStrategies, addCustomStrategy, removeCustomStrategy } =
    useBot();
  const isMobile = useMediaQuery("(max-width: 768px)");

  return (
    <>
      <div
        className="glass-panel"
        style={{ padding: isMobile ? "20px" : "30px", minHeight: "100%", border: isMobile ? "none" : "1px solid var(--border)", background: isMobile ? "transparent" : "var(--bg-card)" }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: isMobile ? "column" : "row",
            justifyContent: "space-between",
            alignItems: isMobile ? "flex-start" : "flex-start",
            marginBottom: "25px",
            gap: isMobile ? "20px" : "0"
          }}
        >
          <div>
            <h2 style={{ fontSize: isMobile ? "18px" : "18px", fontWeight: "800" }}>
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
          <div style={{ display: "flex", gap: "10px", alignItems: "center", width: isMobile ? "100%" : "auto" }}>
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
                flex: isMobile ? 1 : "none"
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
            gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fill, minmax(300px, 1fr))",
            gap: isMobile ? "10px" : "12px",
          }}
        >
          {/* Core Strategies */}
          {strategies.map((s, idx) => (
            <StrategyCard
              key={idx}
              strategy={s}
              onClick={() => setSelectedStrategy(s)}
            />
          ))}

          {/* User Strategies */}
          {customStrategies.map((s, idx) => (
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
              onDelete={(e) => {
                e.stopPropagation();
                removeCustomStrategy(s.id);
              }}
            />
          ))}
        </div>
      </div>

      <StrategyModal
        strategy={selectedStrategy}
        onClose={() => setSelectedStrategy(null)}
      />

      <AddStrategyModal
        isOpen={isAddOpen}
        onClose={() => setIsAddOpen(false)}
        onAdd={addCustomStrategy}
      />
    </>
  );
}

function StrategyCard({ strategy, onClick, onDelete }) {
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

"use client";
import React from "react";
import { useBot } from "../components/BotContext";
import { useAuth } from "../components/AuthContext";
import { Shield, Target, AlertTriangle, RefreshCcw, Hash, Trash2 } from "lucide-react";
import { useMediaQuery } from "../lib/useMediaQuery";

export default function RiskControl() {
  const { user } = useAuth();
  const { riskParams, setRiskParams, saveRiskProfile, clearRiskEvents } = useBot();
  const isMobile = useMediaQuery("(max-width: 768px)");

  if (!user) return null;

  const RiskItem = ({
    title,
    sub,
    icon: Icon,
    value,
    onChange,
    step = 1,
    min = 0,
    max = 100,
    isPercentage = false,
    extremeThreshold = null,
  }) => {
    const isExtreme = extremeThreshold && Number(value) >= extremeThreshold;
    return (
      <div
        className="glass-card"
        style={{
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: isMobile ? "20px" : "25px",
          marginBottom: "20px",
          border: isExtreme
            ? "1px solid rgba(255, 50, 50, 0.3)"
            : "1px solid var(--glass-border)",
          boxShadow: isExtreme ? "0 0 15px rgba(255, 50, 50, 0.1)" : "none",
          transition: "all 0.3s ease",
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: isMobile ? "column" : "row",
            justifyContent: "space-between",
            alignItems: isMobile ? "flex-start" : "center",
            gap: isMobile ? "15px" : "0",
            marginBottom: "15px",
          }}
        >
          <div style={{ display: "flex", gap: "15px", alignItems: "center" }}>
            <div
              style={{
                width: isMobile ? "40px" : "50px",
                height: isMobile ? "40px" : "50px",
                borderRadius: "12px",
                background: isExtreme
                  ? "rgba(255, 50, 50, 0.1)"
                  : "rgba(91, 134, 229, 0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: isExtreme ? "#ff4d4d" : "var(--primary)",
                flexShrink: 0
              }}
            >
              <Icon size={isMobile ? 20 : 24} />
            </div>
            <div>
              <h4 style={{ fontSize: isMobile ? "14px" : "16px", marginBottom: "2px", fontWeight:"800" }}>{title}</h4>
              <p style={{ fontSize: "11px", color: "var(--text-sub)", lineHeight: "1.3" }}>
                {sub}
              </p>
            </div>
          </div>
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: "8px", 
            width: isMobile ? "100%" : "auto",
            justifyContent: isMobile ? "flex-end" : "flex-start"
          }}>
            <input
              type="number"
              step={step}
              min={min}
              max={max}
              value={value}
              onChange={onChange}
              style={{
                background: "rgba(255,255,255,0.05)",
                border: "1px solid var(--glass-border)",
                padding: "10px 12px",
                borderRadius: "10px",
                color: isExtreme ? "#ff4d4d" : "white",
                width: "90px",
                textAlign: "right",
                fontSize: "15px",
                fontWeight: "700",
              }}
            />
            {isPercentage && (
              <span
                style={{
                  color: "var(--text-sub)",
                  fontSize: "16px",
                  fontWeight: "700",
                }}
              >
                %
              </span>
            )}
          </div>
        </div>

        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={onChange}
          style={{
            width: "100%",
            accentColor: isExtreme ? "#ff4d4d" : "var(--primary)",
            cursor: "pointer",
            height: "6px",
            borderRadius: "5px",
          }}
        />
      </div>
    );
  };

  return (
    <div 
      className="animate-fade-in" 
      style={{ 
        maxWidth: "800px",
        padding: isMobile ? "0 0 40px 0" : "0"
      }}
    >
      <div style={{ marginBottom: isMobile ? "20px" : "30px" }}>
        <h1 style={{ fontSize: isMobile ? "24px" : "32px", marginBottom: "8px", fontWeight: "900" }}>
          Risk Management
        </h1>
        <p style={{ color: "var(--text-sub)", fontSize: isMobile ? "13px" : "15px" }}>
          Configure the safety protocols for the Alpha Core execution engine.
        </p>
      </div>

      {/* Institutional note */}
      <div
        style={{
          background: "rgba(91,134,229,0.06)",
          border: "1px solid rgba(91,134,229,0.2)",
          borderRadius: "16px",
          padding: isMobile ? "16px" : "18px 22px",
          marginBottom: "30px",
          fontSize: isMobile ? "11px" : "12px",
          color: "var(--text-sub)",
          lineHeight: "1.7",
        }}
      >
        <span
          style={{
            color: "var(--primary)",
            fontWeight: "900",
            display: "block",
            marginBottom: "6px",
            letterSpacing: "1px"
          }}
        >
          ⚙️ PROTOCOL INTERACTION
        </span>
        Engine halts when <b>any</b> limit is hit:
        <br />
        1. <b>Daily Drawdown</b> — floating + closed losses vs equity.
        <br />
        2. <b>Max Daily Trades</b> — Cap on daily losing attempts.
        <br />
        3. <b>Max Concurrent</b> — Simultaneous open position cap.
      </div>

      <div style={{ display: "flex", flexDirection: "column" }}>
        <RiskItem
          title="Exposure Per Deal"
          sub="Liquidity allocation per position entry."
          icon={Target}
          value={riskParams.risk_per_trade}
          step="0.5"
          min="0"
          max="20"
          isPercentage={true}
          extremeThreshold={5}
          onChange={(e) =>
            setRiskParams({ ...riskParams, risk_per_trade: e.target.value })
          }
        />

        <RiskItem
          title="Max Concurrent"
          sub="Global simultaneous exposure cap."
          icon={Shield}
          value={riskParams.max_trades}
          min="1"
          max="10"
          step="1"
          extremeThreshold={6}
          onChange={(e) =>
            setRiskParams({ ...riskParams, max_trades: e.target.value })
          }
        />

        <RiskItem
          title="Max Losing Attempts"
          sub="Daily halt threshold for losing trades."
          icon={Hash}
          value={riskParams.max_daily_trades}
          min="1"
          max="20"
          step="1"
          extremeThreshold={10}
          onChange={(e) =>
            setRiskParams({ ...riskParams, max_daily_trades: e.target.value })
          }
        />

        <RiskItem
          title="Daily Drawdown"
          sub="Account equity circuit breaker."
          icon={AlertTriangle}
          value={riskParams.daily_loss}
          step="0.5"
          min="1"
          max="50"
          isPercentage={true}
          extremeThreshold={15}
          onChange={(e) =>
            setRiskParams({ ...riskParams, daily_loss: e.target.value })
          }
        />

        <button
          onClick={saveRiskProfile}
          className="glass-panel"
          style={{
            marginTop: "10px",
            background: "var(--gradient-primary)",
            border: "none",
            color: "black",
            padding: isMobile ? "18px" : "22px",
            borderRadius: "18px",
            fontWeight: "900",
            cursor: "pointer",
            fontSize: isMobile ? "14px" : "15px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            boxShadow: "0 15px 30px rgba(91, 134, 229, 0.25)",
            animation: "pulseShadow 3s infinite",
          }}
        >
          <RefreshCcw size={isMobile ? 18 : 20} />
          SYNCHRONIZE PROTOCOLS
        </button>

        <button
          onClick={clearRiskEvents}
          className="glass-panel"
          style={{
            marginTop: "12px",
            background: "rgba(255, 50, 50, 0.1)",
            border: "1px solid rgba(255, 50, 50, 0.2)",
            color: "#ff4d4d",
            padding: isMobile ? "16px" : "18px",
            borderRadius: "18px",
            fontWeight: "700",
            cursor: "pointer",
            fontSize: isMobile ? "13px" : "14px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "10px",
            transition: "all 0.3s ease",
          }}
        >
          <Trash2 size={isMobile ? 16 : 18} />
          PURGE SECURITY LOGS
        </button>
      </div>

      <style jsx>{`
        @keyframes pulseShadow {
          0% { box-shadow: 0 15px 30px rgba(91, 134, 229, 0.25); }
          50% { box-shadow: 0 15px 45px rgba(91, 134, 229, 0.45); }
          100% { box-shadow: 0 15px 30px rgba(91, 134, 229, 0.25); }
        }
      `}</style>
    </div>
  );
}

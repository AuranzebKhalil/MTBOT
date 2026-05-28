"use client";
import React from "react";
import { useBot } from "../components/BotContext";
import { useAuth } from "../components/AuthContext";
import { Shield, Target, AlertTriangle, RefreshCcw, Hash, Trash2, RotateCcw, TrendingUp, TrendingDown } from "lucide-react";
import { useMediaQuery } from "../lib/useMediaQuery";
import RRRatioDropdown from "../components/RRRatioDropdown";

export default function RiskControl() {
  const { user } = useAuth();
  const {
    riskParams,
    setRiskParams,
    saveRiskProfile,
    clearRiskEvents,
    resetRiskProfile,
    selectedTF,
    updateBotSettings,
  } = useBot();
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
          Configure the safety protocols and environment for the Alpha Core engine.
        </p>
      </div>

      {/* --- ENVIRONMENT TOGGLE --- */}
      <div 
        className="glass-card" 
        style={{ 
          marginBottom: "30px", 
          padding: "20px", 
          display: "flex", 
          justifyContent: "space-between", 
          alignItems: "center",
          border: riskParams.trading_mode === "REAL" ? "1px solid rgba(255, 69, 58, 0.3)" : "1px solid var(--glass-border)",
          background: riskParams.trading_mode === "REAL" ? "rgba(255, 69, 58, 0.02)" : "rgba(255, 255, 255, 0.01)"
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
          <div style={{
            width: "42px",
            height: "42px",
            borderRadius: "10px",
            background: riskParams.trading_mode === "REAL" ? "rgba(255, 69, 58, 0.1)" : "rgba(0, 255, 189, 0.1)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: riskParams.trading_mode === "REAL" ? "var(--loss)" : "var(--profit)"
          }}>
            <Shield size={20} />
          </div>
          <div>
             <h4 style={{ fontSize: "14px", fontWeight: "800", marginBottom: "2px" }}>
               ENVIRONMENT: {riskParams.trading_mode === "REAL" ? "LIVE CAPITAL" : "DEMO SANDBOX"}
             </h4>
             <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>
               {riskParams.trading_mode === "REAL" 
                 ? "Execution on real market liquidity. High risk." 
                 : "Virtual liquidity simulation. Zero capital risk."}
             </p>
          </div>
        </div>

        <div style={{ 
          display: "flex", 
          background: "rgba(0,0,0,0.2)", 
          padding: "4px", 
          borderRadius: "12px", 
          border: "1px solid var(--glass-border)" 
        }}>
          <button
            onClick={() => setRiskParams({ ...riskParams, trading_mode: "DEMO" })}
            style={{
              padding: "8px 16px",
              borderRadius: "8px",
              border: "none",
              fontSize: "10px",
              fontWeight: "900",
              cursor: "pointer",
              background: riskParams.trading_mode === "DEMO" ? "var(--profit)" : "transparent",
              color: riskParams.trading_mode === "DEMO" ? "black" : "var(--text-sub)",
              transition: "0.3s"
            }}
          >
            DEMO
          </button>
          <button
            onClick={() => setRiskParams({ ...riskParams, trading_mode: "REAL" })}
            style={{
              padding: "8px 16px",
              borderRadius: "8px",
              border: "none",
              fontSize: "10px",
              fontWeight: "900",
              cursor: "pointer",
              background: riskParams.trading_mode === "REAL" ? "var(--loss)" : "transparent",
              color: riskParams.trading_mode === "REAL" ? "white" : "var(--text-sub)",
              transition: "0.3s"
            }}
          >
            REAL
          </button>
        </div>
      </div>

      {/* --- TIMEFRAME CONTROL --- */}
      <div
        className="glass-card"
        style={{
          marginBottom: "30px",
          padding: isMobile ? "18px" : "20px",
          border: "1px solid var(--glass-border)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "14px",
            gap: "12px",
            flexWrap: "wrap",
          }}
        >
          <h4 style={{ fontSize: "14px", fontWeight: "800", margin: 0 }}>
            Execution Timeframe
          </h4>
          <span style={{ fontSize: "11px", color: "var(--text-sub)" }}>
            Signal generation interval
          </span>
        </div>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
            gap: "8px",
          }}
        >
          {["M1", "M5", "M15", "H1"].map((tf) => (
            <button
              key={tf}
              onClick={() => updateBotSettings(null, tf)}
              style={{
                padding: "10px 12px",
                borderRadius: "10px",
                border: "1px solid var(--glass-border)",
                fontSize: "12px",
                fontWeight: "800",
                cursor: "pointer",
                background: selectedTF === tf ? "var(--primary)" : "rgba(255,255,255,0.03)",
                color: selectedTF === tf ? "black" : "var(--text-secondary)",
                transition: "all 0.2s ease",
              }}
            >
              {tf}
            </button>
          ))}
        </div>
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
          title="Min Setup Score"
          sub="Technical score required to approve institutional setups."
          icon={Target}
          value={riskParams.min_setup_score}
          step="1"
          min="50"
          max="100"
          extremeThreshold={85}
          onChange={(e) =>
            setRiskParams({ ...riskParams, min_setup_score: e.target.value })
          }
        />

        <RiskItem
          title="Min AI Confidence"
          sub="Predictive probability threshold from Sentinel AI."
          icon={Shield}
          value={riskParams.min_ai_confidence}
          step="0.01"
          min="0.3"
          max="0.9"
          extremeThreshold={0.7}
          onChange={(e) =>
            setRiskParams({ ...riskParams, min_ai_confidence: e.target.value })
          }
        />

        <RiskItem
          title="Max Allowed Spread"
          sub="Circuit breaker for high volatility/low liquidity periods."
          icon={AlertTriangle}
          value={riskParams.max_spread_points}
          step="1"
          min="10"
          max="200"
          extremeThreshold={100}
          onChange={(e) =>
            setRiskParams({ ...riskParams, max_spread_points: e.target.value })
          }
        />

        <RiskItem
          title="Late Entry Tolerance"
          sub="Maximum percentage of the move already completed before blocking."
          icon={TrendingUp}
          value={riskParams.late_entry_threshold}
          step="0.01"
          min="0.1"
          max="0.9"
          extremeThreshold={0.8}
          onChange={(e) =>
            setRiskParams({ ...riskParams, late_entry_threshold: e.target.value })
          }
        />

        <RiskItem
          title="Min R:R Filter"
          sub="Minimum risk-to-reward ratio required for execution."
          icon={TrendingDown}
          value={riskParams.min_rr_filter}
          step="0.1"
          min="0.5"
          max="3.0"
          extremeThreshold={2.0}
          onChange={(e) =>
            setRiskParams({ ...riskParams, min_rr_filter: e.target.value })
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
          title="Daily Trade Limit"
          sub="Maximum total execution attempts per 24h cycle."
          icon={Hash}
          value={riskParams.max_daily_trades}
          min="1"
          max="50"
          step="1"
          extremeThreshold={30}
          onChange={(e) =>
            setRiskParams({ ...riskParams, max_daily_trades: e.target.value })
          }
        />

        <RiskItem
          title="Daily Drawdown"
          sub="Account equity circuit breaker threshold."
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

        {/* Risk Reward Ratio */}
        <div
          className="glass-card"
          style={{
            padding: isMobile ? "20px" : "25px",
            marginBottom: "32px",
            border: "1px solid var(--glass-border)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "15px", marginBottom: "15px" }}>
            <div
              style={{
                width: isMobile ? "40px" : "50px",
                height: isMobile ? "40px" : "50px",
                borderRadius: "12px",
                background: "rgba(91, 134, 229, 0.1)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "var(--primary)",
              }}
            >
              <Target size={isMobile ? 20 : 24} />
            </div>
            <div>
              <h4 style={{ fontSize: isMobile ? "14px" : "16px", marginBottom: "2px", fontWeight:"800" }}>Target RR Ratio</h4>
              <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Efficiency threshold for institutional order flow.</p>
            </div>
          </div>
        <RRRatioDropdown
            value={riskParams.risk_reward_ratio}
            onChange={(val) => setRiskParams({ ...riskParams, risk_reward_ratio: val })}
          />
        </div>

        {/* --- ADVANCED SAFETY PROTOCOLS --- */}
        <div 
          style={{ 
            marginBottom: "40px", 
            padding: "32px", 
            background: "rgba(255, 255, 255, 0.01)", 
            borderRadius: "24px", 
            border: "1px solid var(--divider)" 
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
             <Shield size={18} color="var(--primary)" />
             <h3 style={{ fontSize: "14px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "1px" }}>Advanced Safety Protocols</h3>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* HTF Filter Toggle */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "15px", background: "rgba(255,255,255,0.02)", borderRadius: "12px" }}>
              <div>
                <h5 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "4px" }}>HTF Trend Alignment</h5>
                <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Only execute signals aligned with M15/H1 institutional bias.</p>
              </div>
              <button 
                onClick={() => setRiskParams({...riskParams, enable_htf_filter: !riskParams.enable_htf_filter})}
                style={{
                  width: "50px",
                  height: "26px",
                  borderRadius: "13px",
                  background: riskParams.enable_htf_filter ? "var(--primary)" : "rgba(255,255,255,0.1)",
                  border: "none",
                  position: "relative",
                  cursor: "pointer",
                  transition: "0.3s"
                }}
              >
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "10px",
                  background: "white",
                  position: "absolute",
                  top: "3px",
                  left: riskParams.enable_htf_filter ? "27px" : "3px",
                  transition: "0.3s"
                }} />
              </button>
            </div>

            {/* Volatility Filter Toggle */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "15px", background: "rgba(255,255,255,0.02)", borderRadius: "12px" }}>
              <div>
                <h5 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "4px" }}>Volatility Protection (ATR)</h5>
                <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Block trades where SL is too tight relative to market noise.</p>
              </div>
              <button 
                onClick={() => setRiskParams({...riskParams, enable_volatility_filter: !riskParams.enable_volatility_filter})}
                style={{
                  width: "50px",
                  height: "26px",
                  borderRadius: "13px",
                  background: riskParams.enable_volatility_filter ? "var(--primary)" : "rgba(255,255,255,0.1)",
                  border: "none",
                  position: "relative",
                  cursor: "pointer",
                  transition: "0.3s"
                }}
              >
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "10px",
                  background: "white",
                  position: "absolute",
                  top: "3px",
                  left: riskParams.enable_volatility_filter ? "27px" : "3px",
                  transition: "0.3s"
                }} />
              </button>
            </div>

            {riskParams.enable_volatility_filter && (
              <div style={{ padding: "0 15px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
                  <span style={{ fontSize: "12px", fontWeight: "700" }}>Volatility Buffer (ATR Mult)</span>
                  <span style={{ fontSize: "12px", color: "var(--primary)", fontWeight: "800" }}>{riskParams.min_sl_atr_multiplier}x</span>
                </div>
                <input 
                  type="range"
                  min="0.1"
                  max="2.0"
                  step="0.1"
                  value={riskParams.min_sl_atr_multiplier}
                  onChange={(e) => setRiskParams({...riskParams, min_sl_atr_multiplier: e.target.value})}
                  style={{ width: "100%", accentColor: "var(--primary)" }}
                />
              </div>
            )}

            {/* Level Distance Filter Toggle */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "15px", background: "rgba(255,255,255,0.02)", borderRadius: "12px" }}>
              <div>
                <h5 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "4px" }}>Institutional Level Buffer</h5>
                <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Block trades entering directly into major S/R levels.</p>
              </div>
              <button 
                onClick={() => setRiskParams({...riskParams, enable_level_distance_filter: !riskParams.enable_level_distance_filter})}
                style={{
                  width: "50px",
                  height: "26px",
                  borderRadius: "13px",
                  background: riskParams.enable_level_distance_filter ? "var(--primary)" : "rgba(255,255,255,0.1)",
                  border: "none",
                  position: "relative",
                  cursor: "pointer",
                  transition: "0.3s"
                }}
              >
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "10px",
                  background: "white",
                  position: "absolute",
                  top: "3px",
                  left: riskParams.enable_level_distance_filter ? "27px" : "3px",
                  transition: "0.3s"
                }} />
              </button>
            </div>

            {riskParams.enable_level_distance_filter && (
              <div style={{ padding: "0 15px" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
                  <span style={{ fontSize: "12px", fontWeight: "700" }}>Min R:R to Level</span>
                  <span style={{ fontSize: "12px", color: "var(--primary)", fontWeight: "800" }}>{riskParams.min_reward_to_nearest_level_rr}x</span>
                </div>
                <input 
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.1"
                  value={riskParams.min_reward_to_nearest_level_rr}
                  onChange={(e) => setRiskParams({...riskParams, min_reward_to_nearest_level_rr: e.target.value})}
                  style={{ width: "100%", accentColor: "var(--primary)" }}
                />
              </div>
            )}

            {/* Same-Zone Block Toggle */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "15px", background: "rgba(255,255,255,0.02)", borderRadius: "12px" }}>
              <div>
                <h5 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "4px" }}>Same-Zone Protection</h5>
                <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Prevent duplicate entries in the same price zone.</p>
              </div>
              <button 
                onClick={() => setRiskParams({...riskParams, enable_same_zone_block: !riskParams.enable_same_zone_block})}
                style={{
                  width: "50px",
                  height: "26px",
                  borderRadius: "13px",
                  background: riskParams.enable_same_zone_block ? "var(--primary)" : "rgba(255,255,255,0.1)",
                  border: "none",
                  position: "relative",
                  cursor: "pointer",
                  transition: "0.3s"
                }}
              >
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "10px",
                  background: "white",
                  position: "absolute",
                  top: "3px",
                  left: riskParams.enable_same_zone_block ? "27px" : "3px",
                  transition: "0.3s"
                }} />
              </button>
            </div>

            {/* Post-SL Cooldown Toggle */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "15px", background: "rgba(255,255,255,0.02)", borderRadius: "12px" }}>
              <div>
                <h5 style={{ fontSize: "14px", fontWeight: "700", marginBottom: "4px" }}>Loss Recovery Cooldown</h5>
                <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Pause trading after a loss to prevent revenge trading.</p>
              </div>
              <button 
                onClick={() => setRiskParams({...riskParams, enable_post_sl_cooldown: !riskParams.enable_post_sl_cooldown})}
                style={{
                  width: "50px",
                  height: "26px",
                  borderRadius: "13px",
                  background: riskParams.enable_post_sl_cooldown ? "var(--primary)" : "rgba(255,255,255,0.1)",
                  border: "none",
                  position: "relative",
                  cursor: "pointer",
                  transition: "0.3s"
                }}
              >
                <div style={{
                  width: "20px",
                  height: "20px",
                  borderRadius: "10px",
                  background: "white",
                  position: "absolute",
                  top: "3px",
                  left: riskParams.enable_post_sl_cooldown ? "27px" : "3px",
                  transition: "0.3s"
                }} />
              </button>
            </div>
          </div>
        </div>

        {/* Primary Action */}
        <button
          onClick={saveRiskProfile}
          className="premium-btn hover-lift"
          style={{
            width: "100%",
            background: "var(--gradient-primary)",
            border: "none",
            color: "black",
            padding: "24px",
            borderRadius: "20px",
            fontWeight: "900",
            cursor: "pointer",
            fontSize: "16px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            boxShadow: "0 20px 40px rgba(0, 122, 255, 0.2)",
            marginBottom: "40px",
            textTransform: "uppercase",
            letterSpacing: "1px"
          }}
        >
          <RefreshCcw size={20} />
          Synchronize Risk Protocols
        </button>

        {/* Maintenance Section */}
        <div style={{ 
          marginTop: "20px", 
          padding: "32px", 
          background: "rgba(255,255,255,0.01)", 
          borderRadius: "24px", 
          border: "1px solid var(--divider)" 
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px" }}>
             <AlertTriangle size={18} color="#eb4d4b" />
             <h3 style={{ fontSize: "14px", fontWeight: "700", textTransform: "uppercase", letterSpacing: "1px" }}>System Maintenance</h3>
          </div>
          
          <div style={{ 
            display: "grid", 
            gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", 
            gap: "16px" 
          }}>
            <button
              onClick={resetRiskProfile}
              className="glass-panel hover-lift"
              style={{
                padding: "20px",
                borderRadius: "16px",
                border: "1px solid var(--border)",
                background: "transparent",
                color: "var(--text-main)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "8px",
                cursor: "pointer"
              }}
            >
              <RotateCcw size={20} color="var(--primary)" />
              <span style={{ fontSize: "12px", fontWeight: "700" }}>Restore Defaults</span>
              <span style={{ fontSize: "10px", color: "var(--text-sub)" }}>Reset to core standards</span>
            </button>

            <button
              onClick={clearRiskEvents}
              className="glass-panel hover-lift"
              style={{
                padding: "20px",
                borderRadius: "16px",
                border: "1px solid rgba(255, 69, 58, 0.1)",
                background: "rgba(255, 69, 58, 0.02)",
                color: "var(--loss)",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: "8px",
                cursor: "pointer"
              }}
            >
              <Trash2 size={20} color="var(--loss)" />
              <span style={{ fontSize: "12px", fontWeight: "700" }}>Purge Logs</span>
              <span style={{ fontSize: "10px", color: "var(--text-sub)" }}>Clear security events</span>
            </button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .premium-btn:active {
          transform: scale(0.98);
        }
      `}</style>
    </div>
  );
}

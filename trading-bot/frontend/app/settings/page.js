"use client";
import React, { useState, useMemo, useEffect } from "react";
import { useBot } from "../components/BotContext";
import { useAuth } from "../components/AuthContext";
import { useTheme } from "../components/ThemeContext";
import { useSearchSymbolsQuery } from "../lib/apiSlice";
import ConfidenceDropdown from "../components/ConfidenceDropdown";
import RRRatioDropdown from "../components/RRRatioDropdown";
import { Shield, Target, TrendingDown, Activity, Save, Zap, AlertTriangle, RotateCcw, Trash2, Clock, Globe, Cpu, Search, Plus, ChevronDown, BarChart3, TrendingUp } from "lucide-react";
import { useMediaQuery } from "../lib/useMediaQuery";

// Premium Icon Mapping for High-End Visualization
const AssetIcon = ({ symbol, size = 18 }) => {
  const s = symbol.toUpperCase();
  if (s.includes("BTC")) return <Zap size={size} color="#f7931a" />;
  if (s.includes("ETH")) return <Activity size={size} color="#627eea" />;
  if (s.includes("SOL")) return <TrendingUp size={size} color="#14f195" />;
  if (s.includes("XAU") || s.includes("GOLD")) return <BarChart3 size={size} color="#ffcc00" />;
  if (s.includes("USD")) return <Globe size={size} color="#007aff" />;
  if (s.includes("EUR")) return <Globe size={size} color="#003399" />;
  if (s.includes("GBP")) return <Globe size={size} color="#c8102e" />;
  return <Target size={size} color="var(--text-sub)" />;
};

function TabButton({ active, onClick, label, icon, isMobile }) {
  const { theme } = useTheme();
  return (
    <button
      onClick={onClick}
      style={{
        flex: 1, padding: isMobile ? "10px 4px" : "12px", borderRadius: "10px", border: "none",
        background: active ? "var(--primary)" : "transparent",
        color: active ? (theme === "dark" ? "#000" : "#fff") : "var(--text-secondary)",
        fontSize: isMobile ? "11px" : "13px", fontWeight: "700", cursor: "pointer",
        display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
        transition: "all 0.3s ease",
        boxShadow: active ? "0 4px 12px rgba(0,122,255,0.15)" : "none",
        minWidth: 0,
        overflow: "hidden"
      }}
    >
      {React.cloneElement(icon, { size: isMobile ? 12 : 14, color: active ? (theme === "dark" ? "#000" : "#fff") : "currentColor" })}
      <span style={{ display: isMobile && !active ? "none" : "inline", whiteSpace: "nowrap" }}>{label}</span>
    </button>
  );
}

export default function Settings() {
  const { user } = useAuth();
  const { theme } = useTheme();
  const {
    riskParams,
    setRiskParams,
    saveRiskProfile,
    resetTradeHistory,
    resetRiskProfile,
    selectedSession,
    updateBotSettings,
    aiConfidenceThreshold,
    engineConfig, 
    strategySettings, 
    updateStrategySetting, 
    updateSymbolManualVolume, 
    activeSymbols,
    symbolData,
  } = useBot();
  const isMobile = useMediaQuery("(max-width: 768px)");

  const [activeTab, setActiveTab] = useState("risk"); // risk | assets | volume
  const [selectedPair, setSelectedPair] = useState(activeSymbols[0] || "");
  const [isSelectorOpen, setIsSelectorOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const { data: searchResults, isFetching: isSearching } = useSearchSymbolsQuery(debouncedSearch, {
    skip: activeTab !== "assets"
  });

  if (!user) return null;

  const symbolInfo = engineConfig[selectedPair] || {};
  const currentPrice = symbolInfo.last_price || (symbolData[selectedPair]?.chart?.slice(-1)[0]?.close) || 0;
  const manualVolume = symbolInfo.manual_volume || 0.01;

  const toggleSymbol = (sym) => {
    let newSymbols;
    if (activeSymbols.includes(sym)) {
      if (activeSymbols.length <= 1) return;
      newSymbols = activeSymbols.filter(s => s !== sym);
    } else {
      if (activeSymbols.length >= 8) return;
      newSymbols = [...activeSymbols, sym];
      setSearchQuery("");
    }
    updateBotSettings(newSymbols, selectedTF, null, null);
  };

  const getCategorizedResults = () => {
    if (!searchResults) return {};
    const groups = {
      FOREX: [],
      METALS: [],
      CRYPTO: [],
      INDICES: [],
      OTHER: []
    };

    searchResults.forEach(s => {
      const name = s.name.toUpperCase();
      const path = (s.path || "").toUpperCase();
      
      if (name.includes("BTC") || name.includes("ETH") || name.includes("SOL") || name.includes("XRP") || path.includes("CRYPTO")) {
        groups.CRYPTO.push(s);
      } else if (name.includes("XAU") || name.includes("XAG") || name.includes("GOLD") || name.includes("SILVER") || path.includes("METAL")) {
        groups.METALS.push(s);
      } else if (name.includes("30") || name.includes("100") || name.includes("500") || name.includes("GER") || name.includes("NAS") || path.includes("INDEX")) {
        groups.INDICES.push(s);
      } else if (name.length <= 7 && (name.includes("USD") || name.includes("EUR") || name.includes("GBP") || name.includes("JPY"))) {
        groups.FOREX.push(s);
      } else {
        groups.OTHER.push(s);
      }
    });

    return groups;
  };

  const categorized = getCategorizedResults();

  return (
    <div className="animate-fade-in" style={{ padding: isMobile ? "0" : "0 20px" }}>
      <div style={{ marginBottom: isMobile ? "20px" : "30px", display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
        <div>
          <h1 style={{ fontSize: isMobile ? "22px" : "24px", fontWeight: "900", marginBottom: "6px" }}>
            Engine <span className="text-gradient">Configurations</span>
          </h1>
          <p style={{ color: "var(--text-sub)", fontSize: isMobile ? "12px" : "13px", fontWeight: "500" }}>
            Advanced parameters for the Alpha Institutional Core.
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{ 
        display: "flex", background: "var(--divider)", borderRadius: "16px", padding: "4px", 
        marginBottom: isMobile ? "20px" : "32px", border: "1px solid var(--border)", gap: "4px", 
        maxWidth: isMobile ? "100%" : "800px",
        overflowX: isMobile ? "auto" : "visible"
      }}>
        <TabButton active={activeTab === "risk"} onClick={() => setActiveTab("risk")} label="Risk" icon={<Shield size={16} />} isMobile={isMobile} />
        <TabButton active={activeTab === "management"} onClick={() => setActiveTab("management")} label="Trade" icon={<Activity size={16} />} isMobile={isMobile} />
        <TabButton active={activeTab === "assets"} onClick={() => setActiveTab("assets")} label="Assets" icon={<Globe size={16} />} isMobile={isMobile} />
        <TabButton active={activeTab === "volume"} onClick={() => setActiveTab("volume")} label="Volume" icon={<Target size={16} />} isMobile={isMobile} />
      </div>

      <div style={{ minHeight: "600px" }}>
        {activeTab === "risk" && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fit, minmax(400px, 1fr))",
              gap: isMobile ? "15px" : "25px",
            }}
          >
            {/* --- INSTITUTIONAL RISK PROFILE --- */}
            <div className="glass-panel" style={{ padding: "30px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "25px" }}>
                <div style={{ background: "rgba(0, 255, 189, 0.1)", border: "1px solid rgba(0, 255, 189, 0.2)", padding: "10px", borderRadius: "10px" }}>
                  <Shield size={20} color="var(--profit)" />
                </div>
                <div>
                  <h3 style={{ fontSize: "15px", fontWeight: "600" }}>Risk Mitigation Profile</h3>
                  <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Capital preservation and trade execution limits</p>
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                {/* Risk Per Trade */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
                    <span style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-main)" }}>Risk Per Trade (%)</span>
                    <span style={{ fontSize: "13px", fontWeight: "700", color: "var(--profit)" }}>{riskParams.risk_per_trade}%</span>
                  </div>
                  <input
                    type="range" min="0.1" max="5.0" step="0.1"
                    value={riskParams.risk_per_trade}
                    onChange={(e) => setRiskParams({ ...riskParams, risk_per_trade: e.target.value })}
                    style={{ width: "100%", accentColor: "var(--profit)" }}
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "15px" }}>
                  {/* Max Open Trades */}
                  <div className="inner-panel" style={{ padding: "15px", background: "rgba(255,255,255,0.02)", borderRadius: "12px", border: "1px solid var(--glass-border)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                      <Target size={14} color="var(--primary)" />
                      <span style={{ fontSize: "11px", fontWeight: "700", letterSpacing: "0.5px" }}>MAX OPEN TRADES</span>
                    </div>
                    <input
                      type="number" min="1" max="10"
                      value={riskParams.max_trades}
                      onChange={(e) => setRiskParams({ ...riskParams, max_trades: e.target.value })}
                      style={{ width: "100%", background: "transparent", border: "none", borderBottom: "1px solid var(--glass-border)", fontSize: "18px", fontWeight: "700", color: "var(--text-main)" }}
                    />
                  </div>

                  {/* Trades Per Day */}
                  <div className="inner-panel" style={{ padding: "15px", background: "rgba(255,255,255,0.02)", borderRadius: "12px", border: "1px solid var(--glass-border)" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                      <Activity size={14} color="var(--primary)" />
                      <span style={{ fontSize: "11px", fontWeight: "700", letterSpacing: "0.5px" }}>DAILY TRADE LIMIT</span>
                    </div>
                    <input
                      type="number" min="1" max="50"
                      value={riskParams.max_daily_trades}
                      onChange={(e) => setRiskParams({ ...riskParams, max_daily_trades: e.target.value })}
                      style={{ width: "100%", background: "transparent", border: "none", borderBottom: "1px solid var(--glass-border)", fontSize: "18px", fontWeight: "700", color: "var(--text-main)" }}
                    />
                  </div>
                </div>

                {/* Daily Loss Limit */}
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px" }}>
                    <span style={{ fontSize: "13px", fontWeight: "700", color: "var(--text-main)" }}>Daily Drawdown Limit (%)</span>
                    <span style={{ fontSize: "13px", fontWeight: "700", color: "var(--loss)" }}>{riskParams.daily_loss}%</span>
                  </div>
                  <input
                    type="range" min="1" max="30" step="1"
                    value={riskParams.daily_loss}
                    onChange={(e) => setRiskParams({ ...riskParams, daily_loss: e.target.value })}
                    style={{ width: "100%", accentColor: "var(--loss)" }}
                  />
                </div>

                {/* Risk Reward Ratio */}
                <div>
                  <h4 style={{ fontSize: "12px", fontWeight: "600", marginBottom: "10px", color: "var(--text-sub)", letterSpacing: "1px" }}>TARGET RISK:REWARD</h4>
                  <RRRatioDropdown
                    value={riskParams.risk_reward_ratio}
                    onChange={(val) => setRiskParams({ ...riskParams, risk_reward_ratio: val })}
                  />
                </div>

                <button onClick={saveRiskProfile} className="premium-btn" style={{ marginTop: "10px", width: "100%", padding: "15px", borderRadius: "12px", display: "flex", justifyContent: "center", alignItems: "center", gap: "10px" }}>
                  <Save size={18} /> SAVE RISK PROFILE
                </button>
              </div>
            </div>

            {/* --- AI DETECTION ENGINE --- */}
            <div style={{ display: "flex", flexDirection: "column", gap: "25px" }}>
              <div className="glass-panel" style={{ padding: "30px", flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "25px" }}>
                  <div style={{ background: "rgba(91, 134, 229, 0.1)", border: "1px solid rgba(91, 134, 229, 0.2)", padding: "10px", borderRadius: "10px" }}>
                    <Zap size={20} color="#5b86e5" />
                  </div>
                  <div>
                    <h3 style={{ fontSize: "15px", fontWeight: "600" }}>AI Detection Engine</h3>
                    <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Sentiment thresholds and script sensitivity</p>
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "25px" }}>
                  <div>
                    <h4 style={{ fontSize: "12px", fontWeight: "600", marginBottom: "15px", color: "var(--text-sub)", letterSpacing: "1px" }}>AI MODEL CONFIDENCE</h4>
                    <ConfidenceDropdown
                      valuePct={Math.round((aiConfidenceThreshold || 0.48) * 100)}
                      minPct={15} maxPct={100}
                      onChangePct={(pct) => {
                        const v = Math.min(1, Math.max(0.15, pct / 100));
                        updateBotSettings(null, null, null, v);
                      }}
                    />
                  </div>

                  <div>
                     <h4 style={{ fontSize: "12px", fontWeight: "600", marginBottom: "15px", color: "var(--text-sub)", letterSpacing: "1px" }}>STRATEGY SYNC</h4>
                     <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                        {Object.entries(strategySettings || {}).map(([id, config]) => (
                          <div key={id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px", borderRadius: "14px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border)" }}>
                             <span style={{ fontSize: "14px", fontWeight: "700" }}>{config.name || id}</span>
                             <div 
                              onClick={() => updateStrategySetting(id, { enabled: !config.enabled })}
                              style={{ width: "44px", height: "22px", background: config.enabled ? "var(--profit)" : "var(--divider)", borderRadius: "11px", position: "relative", cursor: "pointer", transition: "0.3s" }}
                             >
                                <div style={{ width: "16px", height: "16px", background: "white", borderRadius: "50%", position: "absolute", top: "3px", left: config.enabled ? "25px" : "3px", transition: "0.3s" }} />
                             </div>
                          </div>
                        ))}
                     </div>
                  </div>
                </div>
              </div>

              {/* --- INSTITUTIONAL TRADING SESSIONS --- */}
              <div className="glass-panel" style={{ padding: "30px" }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <Clock size={20} color="#9b59b6" />
                      <h3 style={{ fontSize: "15px", fontWeight: "600" }}>Market Volatility Windows</h3>
                    </div>
                    <div style={{ 
                      padding: "4px 12px", borderRadius: "8px", background: "rgba(155, 89, 182, 0.1)", 
                      border: "1px solid rgba(155, 89, 182, 0.2)", color: "#9b59b6", 
                      fontSize: "12px", fontWeight: "700", fontFamily: "monospace" 
                    }}>
                      {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
                    </div>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                    {["ALL", "LONDON", "NEW YORK", "ASIAN"].map((sess) => (
                      <button
                        key={sess} onClick={() => updateBotSettings(null, null, sess)}
                        style={{
                          padding: "12px", borderRadius: "10px",
                          background: selectedSession === sess ? "var(--primary)" : "rgba(255,255,255,0.03)",
                          color: selectedSession === sess ? "black" : "white",
                          border: "1px solid var(--glass-border)", fontSize: "12px", fontWeight: "600", cursor: "pointer"
                        }}
                      >
                        {sess}
                      </button>
                    ))}
                  </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "management" && (
          <div className="glass-panel animate-slide-up" style={{ padding: "40px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "16px", marginBottom: "40px" }}>
              <div style={{ padding: "12px", background: "rgba(0,122,255,0.1)", borderRadius: "14px" }}>
                <Activity size={24} color="var(--primary)" />
              </div>
              <div>
                <h2 style={{ fontSize: "20px", fontWeight: "700" }}>Institutional Trade Management</h2>
                <p style={{ color: "var(--text-sub)", fontSize: "13px" }}>Configure partial profit-taking and progressive stop-loss migration.</p>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fit, minmax(400px, 1fr))", gap: isMobile ? "15px" : "40px" }}>
              {/* STAGED TP GLOBAL TOGGLE */}
              <div className="inner-panel" style={{ padding: "24px", background: "rgba(255,255,255,0.02)", borderRadius: "18px", border: "1px solid var(--border)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px" }}>
                  <div>
                    <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "4px" }}>Staged Partial Execution</h3>
                    <p style={{ fontSize: "12px", color: "var(--text-sub)" }}>Automatically close portions of a trade at milestones</p>
                  </div>
                  <div 
                    onClick={() => setRiskParams({...riskParams, partial_execution_enabled: !riskParams.partial_execution_enabled})}
                    style={{ 
                      width: "50px", height: "26px", borderRadius: "13px", cursor: "pointer", transition: "0.4s",
                      background: riskParams.partial_execution_enabled ? "var(--primary)" : "var(--divider)",
                      position: "relative"
                    }}
                  >
                    <div style={{ 
                      width: "20px", height: "20px", background: riskParams.partial_execution_enabled ? "black" : "white", borderRadius: "50%",
                      position: "absolute", top: "3px", left: riskParams.partial_execution_enabled ? "27px" : "3px", transition: "0.4s"
                    }} />
                  </div>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "30px", opacity: riskParams.partial_execution_enabled ? 1 : 0.4, pointerEvents: riskParams.partial_execution_enabled ? "all" : "none" }}>
                  {/* STAGE 1 */}
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "15px" }}>
                      <span style={{ fontSize: "14px", fontWeight: "600" }}>Stage 1 Trigger (Profit Progress)</span>
                      <span style={{ color: "var(--primary)", fontWeight: "700" }}>{riskParams.partial_stage_1_trigger}%</span>
                    </div>
                    <input 
                      type="range" min="10" max="90" step="5"
                      value={riskParams.partial_stage_1_trigger}
                      onChange={(e) => setRiskParams({...riskParams, partial_stage_1_trigger: parseInt(e.target.value)})}
                      className="premium-slider"
                      style={{ width: "100%" }}
                    />
                    <div style={{ marginTop: "12px", fontSize: "12px", color: "var(--text-sub)", display: "flex", justifyContent: "space-between" }}>
                      <span>Close Position: {riskParams.partial_stage_1_close_pct}%</span>
                      <div style={{ display: "flex", gap: "8px" }}>
                        {[25, 50, 75].map(v => (
                          <button 
                            key={v} onClick={() => setRiskParams({...riskParams, partial_stage_1_close_pct: v})}
                            style={{ padding: "4px 8px", borderRadius: "6px", border: "none", fontSize: "10px", fontWeight: "700", background: riskParams.partial_stage_1_close_pct === v ? "var(--primary)" : "var(--divider)", color: riskParams.partial_stage_1_close_pct === v ? "black" : "white", cursor: "pointer" }}
                          >
                            {v}%
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* STAGE 2 */}
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "15px" }}>
                      <span style={{ fontSize: "14px", fontWeight: "600" }}>Stage 2 Trigger (Profit Progress)</span>
                      <span style={{ color: "var(--primary)", fontWeight: "700" }}>{riskParams.partial_stage_2_trigger}%</span>
                    </div>
                    <input 
                      type="range" min="20" max="95" step="5"
                      value={riskParams.partial_stage_2_trigger}
                      onChange={(e) => setRiskParams({...riskParams, partial_stage_2_trigger: parseInt(e.target.value)})}
                      className="premium-slider"
                      style={{ width: "100%" }}
                    />
                    <div style={{ marginTop: "12px", fontSize: "12px", color: "var(--text-sub)", display: "flex", justifyContent: "space-between" }}>
                      <span>Close Position: {riskParams.partial_stage_2_close_pct}%</span>
                      <div style={{ display: "flex", gap: "8px" }}>
                        {[10, 25, 50].map(v => (
                          <button 
                            key={v} onClick={() => setRiskParams({...riskParams, partial_stage_2_close_pct: v})}
                            style={{ padding: "4px 8px", borderRadius: "6px", border: "none", fontSize: "10px", fontWeight: "700", background: riskParams.partial_stage_2_close_pct === v ? "var(--primary)" : "var(--divider)", color: riskParams.partial_stage_2_close_pct === v ? "black" : "white", cursor: "pointer" }}
                          >
                            {v}%
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                <button 
                  onClick={saveRiskProfile}
                  className="premium-btn" 
                  style={{ width: "100%", padding: "16px", borderRadius: "14px", marginTop: "40px", display: "flex", justifyContent: "center", alignItems: "center", gap: "10px" }}
                >
                  <Save size={18} /> SAVE MANAGEMENT PROTOCOL
                </button>
              </div>

              {/* VISUAL GUIDE */}
              <div style={{ padding: "24px", background: "rgba(0,122,255,0.03)", borderRadius: "18px", border: "1px dashed rgba(0,122,255,0.2)" }}>
                <h3 style={{ fontSize: "16px", fontWeight: "700", marginBottom: "20px" }}>Management Lifecycle</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
                  <div style={{ display: "flex", gap: "15px" }}>
                    <div style={{ width: "24px", height: "24px", borderRadius: "50%", background: "var(--primary)", color: "black", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: "800" }}>1</div>
                    <div>
                      <p style={{ fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Stage 1 Milestone reached ({riskParams.partial_stage_1_trigger}% to TP)</p>
                      <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "11px", color: "var(--text-sub)", lineHeight: "1.6" }}>
                        <li>Closes {riskParams.partial_stage_1_close_pct}% of open volume.</li>
                        <li>Moves SL to Entry + 10% move buffer to capture profit.</li>
                      </ul>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "15px" }}>
                    <div style={{ width: "24px", height: "24px", borderRadius: "50%", background: "var(--primary)", color: "black", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: "800" }}>2</div>
                    <div>
                      <p style={{ fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Stage 2 Milestone reached ({riskParams.partial_stage_2_trigger}% to TP)</p>
                      <ul style={{ margin: 0, paddingLeft: "18px", fontSize: "11px", color: "var(--text-sub)", lineHeight: "1.6" }}>
                        <li>Closes {riskParams.partial_stage_2_close_pct}% of original volume.</li>
                        <li>Moves SL to Stage 1 Trigger Price (locks in 60%+ move).</li>
                      </ul>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: "15px" }}>
                    <div style={{ width: "24px", height: "24px", borderRadius: "50%", background: "var(--divider)", color: "white", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: "800" }}>3</div>
                    <div>
                      <p style={{ fontSize: "13px", fontWeight: "600", marginBottom: "4px" }}>Final Target / ATR Trailing</p>
                      <p style={{ fontSize: "11px", color: "var(--text-sub)", lineHeight: "1.6" }}>Remaining {Math.max(0, 100 - riskParams.partial_stage_1_close_pct - riskParams.partial_stage_2_close_pct)}% hits full TP or is protected by 1.5x ATR trailing stop.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "assets" && (
           <div className="glass-panel" style={{ padding: isMobile ? "20px" : "40px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
                 <div style={{ position: "relative" }}>
                    <Search size={20} style={{ position: "absolute", left: "20px", top: "50%", transform: "translateY(-50%)", color: isSearching ? "var(--primary)" : "var(--text-sub)" }} />
                    <input 
                      type="text" placeholder="Search Markets (Forex, Crypto, Indices, Metals...)"
                      value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                      style={{
                        width: "100%", padding: isMobile ? "16px 16px 16px 48px" : "20px 20px 20px 56px", borderRadius: "18px",
                        background: "var(--divider)", border: "1px solid var(--border)",
                        color: "var(--text-main)", fontSize: isMobile ? "14px" : "16px", outline: "none"
                      }}
                    />
                 </div>

                 <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '40px' }}>
                    {Object.entries(categorized).map(([cat, syms]) => {
                      if (syms.length === 0) return null;
                      return (
                        <div key={cat}>
                          <div style={{ fontSize: "11px", fontWeight: "600", color: "var(--text-sub)", textTransform: "uppercase", letterSpacing: "2.5px", marginBottom: "20px", display: 'flex', alignItems: 'center', gap: '16px' }}>
                             <span style={{ color: 'var(--primary)', whiteSpace: 'nowrap' }}>{cat}</span>
                             <div style={{ height: '1px', flex: 1, background: 'linear-gradient(90deg, var(--divider), transparent)' }}></div>
                          </div>
                          <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fill, minmax(300px, 1fr))", gap: "12px" }}>
                            {syms.map(s => {
                              const isActive = activeSymbols.includes(s.name);
                              return (
                                <div 
                                  key={s.name} onClick={() => toggleSymbol(s.name)}
                                  style={{
                                    padding: "20px", borderRadius: "20px", border: "1px solid",
                                    background: isActive ? "var(--primary-light)" : "var(--divider)",
                                    borderColor: isActive ? "var(--primary)" : "var(--border)",
                                    cursor: "pointer", display: "flex", alignItems: "center", gap: "20px", position: 'relative'
                                  }}
                                  className="hover-lift"
                                >
                                   <AssetIcon symbol={s.name} size={22} />
                                   <div style={{ flex: 1 }}>
                                      <div style={{ fontWeight: "700", fontSize: "16px", color: "var(--text-main)" }}>{s.name}</div>
                                      <div style={{ fontSize: "11px", color: "var(--text-sub)" }}>{s.description || "Institutional Asset"}</div>
                                   </div>
                                   {isActive ? <Trash2 size={18} color="var(--primary)" /> : <Plus size={18} color="var(--text-sub)" />}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                 </div>
              </div>
           </div>
        )}

        {activeTab === "volume" && (
           <div className="glass-panel" style={{ padding: isMobile ? "20px" : "40px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
                 <div style={{ position: "relative", maxWidth: "400px" }}>
                    <div 
                      onClick={() => setIsSelectorOpen(!isSelectorOpen)}
                      style={{
                        background: "var(--divider)", border: "1px solid var(--border)", padding: "18px 24px",
                        borderRadius: "18px", display: "flex", alignItems: "center", justifyContent: "space-between", cursor: "pointer"
                      }}
                      className="hover-lift"
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                        <AssetIcon symbol={selectedPair} size={24} />
                        <span style={{ fontSize: "18px", fontWeight: "700", color: "var(--text-main)" }}>{selectedPair}</span>
                      </div>
                      <ChevronDown size={22} style={{ transform: isSelectorOpen ? "rotate(180deg)" : "rotate(0)", transition: "0.3s" }} />
                    </div>
                    {isSelectorOpen && (
                      <div style={{
                        position: "absolute", top: "110%", left: 0, right: 0, zIndex: 100,
                        background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "20px",
                        padding: "10px", boxShadow: "0 40px 80px rgba(0,0,0,0.4)"
                      }}>
                        {activeSymbols.map(sym => (
                          <div 
                            key={sym} onClick={() => { setSelectedPair(sym); setIsSelectorOpen(false); }}
                            style={{ padding: "16px 20px", borderRadius: "12px", cursor: "pointer", background: selectedPair === sym ? "rgba(0,122,255,0.15)" : "transparent", color: selectedPair === sym ? "var(--primary)" : "var(--text-sub)", fontWeight: "600" }}
                            className="hover-lift"
                          >
                            {sym}
                          </div>
                        ))}
                      </div>
                    )}
                 </div>

                                   <div style={{ background: "rgba(255,255,255,0.01)", borderRadius: "20px", border: "1px solid var(--border)", padding: isMobile ? "20px" : "28px" }}>
                    <div style={{ 
                      display: "grid", 
                      gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr 1fr", 
                      gap: isMobile ? "12px" : "20px", 
                      marginBottom: "28px", 
                      paddingBottom: "20px", 
                      borderBottom: "1px solid var(--divider)" 
                    }}>
                       <div style={{ display: isMobile ? 'flex' : 'block', justifyContent:'space-between', alignItems:'center'}}>
                         <span style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-sub)", textTransform: "uppercase", letterSpacing: "1px" }}>Price</span>
                         <div style={{ fontSize: isMobile ? "18px" : "24px", fontWeight: "600", color: "var(--text-main)", marginTop: isMobile ? 0 : "4px" }}>${currentPrice.toLocaleString()}</div>
                       </div>
                       <div style={{ 
                         textAlign: isMobile ? "left" : "center", 
                         borderLeft: isMobile ? "none" : "1px solid var(--divider)", 
                         borderRight: isMobile ? "none" : "1px solid var(--divider)",
                         display: isMobile ? 'flex' : 'block', 
                         justifyContent:'space-between', 
                         alignItems:'center',
                         padding: isMobile ? '8px 0' : '0'
                       }}>
                         <span style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-sub)", textTransform: "uppercase", letterSpacing: "1px" }}>Value</span>
                         <div style={{ fontSize: isMobile ? "16px" : "16px", fontWeight: "600", color: "var(--text-sub)", marginTop: isMobile ? 0 : "4px" }}>
                            ${(manualVolume * (symbolInfo.contract_size || 100000) * currentPrice).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                         </div>
                       </div>
                       <div style={{ textAlign: isMobile ? "left" : "right", display: isMobile ? 'flex' : 'block', justifyContent:'space-between', alignItems:'center' }}>
                         <span style={{ fontSize: "10px", fontWeight: "700", color: "#ff7675", textTransform: "uppercase", letterSpacing: "1px" }}>Risk (20P)</span>
                         <div style={{ fontSize: isMobile ? "18px" : "22px", fontWeight: "600", color: "#eb4d4b", marginTop: isMobile ? 0 : "4px" }}>
                            ${(manualVolume * (symbolInfo.contract_size || 100000) * (symbolInfo.point * 200 || 0.002)).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                         </div>
                       </div>
                    </div>
                    <label style={{ display: "block", fontSize: "10px", fontWeight: "700", color: "var(--text-sub)", marginBottom: "16px", textTransform: "uppercase", letterSpacing: "1px" }}>Execution Lot Precision</label>
                    <div style={{ display: "grid", gridTemplateColumns: isMobile ? "repeat(3, 1fr)" : "repeat(auto-fill, minmax(110px, 1fr))", gap: "10px" }}>
                      {[0.01, 0.05, 0.1, 0.25, 0.5, 1.0].map(vol => {
                        const isSelected = Math.abs(parseFloat(manualVolume) - vol) < 0.0001;
                        return (
                          <button 
                            key={vol} onClick={() => updateSymbolManualVolume(selectedPair, vol)}
                            style={{
                              padding: "16px", borderRadius: "14px", border: "1px solid",
                              background: isSelected ? "var(--primary)" : "var(--divider)",
                              borderColor: isSelected ? "var(--primary)" : "var(--border)",
                              color: isSelected ? "black" : "var(--text-main)",
                              transition: "all 0.2s ease"
                            }}
                            className="hover-lift"
                          >
                             <div style={{ fontSize: "18px", fontWeight: "600" }}>{vol}</div>
                             <div style={{ fontSize: "10px", opacity: 0.6, marginTop: "2px" }}>LOTS</div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
              </div>
           </div>
        )}
      </div>

      {/* --- MAINTENANCE --- */}
      <div className="glass-panel" style={{ marginTop: "40px", padding: "30px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "25px" }}>
          <AlertTriangle size={20} color="#eb4d4b" />
          <h3 style={{ fontSize: "16px", fontWeight: "600" }}>Maintenance & Recovery</h3>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: isMobile ? "1fr" : "repeat(auto-fit, minmax(300px, 1fr))", gap: isMobile ? "12px" : "20px" }}>
          <button onClick={resetRiskProfile} className="inner-panel" style={{ display: "flex", alignItems: "center", gap: "15px", padding: "20px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--glass-border)", borderRadius: "12px", cursor: "pointer", transition: "0.3s" }}>
            <RotateCcw size={20} color="#3498db" />
            <div>
              <p style={{ fontSize: "14px", fontWeight: "600", color: "white" }}>Restore Risk Defaults</p>
              <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Reset to strict 1% risk & 5-trade limit</p>
            </div>
          </button>
          <button onClick={resetTradeHistory} className="inner-panel" style={{ display: "flex", alignItems: "center", gap: "15px", padding: "20px", background: "rgba(235, 77, 75, 0.05)", border: "1px solid rgba(235, 77, 75, 0.2)", borderRadius: "12px", cursor: "pointer", transition: "0.3s" }}>
            <Trash2 size={20} color="#eb4d4b" />
            <div>
              <p style={{ fontSize: "14px", fontWeight: "600", color: "white" }}>Reset Trade History</p>
              <p style={{ fontSize: "11px", color: "var(--text-sub)" }}>Permanently wipe all past trade logs</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

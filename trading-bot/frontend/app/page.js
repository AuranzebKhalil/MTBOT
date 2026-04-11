"use client";
import React, { useState, useMemo } from "react";
import {
  ShieldCheck,
  Activity,
  TrendingUp,
  Award,
  Shield,
  Zap,
  X,
  Terminal as TerminalIcon,
  Maximize2,
} from "lucide-react";
import QuantGrid from "./components/QuantGrid";
import AuralithChart from "./components/AuralithChart";
import { useBot } from "./components/BotContext";
import { useAuth } from "./components/AuthContext";
import FilterStatusPanel from "./components/FilterStatusPanel";
import { useMediaQuery } from "./lib/useMediaQuery";
import AssetIcon from "./components/AssetIcon";

export default function Home() {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const isTablet = useMediaQuery("(max-width: 1024px)");
  const isSmallMobile = useMediaQuery("(max-width: 600px)");
  const { user } = useAuth();
  const { botStatus, history } = useBot();

  const [showTerminalPopup, setShowTerminalPopup] = useState(false);
  const [popupSymbol, setPopupSymbol] = useState(null);

  const openTerminal = (symbol) => {
    setPopupSymbol(symbol);
    setShowTerminalPopup(true);
  };

  const [expandedLogs, setExpandedLogs] = useState(null); // { title, logs }

  // --- Performance Calculations ---
  const metrics = useMemo(() => {
    const closed = history.filter(
      (t) => t.profit !== undefined || t.pnl !== undefined,
    );
    if (closed.length === 0)
      return {
        winRate: "0.0",
        expectancy: "0.00",
        profitFactor: "0.00",
        totalTrades: 0,
      };

    const wins = closed.filter((t) => (t.profit || t.pnl || 0) > 0);
    const totalProfit = closed.reduce(
      (acc, t) => acc + (t.profit || t.pnl || 0),
      0,
    );

    const grossProfit = closed
      .filter((t) => (t.profit || t.pnl || 0) > 0)
      .reduce((acc, t) => acc + (t.profit || t.pnl || 0), 0);
    const grossLoss = Math.abs(
      closed
        .filter((t) => (t.profit || t.pnl || 0) < 0)
        .reduce((acc, t) => acc + (t.profit || t.pnl || 0), 0),
    );

    return {
      winRate: ((wins.length / closed.length) * 100).toFixed(1),
      expectancy: (totalProfit / closed.length).toFixed(2),
      profitFactor:
        grossLoss === 0
          ? grossProfit > 0
            ? "9.99"
            : "0.00"
          : (grossProfit / grossLoss).toFixed(2),
      totalTrades: closed.length,
    };
  }, [history]);

  if (!user) return null;

  return (
    <>
      <div
        className="fade-in"
        style={{
          display: "flex",
          flexDirection: "column",
          height: "auto",
          minHeight: "100%",
          overflowX: "hidden",
          maxWidth: "100%",
        }}
      >
        {/* 5-SEGMENT PERFORMANCE STRIP */}
        <div
          className="stats-strip"
          style={{
            display: "flex",
            flexDirection: isTablet ? "column" : "row",
            background: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-md)",
            marginBottom: isMobile ? "24px" : "32px",
            overflow: "hidden",
            boxShadow: "0 12px 40px rgba(0,0,0,0.2)",
          }}
        >
          <div
            style={{
              display: "grid",
              gridTemplateColumns: isSmallMobile
                ? "1fr"
                : isTablet
                  ? "repeat(2, 1fr)"
                  : "repeat(4, 1fr)",
              flex: isMobile ? "none" : 4,
              width: isMobile ? "100%" : "auto",
            }}
          >
            <MetricSegment
              icon={<TrendingUp size={18} />}
              iconClass="icon-green"
              label="Win Rate"
              value={`${metrics.winRate}%`}
              isMobile={isMobile}
            />
            <MetricSegment
              icon={<Activity size={18} />}
              iconClass="icon-blue"
              label="Expectancy"
              value={`$${metrics.expectancy}`}
              isMobile={isMobile}
            />
            <MetricSegment
              icon={<Award size={18} />}
              iconClass="icon-purple"
              label="Profit Factor"
              value={metrics.profitFactor}
              isMobile={isMobile}
            />
            <MetricSegment
              icon={<Shield size={18} />}
              iconClass="icon-green"
              label="Total Volume"
              value={metrics.totalTrades}
              isMobile={isMobile}
            />
          </div>

          <div
            style={{
              flex: isMobile ? "none" : 1.2,
              padding: isMobile ? "24px" : "20px 28px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              background: "rgba(255,255,255,0.01)",
              borderTop: isTablet ? "1px solid var(--divider)" : "none",
              borderLeft: isTablet ? "none" : "1px solid var(--divider)",
              textAlign: isTablet ? "center" : "left",
            }}
          >
            <span
              style={{
                fontSize: "10px",
                fontWeight: "600",
                color: "var(--text-secondary)",
                textTransform: "uppercase",
                letterSpacing: "1.2px",
              }}
            >
              Account Equity
            </span>
            <span
              style={{
                fontSize: isMobile ? "32px" : "24px",
                fontWeight: "800",
                color: "var(--text-main)",
                marginTop: "2px",
                letterSpacing: "-0.5px",
              }}
            >
              $
              {botStatus?.equity?.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              }) || "0.00"}
            </span>
          </div>
        </div>

        {/* RISK FILTERS PANEL */}
        <FilterStatusPanel />

        {/* CHART GRID AREA */}
        <div style={{ flex: 1, minHeight: 0 }}>
          <QuantGrid onOpenTerminal={openTerminal} />
        </div>
      </div>

      {/* FULL-SCREEN TERMINAL OVERLAY */}
      {showTerminalPopup && (
        <div
          className="fade-in"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            zIndex: 9999,
            background: "var(--background)",
            backdropFilter: "blur(60px)",
            padding: isMobile ? "16px" : "40px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "flex-start",
            overflowY: "auto",
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "1600px",
              height: isMobile ? "auto" : "90vh",
              display: "flex",
              flexDirection: "column",
              gap: isMobile ? "24px" : "0",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: isMobile ? "0px" : "40px",
                gap: "16px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: isMobile ? "12px" : "24px",
                }}
              >
                <div
                  style={{
                    width: isMobile ? "40px" : "56px",
                    height: isMobile ? "40px" : "56px",
                    // background:
                    //   "linear-gradient(135deg, var(--primary) 0%, #00f2ff 100%)",
                    borderRadius: isMobile ? "12px" : "18px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    // boxShadow: "0 0 30px rgba(0, 122, 255, 0.3)",
                    flexShrink: 0,
                  }}
                >
                  <AssetIcon symbol={popupSymbol} size={isMobile ? 24 : 36} />
                </div>
                <div>
                  <h2
                    style={{
                      fontSize: isMobile ? "20px" : "36px",
                      fontWeight: "800",
                      color: "var(--text-main)",
                      letterSpacing: "-1.2px",
                      margin: 0,
                      lineHeight: 1,
                    }}
                  >
                    <span style={{ color: "var(--accent-yellow)" }}>
                      {popupSymbol}
                    </span>{" "}
                    {!isMobile && (
                      <span style={{ color: "var(--text-main)" }}>
                        QUANT TERMINAL
                      </span>
                    )}
                  </h2>
                  {!isMobile && (
                    <p
                      style={{
                        color: "var(--text-secondary)",
                        fontSize: "12px",
                        marginTop: "6px",
                        fontWeight: "500",
                        opacity: 0.7,
                        letterSpacing: "0.5px",
                        textTransform: "uppercase",
                      }}
                    >
                      Deep liquidity execution & neural network synchronization
                      active
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => setShowTerminalPopup(false)}
                style={{
                  background: "rgba(255,255,255,0.03)",
                  border: "1px solid var(--border)",
                  color: "var(--text-main)",
                  width: isMobile ? "40px" : "56px",
                  height: isMobile ? "40px" : "56px",
                  borderRadius: isMobile ? "12px" : "16px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  boxShadow: "var(--shadow-glow)",
                  transition: "all 0.2s ease",
                  flexShrink: 0,
                }}
                className="hover-lift"
              >
                <X size={isMobile ? 18 : 24} />
              </button>
            </div>

            <div
              style={{
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                gap: isMobile ? "24px" : "40px",
                flex: isMobile ? "none" : 1,
                minHeight: 0,
              }}
            >
              <div
                style={{
                  flex: isMobile ? "none" : 2.8,
                  height: isMobile ? "300px" : "auto",
                  background: "var(--background)",
                  borderRadius: isMobile ? "20px" : "32px",
                  border: "1px solid var(--border)",
                  position: "relative",
                  overflow: "hidden",
                  boxShadow: "var(--shadow-glow)",
                }}
              >
                <AuralithChart symbol={popupSymbol} />
              </div>
              <div
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  gap: isMobile ? "16px" : "32px",
                  minHeight: isMobile ? "400px" : "auto",
                }}
              >
                <TerminalBox
                  title="Execution Stream"
                  icon={<Zap size={16} />}
                  logs={botStatus.logs?.filter((l) => !l.includes("[HEALTH]"))}
                  onExpand={() =>
                    setExpandedLogs({
                      title: "Execution Stream",
                      logs: botStatus.logs?.filter(
                        (l) => !l.includes("[HEALTH]"),
                      ),
                    })
                  }
                />
                <TerminalBox
                  title="Core Intelligence"
                  icon={<ShieldCheck size={16} />}
                  logs={botStatus.logs?.filter((l) => l.includes("[HEALTH]"))}
                  onExpand={() =>
                    setExpandedLogs({
                      title: "Core Intelligence",
                      logs: botStatus.logs?.filter((l) =>
                        l.includes("[HEALTH]"),
                      ),
                    })
                  }
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* EXPANDED LOGS POPUP */}
      {expandedLogs && (
        <div
          className="fade-in"
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            zIndex: 10000,
            background: "rgba(5, 7, 10, 0.95)",
            backdropFilter: "blur(20px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: isMobile ? "0" : "60px",
          }}
        >
          <div
            className="glass-panel"
            style={{
              width: "100%",
              maxWidth: "1200px",
              height: isMobile ? "100%" : "80vh",
              display: "flex",
              flexDirection: "column",
              padding: isMobile ? "24px" : "40px",
              position: "relative",
              borderRadius: isMobile ? "0" : "32px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: isMobile ? "24px" : "32px",
              }}
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: "16px" }}
              >
                <div
                  style={{
                    padding: isMobile ? "8px" : "12px",
                    background: "var(--primary-light)",
                    borderRadius: "12px",
                    color: "var(--primary)",
                  }}
                >
                  <TerminalIcon size={isMobile ? 18 : 24} />
                </div>
                <h3
                  style={{
                    fontSize: isMobile ? "18px" : "28px",
                    fontWeight: "800",
                    color: "var(--text-main)",
                    letterSpacing: "-0.5px",
                  }}
                >
                  {expandedLogs.title}{" "}
                  {!isMobile && (
                    <span style={{ opacity: 0.5 }}>System Logs</span>
                  )}
                </h3>
              </div>
              <button
                onClick={() => setExpandedLogs(null)}
                style={{
                  background: "var(--divider)",
                  border: "1px solid var(--border)",
                  color: "var(--text-main)",
                  width: isMobile ? "38px" : "48px",
                  height: isMobile ? "38px" : "48px",
                  borderRadius: "12px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
                className="hover-lift"
              >
                <X size={18} />
              </button>
            </div>

            <div
              className="custom-scrollbar"
              style={{
                flex: 1,
                overflowY: "auto",
                background: "rgba(0,0,0,0.2)",
                borderRadius: "16px",
                padding: isMobile ? "16px" : "24px",
                fontFamily: "var(--font-mono)",
                fontSize: isMobile ? "12px" : "14px",
                lineHeight: 1.8,
                border: "1px solid var(--divider)",
              }}
            >
              {expandedLogs.logs?.length > 0 ? (
                expandedLogs.logs
                  .slice()
                  .reverse()
                  .map((log, i) => (
                    <div
                      key={i}
                      style={{
                        padding: "8px 0",
                        borderBottom: "1px solid var(--divider)",
                        display: "flex",
                        flexDirection: isMobile ? "column" : "row",
                        gap: isMobile ? "4px" : "24px",
                      }}
                    >
                      <span
                        style={{
                          color: "var(--primary)",
                          fontWeight: "700",
                          opacity: 0.8,
                          minWidth: isMobile ? "auto" : "120px",
                          fontSize: isMobile ? "10px" : "inherit",
                        }}
                      >
                        {log.split(" - ")[0]}
                      </span>
                      <span
                        style={{
                          color: "var(--text-main)",
                          wordBreak: "break-word",
                        }}
                      >
                        {log.split(" - ").slice(1).join(" - ")}
                      </span>
                    </div>
                  ))
              ) : (
                <div
                  style={{
                    textAlign: "center",
                    padding: "100px",
                    opacity: 0.3,
                    fontWeight: "600",
                  }}
                >
                  NO DATA STREAM AVAILABLE
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function MetricSegment({ icon, iconClass, label, value, isMobile }) {
  return (
    <div
      style={{
        flex: 1,
        padding: isMobile ? "16px" : "20px 24px",
        display: "flex",
        alignItems: "center",
        gap: isMobile ? "14px" : "18px",
        borderRight: isMobile ? "none" : "1px solid var(--divider)",
        borderBottom: isMobile ? "1px solid var(--divider)" : "none",
        position: "relative",
      }}
    >
      <div
        style={{
          width: isMobile ? "38px" : "44px",
          height: isMobile ? "38px" : "44px",
          borderRadius: "10px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background:
            iconClass === "icon-green"
              ? "rgba(50, 215, 75, 0.08)"
              : iconClass === "icon-blue"
                ? "rgba(0, 122, 255, 0.08)"
                : "rgba(191, 90, 242, 0.08)",
          color:
            iconClass === "icon-green"
              ? "var(--success)"
              : iconClass === "icon-blue"
                ? "var(--primary)"
                : "var(--accent-purple)",
          flexShrink: 0,
        }}
      >
        {React.cloneElement(icon, { size: isMobile ? 16 : 18 })}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
        <span
          style={{
            fontSize: "9px",
            fontWeight: "700",
            color: "var(--text-secondary)",
            textTransform: "uppercase",
            letterSpacing: "1.2px",
            lineHeight: 1,
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontSize: isMobile ? "20px" : "24px",
            fontWeight: "700",
            color: "var(--text-main)",
            letterSpacing: "-0.5px",
            lineHeight: 1,
          }}
        >
          {value}
        </span>
      </div>
    </div>
  );
}

function TerminalBox({ title, icon, logs, onExpand }) {
  return (
    <div
      style={{
        flex: 1,
        background: "var(--bg-card)",
        borderRadius: "28px",
        border: "1px solid var(--border)",
        padding: "32px",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
        boxShadow: "var(--shadow-glow)",
        position: "relative",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
          paddingBottom: "16px",
          borderBottom: "1px solid var(--divider)",
        }}
      >
        <span
          style={{
            fontSize: "12px",
            fontWeight: "600",
            color: "var(--primary)",
            textTransform: "uppercase",
            letterSpacing: "1.5px",
          }}
        >
          {title}
        </span>
        <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
          <button
            onClick={onExpand}
            style={{
              background: "var(--divider)",
              border: "1px solid var(--border)",
              color: "var(--text-secondary)",
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s ease",
            }}
            className="hover-lift"
          >
            <Maximize2 size={14} />
          </button>
          <div style={{ opacity: 0.5 }}>{icon}</div>
        </div>
      </div>
      <div
        className="custom-scrollbar"
        style={{
          flex: 1,
          overflowY: "auto",
          fontFamily: "var(--font-mono)",
          fontSize: "13px",
          color: "var(--text-main)",
          lineHeight: 1.6,
        }}
      >
        {logs?.length > 0 ? (
          logs
            .slice(-50)
            .reverse()
            .map((log, i) => (
              <div
                key={i}
                style={{
                  padding: "10px 0",
                  borderBottom: "1px solid var(--divider)",
                  display: "flex",
                  gap: "20px",
                }}
              >
                <span
                  style={{
                    color: "var(--primary)",
                    opacity: 0.5,
                    minWidth: "90px",
                    fontWeight: "700",
                  }}
                >
                  {log.split(" - ")[0]}
                </span>
                <span style={{ flex: 1 }}>
                  {log.split(" - ").slice(1).join(" - ")}
                </span>
              </div>
            ))
        ) : (
          <div
            style={{
              opacity: 0.2,
              marginTop: "40px",
              textAlign: "center",
              fontWeight: "700",
            }}
          >
            Awaiting institutional feed...
          </div>
        )}
      </div>
    </div>
  );
}

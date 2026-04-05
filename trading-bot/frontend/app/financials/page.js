"use client";
import React from "react";
import { useBot } from "../components/BotContext";
import { useMediaQuery } from "../lib/useMediaQuery";
import StatsCard from "../components/StatsCard";
import { TrendingUp, PieChart, ArrowUpRight, Info } from "lucide-react";

export default function Financials() {
  const { botStatus } = useBot();
  const isMobile = useMediaQuery("(max-width: 768px)");

  return (
    <div
      className="animate-fade-in"
      style={{ 
        display: "flex", 
        flexDirection: "column", 
        gap: isMobile ? "20px" : "35px",
        padding: isMobile ? "0 0 40px 0" : "0"
      }}
    >
      <div style={{ marginBottom: isMobile ? "5px" : "10px" }}>
        <h1 style={{ fontSize: isMobile ? "24px" : "32px", marginBottom: "8px", fontWeight:"900" }}>
          Institutional Alpha
        </h1>
        <p style={{ color: "var(--text-sub)", fontSize: isMobile ? "13px" : "15px" }}>
          Performance metrics and capital growth analysis.
        </p>
      </div>

      <div style={{ 
        display: "grid", 
        gridTemplateColumns: isMobile ? "repeat(2, 1fr)" : "repeat(4, 1fr)",
        gap: isMobile ? "10px" : "20px" 
      }}>
        <StatsCard
          label="Cumulative ROI"
          value={`${(botStatus?.total_growth || 0) > 0 ? "+" : ""}${botStatus?.total_growth || 0}%`}
          subtext={isMobile ? "ROI (30D)" : "Net capital expansion (30D)"}
          type={(botStatus?.total_growth || 0) >= 0 ? "profit" : "loss"}
        />
        <StatsCard
          label="Accuracy"
          value={`${botStatus?.win_rate || 0}%`}
          subtext={isMobile ? "Win Rate" : "Target hit probability"}
        />
        <StatsCard
          label="Efficiency"
          value={(botStatus?.profit_factor || 0).toFixed(2)}
          subtext={isMobile ? "P/L Ratio" : "Gain/Loss efficiency ratio"}
          type={(botStatus?.profit_factor || 0) > 1.5 ? "profit" : "normal"}
        />
        <StatsCard
          label="Asset Count"
          value={botStatus?.active_trades || 0}
          subtext={isMobile ? "Active Deals" : "Active risk positions"}
        />
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: isMobile ? "column" : "row",
          gap: isMobile ? "15px" : "25px",
        }}
      >
        <div
          className="glass-panel"
          style={{
            padding: isMobile ? "20px" : "35px",
            minHeight: isMobile ? "300px" : "450px",
            position: "relative",
            overflow: "hidden",
            flex: 1.5
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "30px",
            }}
          >
            <h3 style={{ display: "flex", alignItems: "center", gap: "10px", fontSize: isMobile ? "15px" : "18px" }}>
              <TrendingUp size={20} color="var(--primary)" />
              Equity Matrix
            </h3>
            <div
              style={{
                background: "rgba(255,255,255,0.05)",
                padding: "6px 12px",
                borderRadius: "10px",
                fontSize: "10px",
                color: "var(--text-sub)",
                fontWeight: "900"
              }}
            >
              LIVE
            </div>
          </div>

          <div
            style={{
              height: isMobile ? "180px" : "300px",
              display: "flex",
              alignItems: "flex-end",
              gap: isMobile ? "6px" : "10px",
              paddingBottom: "20px",
            }}
          >
            {[40, 60, 45, 70, 85, 65, 90, 80, 100].map((h, i) => (
              <div
                key={i}
                style={{
                  flex: 1,
                  background: "var(--gradient-primary)",
                  opacity: 0.1 + i * 0.1,
                  borderRadius: "4px",
                  height: `${h}%`,
                }}
              ></div>
            ))}
          </div>

          <div
            style={{
              position: "absolute",
              top: "60%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              textAlign: "center",
              zIndex: 10,
              width: "100%",
              padding: "0 20px"
            }}
          >
            <p
              style={{
                fontSize: "11px",
                color: "var(--text-sub)",
                fontWeight: "800",
                letterSpacing: "1px"
              }}
            >
              CALCULATING ALPHA CURVE...
            </p>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: isMobile ? "15px" : "25px", flex: 1 }}>
          <div className="glass-panel" style={{ padding: isMobile ? "20px" : "30px", flex: 1 }}>
            <h3
              style={{
                fontSize: "14px",
                marginBottom: "20px",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                fontWeight: "800"
              }}
            >
              <PieChart size={18} color="var(--secondary)" />
              Drawdown Logic
            </h3>
            <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
              <div
                style={{
                  width: "4px",
                  height: "36px",
                  background: "var(--loss)",
                  borderRadius: "3px",
                }}
              ></div>
              <div>
                <p style={{ fontSize: "20px", fontWeight: "900" }}>-2.4%</p>
                <p style={{ fontSize: "10px", color: "var(--text-sub)", fontWeight: "700" }}>
                  MAX DRAWDOWN
                </p>
              </div>
            </div>
          </div>

          <div
            className="glass-panel"
            style={{
              padding: isMobile ? "20px" : "30px",
              flex: 1,
              background: "var(--gradient-primary)",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
              }}
            >
              <div>
                <p
                  style={{
                    color: "rgba(0,0,0,0.6)",
                    fontSize: "10px",
                    fontWeight: "900",
                    textTransform: "uppercase"
                  }}
                >
                  EST. MONTHLY
                </p>
                <p
                  style={{
                    color: "black",
                    fontSize: "24px",
                    fontWeight: "900",
                  }}
                >
                  +$4,290.45
                </p>
              </div>
              <div
                style={{
                  background: "rgba(0,0,0,0.1)",
                  padding: "8px",
                  borderRadius: "10px",
                }}
              >
                <ArrowUpRight color="black" size={20} />
              </div>
            </div>
            <p
              style={{
                color: "rgba(0,0,0,0.4)",
                fontSize: "10px",
                marginTop: "10px",
                fontWeight: "800",
              }}
            >
              AS OF CURRENT VELOCITY
            </p>
          </div>
        </div>
      </div>

      <div
        className="glass-card"
        style={{
          display: "flex",
          alignItems: "flex-start",
          gap: "12px",
          padding: isMobile ? "15px" : "15px 25px",
        }}
      >
        <Info size={16} color="var(--primary)" style={{ flexShrink: 0, marginTop: "2px" }} />
        <p style={{ fontSize: "11px", color: "var(--text-sub)", lineHeight: "1.5" }}>
          Metrics synced from MetaTrader Terminal every 60s. Calculation delay may apply.
        </p>
      </div>
    </div>
  );
}

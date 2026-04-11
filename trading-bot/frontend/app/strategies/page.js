"use client";
import React, { useState } from "react";
import StrategyList from "../components/StrategyList";
import StrategyAnalytics from "../components/StrategyAnalytics";
import { BarChart3, LayoutGrid } from "lucide-react";
import { useMediaQuery } from "../lib/useMediaQuery";

export default function StratagemsPage() {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const [showAnalytics, setShowAnalytics] = useState(false);

  return (
    <div
      className="animate-fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: isMobile ? "16px" : "25px",
        minHeight: isMobile ? "auto" : "calc(100vh - 80px)",
        padding: isMobile ? "0 0 40px 0" : "0"
      }}
    >
      <div 
        style={{ 
          display: "flex", 
          flexDirection: isMobile ? "column" : "row",
          justifyContent: "space-between", 
          alignItems: isMobile ? "flex-start" : "center", 
          gap: isMobile ? "20px" : "0",
          marginBottom: isMobile ? "24px" : "32px" 
        }}
      >
        <div>
          <h1
            style={{ fontSize: isMobile ? "22px" : "32px", fontWeight: "900", marginBottom: "8px", letterSpacing: "-1px" }}
          >
            Active <span style={{ color: "var(--primary)" }}>Institutional</span> Stratagems
          </h1>
          <p style={{ color: "var(--text-sub)", fontSize: isMobile ? "12px" : "14px", fontWeight: "500" }}>
            The refined institutional strategy families powering the High-Probability Alpha Engine.
          </p>
        </div>
        
        <button 
          onClick={() => setShowAnalytics(!showAnalytics)}
          className="glass-panel hover-lift"
          style={{
            padding: isMobile ? "12px 20px" : "14px 24px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            cursor: "pointer",
            border: `1px solid ${showAnalytics ? "var(--primary)" : "var(--border)"}`,
            background: showAnalytics ? "rgba(0,122,255,0.05)" : "rgba(255,255,255,0.02)",
            color: showAnalytics ? "var(--primary)" : "var(--text-main)",
            fontSize: "11px",
            fontWeight: "800",
            textTransform: "uppercase",
            letterSpacing: "1.5px",
            transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
            borderRadius: "14px",
            boxShadow: showAnalytics ? "0 0 20px rgba(0,122,255,0.1)" : "none"
          }}
        >
          {showAnalytics ? <LayoutGrid size={16} /> : <BarChart3 size={16} />}
          {showAnalytics ? "Parameter Configuration" : "Institutional Analytics"}
        </button>
      </div>

      <div style={{ flex: 1 }}>
        {showAnalytics ? (
          <StrategyAnalytics />
        ) : (
          <StrategyList isExpanded={true} />
        )}
      </div>
    </div>
  );
}

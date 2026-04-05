"use client";
import React from "react";
import TradeTable from "../components/TradeTable";
import { useBot } from "../components/BotContext";
import { useAuth } from "../components/AuthContext";
import { Briefcase, Activity, ShieldCheck, Zap, ArrowLeft } from "lucide-react";
import Link from "next/link";

import { useMediaQuery } from "../lib/useMediaQuery";

export default function PortfolioPage() {
  const { trades, botStatus } = useBot();
  const { user } = useAuth();
  const isMobile = useMediaQuery("(max-width: 768px)");
  const isSmallMobile = useMediaQuery("(max-width: 480px)");

  if (!user) return null;

  return (
    <div className="fade-in" style={{ paddingBottom: "40px" }}>
      {/* Header Area */}
      <div style={{ 
        display: "flex", 
        flexDirection: isMobile ? "column" : "row",
        justifyContent: "space-between", 
        alignItems: isMobile ? "flex-start" : "flex-end", 
        marginBottom: isMobile ? "24px" : "40px",
        gap: isMobile ? "24px" : "0"
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", color: "var(--primary)", marginBottom: "8px" }}>
             <Briefcase size={isMobile ? 16 : 20} />
             <span style={{ fontSize: isMobile ? "10px" : "12px", fontWeight: "900", letterSpacing: "1.5px", textTransform: "uppercase" }}>Global Portfolio</span>
          </div>
          <h1 style={{ fontSize: isMobile ? "28px" : "36px", fontWeight: "900", color: "#fff", letterSpacing: "-1px", margin: 0 }}>
            Active Alpha <span style={{ color: "var(--primary)" }}>Positions</span>
          </h1>
        </div>

        <div style={{ 
          display: "flex", 
          flexDirection: isSmallMobile ? "column" : "row",
          gap: isMobile ? "12px" : "24px",
          width: isMobile ? "100%" : "auto"
        }}>
           <PortfolioMetric label="Exposure" value={`$${(trades?.reduce((acc, t) => acc + (t.volume * (t.entry_price || 0)), 0) || 0).toLocaleString()}`} icon={<Zap size={16} />} isMobile={isMobile} />
           <PortfolioMetric label="Daily PNL" value={`$${(trades?.reduce((acc, t) => acc + (t.profit || 0), 0) || 0).toFixed(2)}`} icon={<Activity size={16} />} color={trades?.reduce((acc, t) => acc + (t.profit || 0), 0) >= 0 ? "var(--success)" : "var(--danger)"} isMobile={isMobile} />
           <PortfolioMetric label="Margin Used" value={`$${(botStatus?.margin || 0).toLocaleString()}`} icon={<ShieldCheck size={16} />} isMobile={isMobile} />
        </div>
      </div>

      {/* Main Table Container */}
      <div style={{ 
        background: "var(--bg-card)", 
        border: "1px solid var(--border)", 
        borderRadius: isMobile ? "16px" : "24px", 
        padding: isMobile ? "16px" : "32px",
        boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
        overflowX: "auto"
      }}>
        <TradeTable trades={trades} />
      </div>

      <div style={{ marginTop: "32px" }}>
         <Link href="/" style={{ 
           display: "inline-flex", 
           alignItems: "center", 
           gap: "10px", 
           color: "var(--text-secondary)", 
           textDecoration: "none",
           fontSize: "14px",
           fontWeight: "700",
           transition: "all 0.2s"
         }} className="hover-lift">
            <ArrowLeft size={16} />
            Back to Intelligence Hub
         </Link>
      </div>
    </div>
  );
}

function PortfolioMetric({ label, value, icon, color, isMobile }) {
  return (
    <div style={{ 
      background: "rgba(255,255,255,0.02)", 
      border: "1px solid var(--border)", 
      borderRadius: "16px", 
      padding: isMobile ? "12px 16px" : "16px 24px",
      display: "flex",
      alignItems: "center",
      gap: "16px",
      minWidth: isMobile ? "0" : "180px",
      flex: 1
    }}>
      <div style={{ color: color || "var(--primary)", opacity: 0.8 }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: "10px", fontWeight: "800", color: "var(--text-sub)", textTransform: "uppercase", letterSpacing: "0.5px" }}>{label}</div>
        <div style={{ fontSize: isMobile ? "15px" : "18px", fontWeight: "900", color: color || "#fff", marginTop: "2px" }}>{value}</div>
      </div>
    </div>
  );
}

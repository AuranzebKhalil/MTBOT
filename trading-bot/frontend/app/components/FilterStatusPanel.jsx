"use client";
import React from "react";
import { Shield, Clock, MapPin, Zap, AlertTriangle } from "lucide-react";
import { useBot } from "./BotContext";
import { useMediaQuery } from "../lib/useMediaQuery";

export default function FilterStatusPanel() {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const isTablet = useMediaQuery("(max-width: 1024px)");
  const isSmallMobile = useMediaQuery("(max-width: 600px)");
  const { filterStatus, activeCooldowns, activeBlockedZones } = useBot();

  const filters = [
    { id: "news", label: "News Filter", icon: <Zap size={14} />, status: filterStatus?.news ? "BLOCKED" : "ACTIVE" },
    { id: "session", label: "Session Guard", icon: <Clock size={14} />, status: filterStatus?.session ? "ACTIVE" : "OUT_OF_SESSION" },
    { id: "cooldown", label: "Cooldown Filter", icon: <Clock size={14} />, status: activeCooldowns.length > 0 ? "COOLDOWN" : "IDLE" },
    { id: "zone", label: "Price Zone Block", icon: <MapPin size={14} />, status: activeBlockedZones.length > 0 ? "BLOCKED" : "NONE" },
  ];

  return (
    <div className="glass-panel" style={{ padding: isMobile ? "16px" : "24px", marginBottom: "32px", display: "flex", flexDirection: "column", gap: "24px" }}>
      <div style={{ display: "flex", flexDirection: isMobile ? "column" : "row", justifyContent: "space-between", alignItems: isMobile ? "flex-start" : "center", gap: isMobile ? "12px" : "0" }}>
        <h3 style={{ fontSize: isMobile ? "12px" : "14px", fontWeight: "700", color: "var(--text-main)", display: "flex", alignItems: "center", gap: "10px" }}>
          <Shield size={16} color="var(--primary)" /> INSTUCTIONAL RISK FILTERS
        </h3>
        <div style={{ display: "flex", gap: "20px" }}>
          {activeCooldowns.length > 0 && (
            <div style={{ fontSize: "10px", color: "var(--accent-yellow)", fontWeight: "600", display: "flex", alignItems: "center", gap: "6px" }}>
               <AlertTriangle size={12} /> {activeCooldowns.length} COOLDOWNS
            </div>
          )}
          {activeBlockedZones.length > 0 && (
            <div style={{ fontSize: "10px", color: "var(--loss)", fontWeight: "600", display: "flex", alignItems: "center", gap: "6px" }}>
               <Shield size={12} /> {activeBlockedZones.length} ZONES BLOCKED
            </div>
          )}
        </div>
      </div>

      <div style={{ 
        display: "grid", 
        gridTemplateColumns: isSmallMobile ? "1fr" : isTablet ? "repeat(2, 1fr)" : "repeat(4, 1fr)", 
        gap: "12px" 
      }}>
        {filters.map((f) => (
          <div key={f.id} style={{
            background: "rgba(255,255,255,0.02)",
            borderRadius: "12px",
            padding: "16px",
            border: "1px solid var(--border)",
            display: "flex",
            flexDirection: "column",
            gap: "8px"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--text-secondary)", fontSize: "10px", fontWeight: "600", textTransform: "uppercase" }}>
              {f.icon} {f.label}
            </div>
            <div style={{ 
              fontSize: "13px", 
              fontWeight: "700", 
              color: f.status === "ACTIVE" || f.status === "NONE" || f.status === "IDLE" ? "var(--success)" : 
                     f.status === "COOLDOWN" ? "var(--accent-yellow)" : "var(--loss)"
            }}>
              {f.status}
            </div>
          </div>
        ))}
      </div>

      {(activeCooldowns.length > 0 || activeBlockedZones.length > 0) && (
        <div style={{ 
          display: "grid", 
          gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr", 
          gap: "24px", 
          paddingTop: "12px", 
          borderTop: "1px solid var(--divider)" 
        }}>
          {/* COOLDOWN LIST */}
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <span style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-secondary)", opacity: 0.6 }}>ACTIVE COOLDOWNS</span>
            {activeCooldowns.map((cd, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", background: "rgba(255, 159, 10, 0.05)", padding: "8px 12px", borderRadius: "8px", border: "1px solid rgba(255, 159, 10, 0.1)" }}>
                <span style={{ fontWeight: "700" }}>{cd.symbol} <span style={{ color: cd.direction === "BUY" ? "var(--success)" : "var(--loss)" }}>{cd.direction}</span></span>
                <span style={{ opacity: 0.7, fontSize: "11px" }}>Until {new Date(cd.expiry).toLocaleTimeString()}</span>
              </div>
            ))}
            {activeCooldowns.length === 0 && <span style={{ fontSize: "11px", opacity: 0.3 }}>No active cooldowns</span>}
          </div>

          {/* BLOCKED ZONES */}
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <span style={{ fontSize: "10px", fontWeight: "700", color: "var(--text-secondary)", opacity: 0.6 }}>BLOCKED PRICE ZONES</span>
            {activeBlockedZones.map((z, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", background: "rgba(255, 69, 58, 0.05)", padding: "8px 12px", borderRadius: "8px", border: "1px solid rgba(255, 69, 58, 0.1)" }}>
                <span style={{ fontWeight: "700" }}>{z.symbol} <span style={{ color: z.direction === "BUY" ? "var(--success)" : "var(--loss)" }}>{z.direction}</span></span>
                <span style={{ opacity: 0.7, fontSize: "11px" }}>Range: {z.bottom.toFixed(5)} - {z.top.toFixed(5)}</span>
              </div>
            ))}
            {activeBlockedZones.length === 0 && <span style={{ fontSize: "11px", opacity: 0.3 }}>No price zones blocked</span>}
          </div>
        </div>
      )}
    </div>
  );
}

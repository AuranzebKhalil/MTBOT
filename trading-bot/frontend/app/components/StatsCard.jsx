"use client";
import React from "react";

export default function StatsCard({ label, value, subtext, type = "default" }) {
  const getColors = () => {
    switch (type) {
      case "profit":
        return "var(--profit)";
      case "loss":
        return "var(--loss)";
      case "primary":
        return "var(--primary)";
      default:
        return "var(--text-main)";
    }
  };

  return (
    <div className="glass-panel" style={{ padding: "25px", flex: 1 }}>
      <p
        style={{
          color: "var(--text-sub)",
          fontSize: "13px",
          fontWeight: "600",
          marginBottom: "10px",
          textTransform: "uppercase",
          letterSpacing: "0.5px",
        }}
      >
        {label}
      </p>
      <h3
        style={{
          fontSize: "26px",
          fontWeight: "900",
          color: getColors(),
          marginBottom: "8px",
          letterSpacing: "-0.5px",
        }}
      >
        {value}
      </h3>
      <p
        style={{
          fontSize: "12px",
          color: "var(--text-sub)",
          fontWeight: "500",
        }}
      >
        {subtext}
      </p>
    </div>
  );
}

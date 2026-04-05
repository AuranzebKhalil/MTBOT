"use client";
import React from "react";
import StrategyList from "../components/StrategyList";

import { useMediaQuery } from "../lib/useMediaQuery";

export default function StratagemsPage() {
  const isMobile = useMediaQuery("(max-width: 768px)");

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
      <div>
        <h1
          style={{ fontSize: isMobile ? "22px" : "28px", fontWeight: "900", marginBottom: "5px" }}
        >
          Active Institutional Stratagems
        </h1>
        <p style={{ color: "var(--text-sub)", fontSize: isMobile ? "12px" : "14px" }}>
          The 5 consolidated institutional strategy families powering the Quant
          Engine.
        </p>
      </div>

      <div style={{ flex: 1 }}>
        <StrategyList isExpanded={true} />
      </div>
    </div>
  );
}

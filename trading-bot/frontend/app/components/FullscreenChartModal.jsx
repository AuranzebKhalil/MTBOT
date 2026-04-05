"use client";
import React, { useEffect } from "react";
import AlphaFluxChart from "./AlphaFluxChart";
import StrategyExplanation from "./StrategyExplanation";
import { X } from "lucide-react";

export default function FullscreenChartModal({ isOpen, onClose }) {
  useEffect(() => {
    if (isOpen) {
      document.body.classList.add("modal-open");
    } else {
      document.body.classList.remove("modal-open");
    }
    return () => {
      document.body.classList.remove("modal-open");
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        zIndex: 999999, // Ultra high to cover sidebar/header
        background: "#08090d", // Dense institutional background
        display: "flex",
        flexDirection: "column",
        padding: "30px",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
        }}
      >
        <h2 style={{ fontSize: "24px", fontWeight: "900", color: "#fff" }}>
          Institutional Chart Analysis
        </h2>
        <button
          onClick={onClose}
          style={{
            background: "rgba(255,255,255,0.1)",
            border: "none",
            color: "#fff",
            padding: "10px",
            borderRadius: "50%",
            cursor: "pointer",
          }}
        >
          <X size={24} />
        </button>
      </div>

      <div style={{ display: "flex", gap: "20px", flex: 1, minHeight: 0 }}>
        <div
          style={{
            flex: 3,
            background: "rgba(255,255,255,0.02)",
            borderRadius: "20px",
            padding: "20px",
            border: "1px solid rgba(255,255,255,0.05)",
          }}
        >
          <AlphaFluxChart />
        </div>
        <div style={{ flex: 1, minWidth: "350px" }}>
          <StrategyExplanation onFullscreen={() => {}} />
        </div>
      </div>
    </div>
  );
}

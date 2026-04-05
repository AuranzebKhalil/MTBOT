"use client";
import React from "react";
import { useBot } from "../components/BotContext";

export default function MarketDepth() {
  const { depth, selectedSymbol } = useBot();

  return (
    <div
      className="animate-fade-in glass-panel"
      style={{ padding: "30px", minHeight: "600px" }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "30px",
        }}
      >
        <h2 style={{ fontSize: "24px", fontWeight: "800" }}>
          Institutional Market Depth
        </h2>
        <div style={{ fontSize: "12px", color: "rgba(255,255,255,0.4)" }}>
          ASSET: {selectedSymbol} • DEPTH: L2
        </div>
      </div>

      <div
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "30px" }}
      >
        <div className="depth-side">
          <h3
            style={{
              color: "var(--profit)",
              fontSize: "14px",
              marginBottom: "15px",
              padding: "10px",
            }}
          >
            BIDS (BUY ORDERS)
          </h3>
          {depth.bids && depth.bids.length > 0 ? (
            depth.bids.map((d, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "10px 15px",
                  borderBottom: "1px solid rgba(0,255,189,0.05)",
                  fontSize: "14px",
                }}
              >
                <span style={{ fontFamily: "monospace" }}>
                  {d.price.toFixed(5)}
                </span>
                <span style={{ color: "var(--profit)", fontWeight: "700" }}>
                  {d.volume.toFixed(2)}M
                </span>
              </div>
            ))
          ) : (
            <div style={{ padding: "20px", color: "rgba(255,255,255,0.2)" }}>
              Waiting for Depth Data...
            </div>
          )}
        </div>

        <div className="depth-side">
          <h3
            style={{
              color: "var(--loss)",
              fontSize: "14px",
              marginBottom: "15px",
              padding: "10px",
            }}
          >
            ASKS (SELL ORDERS)
          </h3>
          {depth.asks && depth.asks.length > 0 ? (
            depth.asks.map((d, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "10px 15px",
                  borderBottom: "1px solid rgba(255,71,87,0.05)",
                  fontSize: "14px",
                }}
              >
                <span style={{ fontFamily: "monospace" }}>
                  {d.price.toFixed(5)}
                </span>
                <span style={{ color: "var(--loss)", fontWeight: "700" }}>
                  {d.volume.toFixed(2)}M
                </span>
              </div>
            ))
          ) : (
            <div style={{ padding: "20px", color: "rgba(255,255,255,0.2)" }}>
              Waiting for Depth Data...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

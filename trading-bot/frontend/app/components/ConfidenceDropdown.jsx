"use client";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";

export default function ConfidenceDropdown({
  valuePct,
  minPct = 15,
  maxPct = 100,
  onChangePct,
}) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  const options = useMemo(() => {
    const out = [];
    for (let i = minPct; i <= maxPct; i++) out.push(i);
    return out;
  }, [minPct, maxPct]);

  useEffect(() => {
    const onDocClick = (e) => {
      if (!open) return;
      if (!rootRef.current) return;
      if (rootRef.current.contains(e.target)) return;
      setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open]);

  const safeValue =
    typeof valuePct === "number"
      ? Math.min(maxPct, Math.max(minPct, Math.round(valuePct)))
      : 65;

  return (
    <div ref={rootRef} style={{ position: "relative" }}>
      <div
        onClick={() => setOpen((v) => !v)}
        className="hover-lift"
        style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "10px",
          padding: "14px",
          borderRadius: "10px",
          cursor: "pointer",
          background: "var(--divider)",
          border: "1px solid var(--glass-border)",
          userSelect: "none",
        }}
      >
        <span style={{ fontSize: "14px", fontWeight: "800", color: "var(--text-main)" }}>
          {safeValue}% Confidence
        </span>
        <ChevronDown size={16} color="var(--text-sub)" />
      </div>

      {open && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            right: 0,
            marginTop: "10px",
            background: "var(--bg-card)",
            border: "1px solid var(--glass-border)",
            borderRadius: "12px",
            boxShadow: "var(--shadow-glow)",
            overflow: "hidden",
            zIndex: 1000,
          }}
        >
          <div
            style={{
              maxHeight: "280px",
              overflowY: "auto",
              padding: "8px",
            }}
          >
            {options.map((pct) => {
              const active = pct === safeValue;
              return (
                <div
                  key={pct}
                  onClick={() => {
                    onChangePct?.(pct);
                    setOpen(false);
                  }}
                  style={{
                    padding: "10px 12px",
                    fontSize: "12px",
                    fontWeight: "900",
                    borderRadius: "10px",
                    color: active ? "var(--primary)" : "var(--text-sub)",
                    background: active
                      ? "rgba(91, 134, 229, 0.12)"
                      : "transparent",
                    cursor: "pointer",
                    transition: "0.2s",
                    marginBottom: "4px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                  onMouseEnter={(e) => {
                    if (!active)
                      e.currentTarget.style.background =
                        "var(--divider)";
                  }}
                  onMouseLeave={(e) => {
                    if (!active)
                      e.currentTarget.style.background = "transparent";
                  }}
                >
                  <span>{pct}% Confidence</span>
                  {active && (
                    <div
                      style={{
                        width: "7px",
                        height: "7px",
                        borderRadius: "50%",
                        background: "var(--primary)",
                      }}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}


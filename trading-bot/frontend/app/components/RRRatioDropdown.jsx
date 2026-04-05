"use client";
import React, { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";

export default function RRRatioDropdown({ value, onChange }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  const options = [
    { label: "1 : 0.5 (Scalp)", value: 0.5 },
    { label: "1 : 1.0 (Balanced)", value: 1.0 },
    { label: "1 : 1.5 (Standard)", value: 1.5 },
    { label: "1 : 2.0 (Conservative)", value: 2.0 },
    { label: "1 : 3.0 (Trend)", value: 3.0 },
    { label: "1 : 5.0 (Institution)", value: 5.0 },
  ];

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

  const selectedOption = options.find((opt) => String(opt.value) === String(value)) || options[2];

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
          {selectedOption.label}
        </span>
        <ChevronDown size={16} color="var(--text-sub)" />
      </div>

      {open && (
        <div
          style={{
            position: "absolute",
            bottom: "100%", // Open upwards since it's near the bottom of the scroll
            left: 0,
            right: 0,
            marginBottom: "10px",
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
            {options.map((opt) => {
              const active = String(opt.value) === String(value);
              return (
                <div
                  key={opt.value}
                  onClick={() => {
                    onChange?.(opt.value);
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
                  <span>{opt.label}</span>
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

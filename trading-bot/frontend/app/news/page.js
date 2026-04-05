"use client";
import React, { useState, useEffect } from "react";
import { useMediaQuery } from "../lib/useMediaQuery";
import { Search, Filter, Globe, Clock, AlertTriangle, ShieldAlert } from "lucide-react";
import { getApiBaseUrl } from "../lib/config";

export default function NewsPage() {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const isMobile = useMediaQuery("(max-width: 768px)");

  useEffect(() => {
    fetchNews();
    const interval = setInterval(fetchNews, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchNews = async () => {
    try {
      const token = localStorage.getItem("quant_token");
      const res = await fetch(`${getApiBaseUrl()}/news`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setNews(data);
      }
    } catch (err) {
      console.error("Failed to fetch news:", err);
    } finally {
      setLoading(false);
    }
  };

  const filteredNews = news.filter((item) => {
    const matchesFilter = filter === "ALL" || item.symbol === filter;
    const matchesSearch =
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.symbol.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const uniqueCurrencies = ["ALL", ...new Set(news.map((item) => item.symbol))];

  return (
    <div
      style={{
        padding: isMobile ? "20px" : "40px",
        color: "var(--text-main)",
        maxWidth: "1200px",
        margin: "0 auto",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: isMobile ? "column" : "row",
          justifyContent: "space-between",
          alignItems: isMobile ? "flex-start" : "flex-end",
          marginBottom: isMobile ? "24px" : "40px",
          gap: isMobile ? "20px" : "0"
        }}
      >
        <div>
          <h1
            style={{
              fontSize: isMobile ? "24px" : "32px",
              fontWeight: "900",
              letterSpacing: "-1px",
              marginBottom: "10px",
            }}
          >
            ECONOMIC <span className="text-gradient">CALENDAR</span>
          </h1>
          <p
            style={{
              color: "var(--text-sub)",
              fontSize: isMobile ? "12px" : "14px",
              fontWeight: "500",
            }}
          >
            Real-time high-impact events monitoring.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", width: isMobile ? "100%" : "auto" }}>
          <div
            className="glass-panel"
            style={{
              padding: "8px 15px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              flex: 1
            }}
          >
            <Search size={16} color="var(--text-sub)" />
            <input
              type="text"
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                background: "none",
                border: "none",
                color: "var(--text-main)",
                outline: "none",
                fontSize: "13px",
                width: "100%",
              }}
            />
          </div>

          <div
            className="glass-panel"
            style={{
              padding: "8px 15px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <Filter size={16} color="var(--text-sub)" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{
                background: "none",
                border: "none",
                color: "var(--text-main)",
                outline: "none",
                fontSize: "13px",
                cursor: "pointer",
              }}
            >
              {uniqueCurrencies.map((c) => (
                <option
                  key={c}
                  value={c}
                  style={{ background: "var(--surface)" }}
                >
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: "100px" }}>
          <div className="spinner" style={{ marginBottom: "20px" }}></div>
          <p>Syncing Alpha News Feed...</p>
        </div>
      ) : filteredNews.length === 0 ? (
        <div
          className="glass-panel"
          style={{
            padding: isMobile ? "60px 20px" : "100px",
            textAlign: "center",
            border: "1px dashed var(--glass-border)",
          }}
        >
          <Globe
            size={48}
            color="var(--text-sub)"
            style={{ opacity: 0.3, marginBottom: "20px" }}
          />
          <h2 style={{ fontSize: "18px", marginBottom: "10px" }}>
            No Major Volatility Detected
          </h2>
          <p style={{ color: "var(--text-sub)", fontSize: "14px" }}>
            The horizon is clear for{" "}
            {filter === "ALL" ? "global markets" : filter}.
          </p>
        </div>
      ) : (
        <div style={{ display: "grid", gap: "15px" }}>
          {filteredNews.map((event, idx) => (
            <div
              key={idx}
              className="glass-panel"
              style={{
                padding: isMobile ? "16px" : "20px 30px",
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                alignItems: isMobile ? "flex-start" : "center",
                justifyContent: "space-between",
                borderLeft:
                  event.impact === "HIGH"
                    ? "4px solid var(--loss)"
                    : "4px solid var(--primary)",
                transition: "0.3s ease",
                gap: isMobile ? "16px" : "0"
              }}
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: isMobile ? "16px" : "25px" }}
              >
                <div
                  style={{
                    width: isMobile ? "40px" : "50px",
                    height: isMobile ? "40px" : "50px",
                    borderRadius: "12px",
                    background: "rgba(255,255,255,0.03)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: isMobile ? "12px" : "14px",
                    fontWeight: "800",
                    color: "var(--primary)",
                    flexShrink: 0
                  }}
                >
                  {event.symbol}
                </div>

                <div>
                  <h3
                    style={{
                      fontSize: isMobile ? "14px" : "16px",
                      fontWeight: "700",
                      marginBottom: "4px",
                    }}
                  >
                    {event.name}
                  </h3>
                  <div
                    style={{
                      display: "flex",
                      gap: "15px",
                      alignItems: "center",
                    }}
                  >
                    <span
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "12px",
                        color: "var(--text-sub)",
                      }}
                    >
                      <Clock size={12} /> {event.time}
                    </span>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: "900",
                        padding: "2px 8px",
                        borderRadius: "6px",
                        background:
                          event.impact === "HIGH"
                            ? "rgba(255, 71, 87, 0.1)"
                            : "rgba(0, 255, 189, 0.1)",
                        color:
                          event.impact === "HIGH"
                            ? "var(--loss)"
                            : "var(--profit)",
                        letterSpacing: "0.5px",
                      }}
                    >
                      {event.impact} IMPACT
                    </span>
                  </div>
                </div>
              </div>

              <div style={{ textAlign: isMobile ? "left" : "right", width: isMobile ? "100%" : "auto" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    color: "var(--loss)",
                    fontSize: "12px",
                    fontWeight: "700",
                  }}
                >
                  <AlertTriangle size={14} />
                  ENGINE AUTO-PAUSE ACTIVE
                </div>
                <p
                  style={{
                    fontSize: "11px",
                    color: "var(--text-sub)",
                    marginTop: "4px",
                  }}
                >
                  Institutional news buffer: ±15m
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      <div
        className="glass-panel"
        style={{
          marginTop: "40px",
          padding: isMobile ? "20px" : "30px",
          background: "rgba(91, 134, 229, 0.03)",
          border: "1px solid rgba(91, 134, 229, 0.1)",
        }}
      >
        <h4
          style={{
            fontSize: "14px",
            fontWeight: "800",
            marginBottom: "15px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <ShieldAlert size={16} color="var(--primary)" />
          RISK ADVISORY: NEWS PROTOCOL
        </h4>
        <p
          style={{
            fontSize: "13px",
            color: "var(--text-sub)",
            lineHeight: "1.6",
          }}
        >
          The Alertli AI Quant Engine automatically halts all new entry signals
          15 minutes before and after scheduled High-Impact (Red Folder) news.
        </p>
      </div>
    </div>
  );
}

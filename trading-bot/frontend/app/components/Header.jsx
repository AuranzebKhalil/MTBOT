"use client";
import React from "react";
import { useBot } from "./BotContext";
import { useAuth } from "./AuthContext";
import { useTheme } from "./ThemeContext";
import { usePathname, useRouter } from "next/navigation";
import {
  Menu,
  X,
  ChevronDown,
  Settings,
  Bell,
  Maximize2,
  Minimize2,
  Sun,
  Moon,
  Zap,
  Globe,
  Activity,
  TrendingUp,
  BarChart3,
  Target,
  Plus,
  Trash2,
  Loader,
  User,
} from "lucide-react";
import { useMediaQuery } from "../lib/useMediaQuery";
import AssetIcon from "./AssetIcon";
import Image from "next/image";

export default function Header() {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const isTablet = useMediaQuery("(max-width: 1024px)");
  const isSmallDesktop = useMediaQuery("(max-width: 1280px)");
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const {
    isRunning,
    activeSymbols,
    selectedTF,
    updateBotSettings,
    isSidebarCollapsed,
    setIsSidebarCollapsed,
    isSidebarHidden,
    setIsSidebarHidden,
    aiConfidenceThreshold,
  } = useBot();
  const router = useRouter();
  const [isPairsOpen, setIsPairsOpen] = React.useState(false);
  const pairsRef = React.useRef(null);
  const pathname = usePathname();

  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (pairsRef.current && !pairsRef.current.contains(event.target)) {
        setIsPairsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  if (!user || pathname === "/login" || pathname === "/register") return null;

  return (
    <header
      style={{
        zIndex: 200,
        height: isMobile ? "70px" : "80px",
        padding: isMobile ? "0 16px" : "0 32px",
        background: "var(--glass-bg)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid var(--border)",
        boxShadow: "var(--card-shadow)",
        display: isTablet ? "flex" : "grid",
        gridTemplateColumns: isTablet ? "none" : "1fr 1fr 1fr",
        flexDirection: isTablet ? "column" : "row",
        alignItems: "center",
        justifyContent: isTablet ? "space-between" : "stretch",
        flexShrink: 0,
        width: "100%",
        gap: "0",
        position: "sticky",
        top: 0,
      }}
    >
      {/* MOBILE HEADER LAYOUT (Two Rows) */}
      {isMobile ? (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "16px",
            width: "100%",
          }}
        >
          {/* Row 1: Logo, Status, Controls */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              width: "100%",
            }}
          >
            <div
              style={{
                width: "36px",
                height: "36px",
                background: "var(--gradient-auralith)",
                borderRadius: "10px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 15px var(--primary-glow)",
              }}
            >
              <Image
                src="/logo/AuraLithLogo.png"
                alt="Logo"
                width={22}
                height={22}
              />
            </div>

            <div
              style={{
                background: "var(--bg-card)",
                border: "1px solid var(--border)",
                padding: "6px 12px",
                borderRadius: "100px",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <div
                style={{
                  width: "8px",
                  height: "8px",
                  background: isRunning ? "var(--success)" : "var(--danger)",
                  borderRadius: "50%",
                  boxShadow: isRunning
                    ? "0 0 8px var(--success)"
                    : "0 0 8px var(--danger)",
                }}
              />
              <span
                style={{
                  fontSize: "10px",
                  fontWeight: "800",
                  color: "var(--text-main)",
                  textTransform: "uppercase",
                }}
              >
                {isRunning ? "SCN" : "STB"}
              </span>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <HeaderIconButton
                icon={theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
                onClick={toggleTheme}
                size={36}
              />
              <button
                onClick={() => setIsSidebarHidden(!isSidebarHidden)}
                style={{
                  background: "var(--divider)",
                  border: "1px solid var(--border)",
                  borderRadius: "12px",
                  padding: "8px",
                  color: "var(--text-main)",
                }}
              >
                {isSidebarHidden ? <Menu size={20} /> : <X size={20} />}
              </button>
            </div>
          </div>

          {/* Row 2: Tabs and Pairs */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              justifyContent: "flex-start",
            }}
          >
            <div
              style={{
                display: "flex",
                background: "var(--divider)",
                borderRadius: "10px",
                padding: "2px",
                border: "1px solid var(--border)",
              }}
            >
              {["M1", "M5", "M15", "H1"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => updateBotSettings(null, tf)}
                  style={{
                    padding: "0 8px",
                    height: "28px",
                    minWidth: "32px",
                    background:
                      selectedTF === tf ? "var(--primary)" : "transparent",
                    border: "none",
                    color: selectedTF === tf ? "#000" : "var(--text-secondary)",
                    fontSize: "10px",
                    fontWeight: "800",
                    borderRadius: "6px",
                  }}
                >
                  {tf}
                </button>
              ))}
            </div>
            <div style={{ position: "relative" }} ref={pairsRef}>
              <div
                onClick={() => setIsPairsOpen(!isPairsOpen)}
                style={{
                  background: "var(--primary-light)",
                  border: "1px solid var(--primary-glow)",
                  padding: "0 10px",
                  borderRadius: "10px",
                  fontSize: "10px",
                  fontWeight: "800",
                  color: "var(--primary)",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                  height: "32px",
                }}
              >
                {activeSymbols.length} PAIRS
              </div>
              {isPairsOpen && (
                <QuickPairsDropdown
                  activeSymbols={activeSymbols}
                  updateBotSettings={updateBotSettings}
                  selectedTF={selectedTF}
                  aiThreshold={aiConfidenceThreshold}
                  isMobile={true}
                />
              )}
            </div>
          </div>
        </div>
      ) : (
        /* DESKTOP HEADER LAYOUT (Robust 3x1fr Grid) */
        <>
          {/* LEFT: STATUS & LOGO (Grid Cell 1 - Start Aligned) */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifySelf: "start",
              gap: "16px",
            }}
          >
            {/* <div
              style={{
                width: "40px",
                height: "40px",
                background: "var(--gradient-auralith)",
                borderRadius: "12px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 20px var(--primary-glow)",
                flexShrink: 0,
                overflow: "hidden",
              }}
            >
              <Image
                src="/logo/AuraLithLogo.png"
                alt="Logo"
                width={28}
                height={28}
                style={{ objectFit: "cover" }}
              />
            </div> */}

            {/* STATUS PILL (MOVED TO LEFT) */}
            <div
              style={{
                background: "rgba(255,255,255,0.02)",
                border: "1px solid var(--border)",
                padding: "4px 14px",
                borderRadius: "100px",
                display: "flex",
                alignItems: "center",
                gap: "10px",
                minHeight: "38px",
                whiteSpace: "nowrap",
              }}
            >
              <div
                style={{
                  width: "8px",
                  height: "8px",
                  background: isRunning ? "var(--success)" : "var(--danger)",
                  borderRadius: "50%",
                  boxShadow: isRunning
                    ? "0 0 8px var(--success)"
                    : "0 0 8px var(--danger)",
                  animation: isRunning
                    ? "pulse 2s infinite ease-in-out"
                    : "none",
                }}
              />
              <div
                style={{ display: "flex", flexDirection: "column", gap: "0" }}
              >
                <span
                  style={{
                    fontSize: "7px",
                    fontWeight: "900",
                    color: "var(--text-sub)",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    opacity: 0.6,
                  }}
                >
                  Engine Status
                </span>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: "800",
                    color: "var(--text-main)",
                    lineHeight: 1,
                    marginTop: "2px",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      gap: "10px",
                      alignItems: "center",
                    }}
                  >
                    {isRunning ? "SCANNING..." : "STANDBY"}

                    <Loader style={{ width: "16px" }} />
                  </div>
                </span>
              </div>
            </div>
          </div>

          {/* CENTER: Grid Cell 2 - Center Aligned */}
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              justifySelf: "center",
            }}
          >
            {/* Center cell empty - Status moved to Left */}
          </div>

          {/* RIGHT: CONTROLS (Grid Cell 3 - End Aligned) */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              justifySelf: "end",
            }}
          >
            <div
              style={{
                display: "flex",
                background: "var(--divider)",
                borderRadius: "12px",
                padding: "3px",
                border: "1px solid var(--border)",
                height: "36px",
                alignItems: "center",
              }}
            >
              {["M1", "M5", "M15", "H1"].map((tf) => (
                <button
                  key={tf}
                  onClick={() => updateBotSettings(null, tf)}
                  style={{
                    padding: isSmallDesktop ? "0 10px" : "0 14px",
                    height: "30px",
                    background:
                      selectedTF === tf ? "var(--primary)" : "transparent",
                    border: "none",
                    color:
                      selectedTF === tf
                        ? theme === "dark"
                          ? "#000"
                          : "#fff"
                        : "var(--text-secondary)",
                    fontSize: "11px",
                    fontWeight: "800",
                    cursor: "pointer",
                    borderRadius: "8px",
                  }}
                >
                  {tf}
                </button>
              ))}
            </div>

            {!isSmallDesktop && (
              <div
                style={{
                  background: "var(--divider)",
                  border: "1px solid var(--border)",
                  padding: "0 12px",
                  borderRadius: "12px",
                  fontSize: "11px",
                  fontWeight: "600",
                  color: "var(--text-secondary)",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  height: "36px",
                }}
              >
                {new Date().getUTCHours().toString().padStart(2, "0")}:
                {new Date().getUTCMinutes().toString().padStart(2, "0")}{" "}
                <ChevronDown size={12} style={{ opacity: 0.6 }} />
              </div>
            )}

            <div style={{ position: "relative" }} ref={pairsRef}>
              <div
                onClick={() => setIsPairsOpen(!isPairsOpen)}
                style={{
                  background: "var(--primary-light)",
                  border: "1px solid var(--primary-glow)",
                  padding: isSmallDesktop ? "0 10px" : "0 14px",
                  borderRadius: "12px",
                  fontSize: "11px",
                  fontWeight: "800",
                  color: "var(--primary)",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  height: "36px",
                  whiteSpace: "nowrap",
                }}
                className="hover-lift"
              >
                {activeSymbols.length} {isSmallDesktop ? "P" : "ACTIVE PAIRS"}{" "}
                <ChevronDown
                  size={12}
                  style={{
                    transform: isPairsOpen ? "rotate(180deg)" : "rotate(0)",
                    transition: "0.3s",
                  }}
                />
              </div>
              {isPairsOpen && (
                <QuickPairsDropdown
                  activeSymbols={activeSymbols}
                  updateBotSettings={updateBotSettings}
                  selectedTF={selectedTF}
                  aiThreshold={aiConfidenceThreshold}
                  isMobile={false}
                />
              )}
            </div>

            <div style={{ display: "flex", gap: "6px" }}>
              <HeaderIconButton
                icon={theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
                onClick={toggleTheme}
                size={36}
              />
              {!isSmallDesktop && (
                <HeaderIconButton
                  icon={<User size={14} />}
                  onClick={() => router.push("/profile")}
                  size={36}
                />
              )}
            </div>
          </div>
        </>
      )}
    </header>
  );
}

function HeaderIconButton({ icon, onClick, size = 42 }) {
  return (
    <button
      onClick={onClick}
      style={{
        width: `${size}px`,
        height: `${size}px`,
        borderRadius: "12px",
        background: "var(--divider)",
        border: "1px solid var(--border)",
        color: "var(--text-secondary)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        transition: "all 0.2s ease",
        flexShrink: 0,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--primary)";
        e.currentTarget.style.color = "var(--primary)";
        e.currentTarget.style.background = "var(--primary-light)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--border)";
        e.currentTarget.style.color = "var(--text-secondary)";
        e.currentTarget.style.background = "var(--divider)";
      }}
    >
      {icon}
    </button>
  );
}

function QuickPairsDropdown({
  activeSymbols,
  updateBotSettings,
  selectedTF,
  aiThreshold,
  isMobile,
}) {
  const SUGGESTED = [
    "EURUSD",
    "USDJPY",
    "AUDUSD",
    "USDCHF",
    "USDCAD",
    "GBPUSD",
    "XAUUSD",
  ];

  const toggleSymbol = (sym) => {
    let next;
    if (activeSymbols.includes(sym)) {
      if (activeSymbols.length <= 1) return;
      next = activeSymbols.filter((s) => s !== sym);
    } else {
      if (activeSymbols.length >= 8) return;
      next = [...activeSymbols, sym];
    }
    updateBotSettings(next, selectedTF, null, aiThreshold);
  };

  return (
    <div
      style={{
        position: "absolute",
        top: "calc(100% + 12px)",
        right: 0,
        width: "300px",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "20px",
        padding: "16px",
        boxShadow: "var(--shadow-glow)",
        zIndex: 1000,
        display: "flex",
        flexDirection: "column",
        gap: "6px",
      }}
    >
      <div
        style={{
          padding: "4px 8px 12px",
          fontSize: "11px",
          fontWeight: "800",
          color: "var(--text-sub)",
          textTransform: "uppercase",
          letterSpacing: "1px",
          borderBottom: "1px solid var(--divider)",
        }}
      >
        Quick Asset Selector
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "4px",
          marginTop: "8px",
        }}
      >
        {SUGGESTED.map((sym) => {
          const isActive = activeSymbols.includes(sym);
          return (
            <div
              key={sym}
              onClick={(e) => {
                e.stopPropagation();
                toggleSymbol(sym);
              }}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 14px",
                borderRadius: "14px",
                cursor: "pointer",
                background: isActive
                  ? "var(--primary-light)"
                  : "var(--divider)",
                border: isActive
                  ? "1px solid var(--primary-glow)"
                  : "1px solid transparent",
                transition: "0.2s",
              }}
              className="hover-lift"
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: "10px" }}
              >
                <div
                  style={{
                    width: "40px",
                    display: "flex",
                    justifyContent: "center",
                  }}
                >
                  <AssetIcon symbol={sym} size={18} />
                </div>
                <span
                  style={{
                    fontSize: "14px",
                    fontWeight: "700",
                    color: isActive ? "var(--primary)" : "var(--text-main)",
                  }}
                >
                  {sym}
                </span>
              </div>
              {isActive ? (
                <Trash2 size={14} color="var(--primary)" />
              ) : (
                <Plus size={14} color="var(--text-sub)" />
              )}
            </div>
          );
        })}
      </div>

      {activeSymbols.filter((s) => !SUGGESTED.includes(s)).length > 0 && (
        <>
          <div
            style={{
              height: "1px",
              background: "var(--divider)",
              margin: "12px 0",
            }}
          />
          <div
            style={{
              padding: "0 8px 8px",
              fontSize: "10px",
              fontWeight: "700",
              color: "var(--text-sub)",
              textTransform: "uppercase",
            }}
          >
            Other Active Assets
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {activeSymbols
              .filter((s) => !SUGGESTED.includes(s))
              .map((sym) => (
                <div
                  key={sym}
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSymbol(sym);
                  }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "12px 14px",
                    borderRadius: "14px",
                    cursor: "pointer",
                    background: "var(--primary-light)",
                    border: "1px solid var(--primary-glow)",
                    transition: "0.2s",
                  }}
                  className="hover-lift"
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                    }}
                  >
                    <div
                      style={{
                        width: "40px",
                        display: "flex",
                        justifyContent: "center",
                      }}
                    >
                      <AssetIcon symbol={sym} size={18} />
                    </div>
                    <span
                      style={{
                        fontSize: "14px",
                        fontWeight: "600",
                        color: "var(--primary)",
                      }}
                    >
                      {sym}
                    </span>
                  </div>
                  <Trash2 size={14} color="var(--primary)" />
                </div>
              ))}
          </div>
        </>
      )}
    </div>
  );
}

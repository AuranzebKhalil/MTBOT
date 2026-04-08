"use client";
import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Calendar,
  LayoutDashboard,
  TrendingUp,
  History as HistoryIcon,
  ShieldAlert,
  Settings,
  Power,
  Zap,
  Wallet,
  LogOut,
  ChevronRight,
  ChevronLeft,
  Briefcase,
  Users as UsersIcon,
  MessageSquare,
  ShieldAlert as ShieldIcon,
  TrendingDown
} from "lucide-react";
import { useBot } from "./BotContext";
import { useAuth } from "./AuthContext";
import { useTheme } from "./ThemeContext";
import { useMediaQuery } from "../lib/useMediaQuery";

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const isMobile = useMediaQuery("(max-width: 768px)");

  const {
    isRunning,
    toggleBot,
    isSidebarCollapsed,
    setIsSidebarCollapsed,
    trades,
    setIsEngineSettingsOpen,
    isSidebarHidden,
    setIsSidebarHidden,
  } = useBot();
  const { logout, user } = useAuth();
  const { theme } = useTheme();

  if (!user && pathname !== "/login" && pathname !== "/register") return null;
  if (pathname === "/login" || pathname === "/register") return null;

  const width = isSidebarCollapsed ? "80px" : "280px";
  const openTradesCount = trades?.length || 0;

  const menuItems = [
    {
      id: "intelligence",
      icon: LayoutDashboard,
      label: "Intelligence",
      href: "/",
    },
    {
      id: "portfolio",
      icon: Briefcase,
      label: "Active Portfolio",
      href: "/portfolio",
      badge: openTradesCount,
    },
    { id: "news", icon: Calendar, label: "Economic Calendar", href: "/news" },
    {
      id: "stratagems",
      icon: Zap,
      label: "Active Strategies",
      href: "/stratagems",
    },
    {
      id: "market_depth",
      icon: TrendingUp,
      label: "Market Depth",
      href: "/market-depth",
      hasArrow: true,
    },
    {
      id: "financials",
      icon: Wallet,
      label: "Secured Financials",
      href: "/financials",
    },
    {
      id: "history",
      icon: HistoryIcon,
      label: "Alpha History",
      href: "/history",
    },
    { id: "risk", icon: ShieldAlert, label: "Risk Control", href: "/risk" },
    { id: "settings", icon: Settings, label: "Engine Settings", href: "/settings" },
    { id: "user_support", icon: MessageSquare, label: "Live Support", href: "/support" }
  ];

  const adminItems = [
    { id: "admin_dash", icon: LayoutDashboard, label: "Admin Console", href: "/admin" },
    { id: "admin_users", icon: UsersIcon, label: "User Management", href: "/admin/users" },
    { id: "admin_support", icon: MessageSquare, label: "Global Support", href: "/admin/support" },
    { id: "admin_profits", icon: TrendingUp, label: "Profit Analytics", href: "/admin/profits" },
    { id: "user_view", icon: ShieldIcon, label: "Exit to App", href: "/" },
  ];

  const isAdminPath = pathname.startsWith("/admin");
  const isAdminUser = user?.role === "admin" || user?.role === "superadmin";

  const itemsToRender = (isAdminPath && isAdminUser) ? adminItems : menuItems;

  // Add Admin Panel link to user menu if admin
  const finalItems = isAdminUser && !isAdminPath 
    ? [...itemsToRender, {
        id: "admin_gateway",
        icon: ShieldIcon,
        label: "Admin Dashboard",
        href: "/admin",
        style: { marginTop: 'auto', borderTop: '1px solid var(--border)' }
      }]
    : itemsToRender;

  // Render nothing if hidden on desktop
  if (isSidebarHidden && !isMobile) return null;

  return (
    <aside
      className="sidebar glass-panel no-lift"
      style={{
        width: isMobile ? "280px" : width,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        padding: isSidebarCollapsed ? "32px 12px" : "32px 16px 20px",
        position: isMobile ? "fixed" : "sticky",
        left: isMobile ? (isSidebarHidden ? "-280px" : "0") : "0",
        top: 0,
        background: "var(--surface)",
        borderRight: "1px solid var(--border)",
        boxShadow: isMobile ? "20px 0 50px rgba(0,0,0,0.5)" : "inset -4px 0 24px rgba(0, 0, 0, 0.05)",
        zIndex: 1000,
        transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
        overflow: "hidden",
      }}
    >
      <div
        className="brand-block"
        style={{
          padding: isSidebarCollapsed ? "0 0 40px" : "0 12px 40px",
          display: "flex",
          alignItems: "center",
          gap: "14px",
          justifyContent: isSidebarCollapsed ? "center" : "flex-start",
        }}
      >
        <div
          style={{
            width: "42px",
            height: "42px",
            background: "linear-gradient(135deg, #007aff 0%, #00f2ff 100%)",
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 8px 20px rgba(0, 122, 255, 0.3)",
            flexShrink: 0,
          }}
        >
          <span
            style={{
              color: theme === "dark" ? "#000" : "#fff",
              fontWeight: "700",
              fontSize: "20px",
            }}
          >
            A
          </span>
        </div>
        {!isSidebarCollapsed && (
          <div style={{ display: "flex", flexDirection: "column" }}>
            <h1
              style={{
                fontSize: "18px",
                fontWeight: "600",
                color: "var(--text-main)",
                letterSpacing: "0.5px",
                textTransform: "uppercase",
                margin: 0,
              }}
            >
              Auralith
            </h1>
            <span
              style={{
                fontSize: "9px",
                fontWeight: "600",
                color: "var(--text-sub)",
                letterSpacing: "1px",
                textTransform: "uppercase",
              }}
            >
              Alpha Core V2
            </span>
          </div>
        )}
      </div>

      <nav
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "8px",
          flex: 1,
          overflowY: "auto",
          paddingRight: isSidebarCollapsed ? 0 : "8px",
        }}
        className="custom-scrollbar"
      >
        {finalItems.map((item) => {
          const isActive = pathname === item.href;

          if (item.action) {
            return (
              <div
                key={item.id}
                onClick={item.action}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: isSidebarCollapsed
                    ? "center"
                    : "space-between",
                  padding: "12px 16px",
                  borderRadius: "12px",
                  cursor: "pointer",
                  color: "var(--text-sub)",
                  transition: "all 0.2s ease",
                }}
                className="hover-lift"
              >
                <div
                  style={{ display: "flex", alignItems: "center", gap: "16px" }}
                >
                  <item.icon size={18} strokeWidth={2} />
                  {!isSidebarCollapsed && (
                    <span style={{ fontSize: "14px", fontWeight: "500" }}>
                      {item.label}
                    </span>
                  )}
                </div>
              </div>
            );
          }

          return (
            <Link
              key={item.id}
              href={item.href}
              title={isSidebarCollapsed ? item.label : ""}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: isSidebarCollapsed ? "center" : "space-between",
                padding: "12px 16px",
                borderRadius: "12px",
                textDecoration: "none",
                background: isActive ? "rgba(0,122,255,0.1)" : "transparent",
                color: isActive ? "var(--primary)" : "var(--text-sub)",
                transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                position: "relative",
                margin: isSidebarCollapsed ? "2px 0" : "2px 0",
                border: "1px solid transparent",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255,255,255,0.03)";
                e.currentTarget.style.borderColor = "rgba(255,255,255,0.05)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = isActive
                  ? "rgba(0,122,255,0.1)"
                  : "transparent";
                e.currentTarget.style.borderColor = "transparent";
              }}
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: "16px" }}
              >
                <item.icon
                  size={18}
                  strokeWidth={isActive ? 2.5 : 2}
                  style={{
                    color: isActive ? "var(--primary)" : "var(--text-sub)",
                  }}
                />
                {!isSidebarCollapsed && (
                  <span
                    style={{
                      fontSize: "14px",
                      fontWeight: isActive ? "700" : "500",
                      letterSpacing: "0.2px",
                    }}
                  >
                    {item.label}
                  </span>
                )}
              </div>

              {!isSidebarCollapsed && item.badge !== undefined && (
                <div
                  style={{
                    background: isActive
                      ? "var(--primary)"
                      : "var(--primary-light)",
                    color: isActive
                      ? theme === "dark"
                        ? "#000"
                        : "#fff"
                      : "var(--primary)",
                    fontSize: "11px",
                    fontWeight: "700",
                    padding: "2px 10px",
                    borderRadius: "20px",
                    minWidth: "20px",
                    textAlign: "center",
                    boxShadow: isActive
                      ? "0 4px 12px var(--primary-glow)"
                      : "none",
                  }}
                >
                  {item.badge}
                </div>
              )}

              {isSidebarCollapsed && item.badge !== undefined && (
                <div
                  style={{
                    position: "absolute",
                    top: "6px",
                    right: "6px",
                    background: "var(--primary)",
                    color: theme === "dark" ? "#000" : "#fff",
                    fontSize: "9px",
                    fontWeight: "700",
                    width: "18px",
                    height: "18px",
                    borderRadius: "50%",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    border: "2px solid var(--surface)",
                    boxShadow: "0 4px 10px rgba(0,0,0,0.2)",
                  }}
                >
                  {item.badge}
                </div>
              )}

              {!isSidebarCollapsed && item.hasArrow && (
                <ChevronRight size={14} style={{ opacity: 0.3 }} />
              )}
            </Link>
          );
        })}
      </nav>

      <div
        className="sidebar-footer"
        style={{
          marginTop: "auto",
          borderTop: "1px solid var(--border)",
          paddingTop: "24px",
          display: isSidebarCollapsed ? "flex" : "block",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        {!isSidebarCollapsed && (
          <>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                padding: "0 8px 16px",
              }}
            >
              <span
                style={{
                  fontSize: "11px",
                  fontWeight: "700",
                  color: "var(--text-sub)",
                  textTransform: "uppercase",
                  letterSpacing: "1px",
                }}
              >
                Autotrade
              </span>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  marginLeft: "auto",
                }}
              >
                <div
                  onClick={toggleBot}
                  style={{
                    width: "42px",
                    height: "20px",
                    background: isRunning ? "var(--success)" : "var(--divider)",
                    borderRadius: "12px",
                    position: "relative",
                    cursor: "pointer",
                    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                  }}
                >
                  <div
                    style={{
                      width: "14px",
                      height: "14px",
                      background: "#fff",
                      borderRadius: "50%",
                      position: "absolute",
                      top: "3px",
                      left: isRunning ? "25px" : "3px",
                      transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                      boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                    }}
                  />
                </div>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: "700",
                    color: isRunning ? "var(--success)" : "var(--text-sub)",
                    minWidth: "24px",
                  }}
                >
                  {isRunning ? "ON" : "OFF"}
                </span>
              </div>
            </div>

            <button
              onClick={toggleBot}
              style={{
                width: "100%",
                padding: "16px",
                borderRadius: "14px",
                background: "transparent",
                border: "1px solid var(--danger)",
                color: "var(--danger)",
                fontWeight: "700",
                fontSize: "14px",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "12px",
                transition: "all 0.2s ease",
                boxShadow: "0 4px 20px rgba(255,69,58,0.05)",
              }}
              className="hover-lift"
            >
              <Power size={18} />
              {isRunning ? "HALT ENGINE" : "RESUME QUANT"}
            </button>
          </>
        )}

        {isSidebarCollapsed && (
          <button
            onClick={toggleBot}
            style={{
              width: "48px",
              height: "48px",
              border: "1px solid var(--danger)",
              borderRadius: "14px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--danger)",
              background: "transparent",
              marginBottom: "20px",
              cursor: "pointer",
            }}
            className="hover-lift"
          >
            <Power size={20} />
          </button>
        )}

        <div
          style={{
            display: "flex",
            justifyContent: isSidebarCollapsed ? "center" : "space-between",
            marginTop: isSidebarCollapsed ? "0" : "20px",
            paddingBottom: "10px",
            width: "100%",
          }}
        >
          <button
            style={{
              background: "transparent",
              border: "none",
              color: "var(--text-sub)",
              cursor: "pointer",
            }}
            onClick={logout}
            title="Logout"
            className="hover-lift"
          >
            <LogOut size={18} />
          </button>
          <button
            onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
            style={{
              background: "var(--divider)",
              border: "1px solid var(--border)",
              color: "var(--text-sub)",
              cursor: "pointer",
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            className="hover-lift"
            title={isSidebarCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}
          >
            {isSidebarCollapsed ? (
              <ChevronRight size={18} />
            ) : (
              <ChevronLeft size={18} />
            )}
          </button>
        </div>
      </div>
    </aside>
  );
}

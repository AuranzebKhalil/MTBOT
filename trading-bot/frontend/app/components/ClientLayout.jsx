"use client";
import React from "react";
import { Toaster } from "react-hot-toast";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { BotProvider, useBot } from "./BotContext";
import { AuthProvider } from "./AuthContext";
import { ThemeProvider } from "./ThemeContext";
import { useMediaQuery } from "../lib/useMediaQuery";
import StoreProvider from "../StoreProvider";

function LayoutContent({ children }) {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const { isSidebarCollapsed, isSidebarHidden, setIsSidebarHidden } = useBot();
  
  // Auto-hide sidebar on mobile resize
  React.useEffect(() => {
    if (isMobile) {
      setIsSidebarHidden(true);
    } else {
      setIsSidebarHidden(false);
    }
  }, [isMobile, setIsSidebarHidden]);

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        background: "var(--background)",
        position: "relative",
        overflow: "hidden"
      }}
    >
      {!isSidebarHidden && <Sidebar />}

      {/* Overlay for mobile sidebar */}
      {!isSidebarHidden && isMobile && (
        <div 
          onClick={() => setIsSidebarHidden(true)}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            backdropFilter: "blur(4px)",
            zIndex: 90,
            transition: "opacity 0.3s"
          }}
        />
      )}

      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
          width: "100%",
          overflow: "hidden",
          position: "relative"
        }}
      >
        <div style={{ 
          position: "absolute", 
          top: 0, 
          left: 0, 
          right: 0, 
          zIndex: 100 
        }}>
          <Header />
        </div>
        
        <div 
          className="custom-scrollbar"
          style={{ 
            flex: 1, 
            width: "100%", 
            overflowY: "auto",
            paddingTop: isMobile ? "70px" : "80px",
            background: "var(--background)"
          }}
        >
          <div style={{ padding: isMobile ? "12px" : isSidebarHidden ? "16px 24px" : "24px 32px" }}>
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}

export default function ClientLayout({ children }) {
  return (
    <StoreProvider>
      <ThemeProvider>
        <AuthProvider>
          <BotProvider>
            <Toaster
              position="bottom-center"
              toastOptions={{
                style: {
                  background: "var(--bg-card)",
                  color: "var(--text-main)",
                  border: "1px solid var(--border)",
                  borderRadius: "16px",
                  padding: "16px 24px",
                  fontWeight: "700",
                  fontSize: "14px",
                  boxShadow: "var(--shadow-glow)",
                },
              }}
            />
            <LayoutContent>{children}</LayoutContent>
          </BotProvider>
        </AuthProvider>
      </ThemeProvider>
    </StoreProvider>
  );
}

"use client";
import React from "react";
import "./globals.css";
import { Toaster } from "react-hot-toast";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import { BotProvider, useBot } from "./components/BotContext";
import { AuthProvider } from "./components/AuthContext";
import { ThemeProvider } from "./components/ThemeContext";
import { useMediaQuery } from "./lib/useMediaQuery";
import StoreProvider from "./StoreProvider";

function LayoutContent({ children }) {
  const isMobile = useMediaQuery("(max-width: 768px)");
  const { isSidebarCollapsed, isSidebarHidden, setIsSidebarHidden } = useBot();
  
  const sidebarWidth = isSidebarHidden
    ? "0px"
    : isSidebarCollapsed
      ? "80px"
      : "280px";

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
          padding: isMobile ? "16px 16px" : isSidebarHidden ? "16px 24px" : "24px 32px",
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          overflowY: "auto",
          transition: "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)",
          width: "100%"
        }}
        className="custom-scrollbar"
      >
        <Header />
        <div style={{ flex: 1, width: "100%" }}>{children}</div>
      </main>
    </div>
  );
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="true"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
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
        <StoreProvider>
          <ThemeProvider>
            <AuthProvider>
              <BotProvider>
                <LayoutContent>{children}</LayoutContent>
              </BotProvider>
            </AuthProvider>
          </ThemeProvider>
        </StoreProvider>
      </body>
    </html>
  );
}

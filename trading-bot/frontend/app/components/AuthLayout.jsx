"use client";
import React from "react";
import AuthImageCarousel from "./AuthImageCarousel";
import { ShieldCheck } from "lucide-react";

export default function AuthLayout({ children }) {
  return (
    <div
      style={{
        minHeight: "100vh",
        maxHeight: "100vh",
        display: "flex",
        overflow: "hidden",
        background: "#05070a",
        color: "white",
        fontFamily: "'Inter', sans-serif",
      }}
    >
      {/* Left Section: Image Carousel (Hidden on small screens) */}
      <div
        style={{
          flex: "1.2",
          position: "relative",
        }}
        className="auth-carousel-container"
      >
        <AuthImageCarousel />
      </div>

      {/* Right Section: Form Content */}
      <div
        style={{
          flex: "1",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "40px",
          position: "relative",
          background:
            "radial-gradient(circle at 70% 30%, rgba(0, 122, 255, 0.05), transparent)",
        }}
      >
        {/* Background Decorative Blur */}
        <div
          style={{
            position: "absolute",
            top: "10%",
            right: "10%",
            width: "300px",
            height: "300px",
            background: "var(--primary)",
            filter: "blur(120px)",
            opacity: 0.1,
            borderRadius: "50%",
            zIndex: 0,
          }}
        />

        <div
          style={{
            width: "100%",
            maxWidth: "400px",
            zIndex: 1,
          }}
        >
          {children}
        </div>

        {/* Footer info */}
        <div
          style={{
            position: "absolute",
            bottom: "40px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            color: "rgba(255,255,255,0.3)",
            fontSize: "0.75rem",
            letterSpacing: "1.5px",
            fontWeight: "700",
          }}
        >
          <ShieldCheck size={14} color="#10b981" /> SECURE PROTOCOL v4.2 //
          ENCRYPTED
        </div>
      </div>

      {/* Small style tag for media query */}
      <style jsx>{`
        @media (max-width: 1024px) {
          .auth-carousel-container {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}

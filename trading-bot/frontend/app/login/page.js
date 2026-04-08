"use client";
import React, { useState } from "react";
import { useAuth } from "../components/AuthContext";
import Link from "next/link";
import {
  Zap,
  Mail,
  Lock,
  ShieldCheck,
  ArrowRight,
  Loader2,
} from "lucide-react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await login(email, password);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        position: "relative",
        overflow: "hidden",
        background: "#05070a",
      }}
    >
      {/* Decorative pulse glow */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: "500px",
          height: "500px",
          background: "var(--primary)",
          filter: "blur(150px)",
          opacity: 0.1,
          borderRadius: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 0,
        }}
      />

      <div
        className="glass-panel"
        style={{
          width: "100%",
          maxWidth: "440px",
          padding: "48px 40px",
          borderRadius: "32px",
          zIndex: 1,
          background: "rgba(13, 17, 23, 0.7)",
          backdropFilter: "blur(20px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          boxShadow: "0 40px 100px rgba(0, 0, 0, 0.4)",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <div
            style={{
              width: "80px",
              height: "80px",
              background: "var(--gradient-primary)",
              borderRadius: "24px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 24px",
              boxShadow: "0 20px 40px rgba(0, 122, 255, 0.3)",
              padding: "16px",
            }}
          >
            <img
              src="/logo/alertli_logo.png"
              alt="Alertli"
              style={{ width: "100%", height: "100%", objectFit: "contain" }}
            />
          </div>
          <h1
            style={{
              fontSize: "2rem",
              fontWeight: "900",
              color: "white",
              marginBottom: "8px",
              letterSpacing: "-1px",
            }}
          >
            ALERTLI <span style={{ color: "var(--primary)" }}>ALPHA</span>
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
            Secure Operator Authorization
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "24px" }}
        >
          <div style={{ position: "relative" }}>
            <Mail
              size={18}
              style={{
                position: "absolute",
                left: "16px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
                opacity: 0.6,
              }}
            />
            <input
              type="email"
              placeholder="Operator ID / Email"
              required
              autoComplete="off"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: "100%",
                padding: "16px 16px 16px 48px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "16px",
                color: "white",
                fontSize: "15px",
                outline: "none",
                transition: "border-color 0.3s",
              }}
              onFocus={(e) => (e.target.style.borderColor = "var(--primary)")}
              onBlur={(e) =>
                (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")
              }
            />
          </div>

          <div style={{ position: "relative" }}>
            <Lock
              size={18}
              style={{
                position: "absolute",
                left: "16px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-muted)",
                opacity: 0.6,
              }}
            />
            <input
              type="password"
              placeholder="Security Key"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: "100%",
                padding: "16px 16px 16px 48px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "16px",
                color: "white",
                fontSize: "15px",
                outline: "none",
                transition: "border-color 0.3s",
              }}
              onFocus={(e) => (e.target.style.borderColor = "var(--primary)")}
              onBlur={(e) =>
                (e.target.style.borderColor = "rgba(255, 255, 255, 0.1)")
              }
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              padding: "18px",
              borderRadius: "16px",
              background: "var(--gradient-primary)",
              color: "white",
              border: "none",
              fontSize: "1rem",
              fontWeight: "800",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "12px",
              transition: "transform 0.2s, box-shadow 0.2s",
              boxShadow: "0 10px 30px rgba(0, 122, 255, 0.2)",
              opacity: isSubmitting ? 0.7 : 1,
            }}
            onMouseOver={(e) => {
              e.target.style.transform = "translateY(-2px)";
              e.target.style.boxShadow = "0 15px 40px rgba(0, 122, 255, 0.4)";
            }}
            onMouseOut={(e) => {
              e.target.style.transform = "translateY(0)";
              e.target.style.boxShadow = "0 10px 30px rgba(0, 122, 255, 0.2)";
            }}
          >
            {isSubmitting ? (
              <Loader2 size={24} className="animate-spin" />
            ) : (
              <>
                ENGAGE SESSION <ArrowRight size={20} />
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: "32px", textAlign: "center" }}>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Not an authorized operator?{" "}
            <Link
              href="/register"
              style={{
                color: "var(--primary)",
                fontWeight: "700",
                textDecoration: "none",
              }}
            >
              Apply for License
            </Link>
          </p>
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          bottom: "30px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
          color: "var(--text-muted)",
          fontSize: "0.8rem",
          letterSpacing: "1px",
        }}
      >
        <ShieldCheck size={14} color="#10b981" /> ENCRYPTED PROTOCOL ACTIVE
      </div>
    </div>
  );
}

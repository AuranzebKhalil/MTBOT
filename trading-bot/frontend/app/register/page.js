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
  UserPlus,
} from "lucide-react";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password !== confirmPassword) return alert("Passwords do not match");

    setIsSubmitting(true);
    try {
      await register(email, password);
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
          background: "var(--accent)",
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
          <div>
            <img
              src="/logo/AuraLithLogo.png"
              alt="Alertli"
              style={{ width: "150px", height: "150px", objectFit: "contain" }}
            />
          </div>

          <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
            Sign up with use to make money
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "20px" }}
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
              placeholder="Operational Email Address"
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
              }}
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
              placeholder="Define Security Key"
              required
              autoComplete="new-password"
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
              }}
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
              placeholder="Confirm Security Key"
              required
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              style={{
                width: "100%",
                padding: "16px 16px 16px 48px",
                background: "rgba(255, 255, 255, 0.03)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "16px",
                color: "white",
                fontSize: "15px",
                outline: "none",
              }}
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
              boxShadow: "0 10px 30px rgba(0, 122, 255, 0.2)",
              marginTop: "10px",
            }}
          >
            {isSubmitting ? (
              <Loader2 size={24} className="animate-spin" />
            ) : (
              <>
                Register <UserPlus size={20} />
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: "32px", textAlign: "center" }}>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            Already an operator?{" "}
            <Link
              href="/login"
              style={{
                color: "var(--primary)",
                fontWeight: "700",
                textDecoration: "none",
              }}
            >
              Engage Session
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

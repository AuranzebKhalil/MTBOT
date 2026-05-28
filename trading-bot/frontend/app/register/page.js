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

import AuthLayout from "../components/AuthLayout";

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
    <AuthLayout>
      {/* Logo & Header */}
      <div style={{ textAlign: "left", marginBottom: "40px" }}>
        <img
          src="/logo/AuraLithLogo.png"
          alt="AuraLith"
          style={{
            width: "80px",
            height: "80px",
            objectFit: "contain",
            marginBottom: "24px",
          }}
        />
        <h1
          style={{
            fontSize: "2.5rem",
            fontWeight: "900",
            marginBottom: "12px",
            letterSpacing: "-1px",
          }}
        >
          Join the Grid
        </h1>
        <p
          style={{
            color: "var(--text-muted)",
            fontSize: "1.1rem",
            opacity: 0.7,
          }}
        >
          Create your operator account to begin automated execution.
        </p>
      </div>

          <form
            onSubmit={handleSubmit}
            style={{ display: "flex", flexDirection: "column", gap: "20px" }}
          >
            <div
              style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
              <label
                style={{
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  color: "var(--text-muted)",
                  marginLeft: "4px",
                }}
              >
                OPERATIONAL EMAIL
              </label>
              <div style={{ position: "relative" }}>
                <Mail
                  size={18}
                  style={{
                    position: "absolute",
                    left: "16px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "rgba(255,255,255,0.4)",
                  }}
                />
                <input
                  type="email"
                  placeholder="operator@auralith.ai"
                  required
                  autoComplete="off"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "16px 16px 16px 48px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "14px",
                    color: "white",
                    fontSize: "15px",
                    outline: "none",
                    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                  }}
                />
              </div>
            </div>

            <div
              style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
              <label
                style={{
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  color: "var(--text-muted)",
                  marginLeft: "4px",
                }}
              >
                DEFINE SECURITY KEY
              </label>
              <div style={{ position: "relative" }}>
                <Lock
                  size={18}
                  style={{
                    position: "absolute",
                    left: "16px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "rgba(255,255,255,0.4)",
                  }}
                />
                <input
                  type="password"
                  placeholder="Create a strong key"
                  required
                  autoComplete="new-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "16px 16px 16px 48px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "14px",
                    color: "white",
                    fontSize: "15px",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            <div
              style={{ display: "flex", flexDirection: "column", gap: "8px" }}
            >
              <label
                style={{
                  fontSize: "0.85rem",
                  fontWeight: "600",
                  color: "var(--text-muted)",
                  marginLeft: "4px",
                }}
              >
                CONFIRM SECURITY KEY
              </label>
              <div style={{ position: "relative" }}>
                <Lock
                  size={18}
                  style={{
                    position: "absolute",
                    left: "16px",
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "rgba(255,255,255,0.4)",
                  }}
                />
                <input
                  type="password"
                  placeholder="Repeat your key"
                  required
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "16px 16px 16px 48px",
                    background: "rgba(255, 255, 255, 0.05)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "14px",
                    color: "white",
                    fontSize: "15px",
                    outline: "none",
                  }}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                marginTop: "10px",
                padding: "18px",
                borderRadius: "14px",
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
                transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                boxShadow: "0 10px 30px rgba(0, 122, 255, 0.3)",
                opacity: isSubmitting ? 0.7 : 1,
              }}
            >
              {isSubmitting ? (
                <Loader2 size={24} className="animate-spin" />
              ) : (
                <>
                  Initialize Account <UserPlus size={20} />
                </>
              )}
            </button>
          </form>

          <div
            style={{
              marginTop: "40px",
              textAlign: "center",
              padding: "24px",
              borderRadius: "16px",
              background: "rgba(255,255,255,0.02)",
              border: "1px solid rgba(255,255,255,0.05)",
            }}
          >
            <p style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>
              Already an authorized operator?{" "}
              <Link
                href="/login"
                style={{
                  color: "var(--primary)",
                  fontWeight: "700",
                  textDecoration: "none",
                  paddingBottom: "2px",
                  borderBottom: "2px solid rgba(0, 122, 255, 0.3)",
                }}
              >
                Engage Session
              </Link>
            </p>
          </div>
    </AuthLayout>
  );
}

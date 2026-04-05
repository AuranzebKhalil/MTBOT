"use client";
import React, { useState } from "react";
import { useAuth } from "../components/AuthContext";
import Link from "next/link";
import { UserPlus, Mail, Lock } from "lucide-react";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { register } = useAuth();

  const handleSubmit = (e) => {
    e.preventDefault();
    register(email, password);
  };

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        background: "var(--background)",
        padding: "20px"
      }}
    >
      <div
        className="glass-panel animate-fade-in"
        style={{
          padding: "40px 30px",
          width: "100%",
          maxWidth: "420px",
          textAlign: "center",
          background: "var(--surface)",
          borderRadius: "32px",
          boxShadow: "0 40px 100px rgba(0,0,0,0.5)"
        }}
      >
        <div
          style={{
            width: "72px",
            height: "72px",
            background: "var(--gradient-primary)",
            borderRadius: "20px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            margin: "0 auto 30px",
            boxShadow: "0 15px 35px rgba(91, 134, 229, 0.4)",
            overflow: "hidden",
            border: "1px solid rgba(255,255,255,0.15)",
          }}
        >
          <img
            src="/logo/alertli_logo.png"
            alt="Alertli Logo"
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </div>

        <h2
          style={{
            fontSize: "32px",
            fontWeight: "900",
            marginBottom: "10px",
            color: "var(--text-main)",
            letterSpacing: "-1px",
          }}
        >
          ALERTLI <span className="text-gradient">ACCOUNT</span>
        </h2>
        <p
          style={{
            color: "var(--text-sub)",
            fontSize: "15px",
            fontWeight: "500",
            marginBottom: "35px",
          }}
        >
          Create your quantitative institutional profile.
        </p>

        <form
          onSubmit={handleSubmit}
          style={{ display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <div style={{ position: "relative" }}>
            <Mail
              size={18}
              style={{
                position: "absolute",
                left: "18px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-sub)",
                opacity: 0.5,
              }}
            />
            <input
              type="email"
              placeholder="Operator Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "16px 16px 16px 50px",
                background: "var(--glass-bg)",
                border: "1px solid var(--glass-border)",
                borderRadius: "14px",
                color: "var(--text-main)",
                fontSize: "14px",
                fontWeight: "500",
                outline: "none",
              }}
            />
          </div>

          <div style={{ position: "relative" }}>
            <Lock
              size={18}
              style={{
                position: "absolute",
                left: "18px",
                top: "50%",
                transform: "translateY(-50%)",
                color: "var(--text-sub)",
                opacity: 0.5,
              }}
            />
            <input
              type="password"
              placeholder="Secure Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "16px 16px 16px 50px",
                background: "var(--glass-bg)",
                border: "1px solid var(--glass-border)",
                borderRadius: "14px",
                color: "var(--text-main)",
                fontSize: "14px",
                fontWeight: "500",
                outline: "none",
              }}
            />
          </div>

          <button
            type="submit"
            style={{
              background: "var(--text-main)",
              color: "var(--background)",
              padding: "18px",
              borderRadius: "14px",
              border: "none",
              fontSize: "15px",
              fontWeight: "800",
              cursor: "pointer",
              marginTop: "10px",
              transition:
                "transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275)",
            }}
            className="hover-lift"
          >
            CREATE ACCOUNT
          </button>
        </form>

        <p
          style={{
            marginTop: "30px",
            fontSize: "14px",
            color: "var(--text-sub)",
            fontWeight: "500",
          }}
        >
          Already registered?{" "}
          <Link
            href="/login"
            style={{
              color: "var(--primary)",
              textDecoration: "none",
              fontWeight: "700",
            }}
          >
            Login Here
          </Link>
        </p>
      </div>
    </div>
  );
}

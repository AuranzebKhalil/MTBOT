"use client";
import React, { useEffect } from "react";
import { useAuth } from "../components/AuthContext";
import { useRouter } from "next/navigation";

export default function AdminLayout({ children }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    const hasToken = typeof window !== 'undefined' && localStorage.getItem("quant_token");
    
    if (!loading) {
      if (!hasToken) {
        router.push("/login");
      } else if (user && user.role !== "admin" && user.role !== "superadmin") {
        router.push("/");
      }
    }
  }, [user, loading, router]);

  const hasToken = typeof window !== 'undefined' && localStorage.getItem("quant_token");

  if (loading || (hasToken && !user)) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#020408',
        color: 'white',
        gap: '2rem'
      }}>
        <div style={{ 
          width: '48px', 
          height: '48px', 
          border: '3px solid rgba(255,255,255,0.1)', 
          borderTopColor: 'white', 
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <div style={{ letterSpacing: '2px', fontWeight: '800', fontSize: '0.9rem', opacity: 0.5 }}>AUTHORIZING MISSION CONTROL...</div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!user || (user.role !== "admin" && user.role !== "superadmin")) {
    return null; // Component will redirect via useEffect
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      {children}
    </div>
  );
}

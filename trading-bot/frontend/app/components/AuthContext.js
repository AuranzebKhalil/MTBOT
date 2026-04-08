"use client";
import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import toast from "react-hot-toast";
import { getApiBaseUrl } from "../lib/config";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const storedToken = localStorage.getItem("quant_token");
    const isPublicPath = pathname === "/login" || pathname === "/register";

    if (storedToken) {
      setToken(storedToken);
      fetchUser(storedToken);
    } else {
      if (!isPublicPath) router.push("/login");
      setLoading(false);
    }
  }, [pathname]);

  const fetchUser = async (authToken) => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/v1/auth/me`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data);
        return true;
      } else if (res.status === 401) {
        logout();
        return false;
      }
      return false;
    } catch (err) {
      console.error("Profile Fetch Exception:", err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      const res = await fetch(`${getApiBaseUrl()}/v1/auth/token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: params,
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("quant_token", data.access_token);
        setToken(data.access_token);
        const success = await fetchUser(data.access_token);
        if (success) {
           toast.success("Welcome back, Quant");
           router.push("/");
        } else {
           toast.error("Account Profile Fault. Reload required.");
        }
      } else {
        const data = await res.json().catch(() => ({}));
        toast.error(data.detail || "Invalid Credentials");
      }
    } catch (err) {
      toast.error("Auth Server Offline");
    }
  };

  const register = async (email, password) => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (res.ok) {
        toast.success("Account Created. Please Login.");
        router.push("/login");
      } else {
        const data = await res.json();
        toast.error(data.detail || "Registration Failed");
      }
    } catch (err) {
      toast.error("Engine Fault during Registration");
    }
  };

  const logout = () => {
    localStorage.removeItem("quant_token");
    setToken(null);
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{ user, token, login, register, logout, loading }}
    >
      {!loading && children}
      {user?.is_breached && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.9)',
          backdropFilter: 'blur(10px)',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          textAlign: 'center'
        }}>
          <div style={{
            background: 'var(--bg-card)',
            border: '2px solid #ef4444',
            padding: '3rem',
            borderRadius: '24px',
            maxWidth: '500px',
            boxShadow: '0 0 50px rgba(239, 68, 68, 0.3)'
          }}>
            <h1 style={{ color: '#ef4444', fontSize: '2rem', marginBottom: '1rem', fontWeight: '900' }}>ACCOUNT SUSPENDED</h1>
            <p style={{ fontSize: '1.1rem', color: 'var(--text-main)', marginBottom: '2rem', lineHeight: '1.6' }}>
              Your account has been suspended by the Risk Control department. Access to the trading infrastructure is currently restricted.
            </p>
            <button 
              onClick={() => router.push('/support')}
              style={{
                background: '#ef4444',
                color: 'white',
                border: 'none',
                padding: '12px 32px',
                borderRadius: '12px',
                fontWeight: '700',
                cursor: 'pointer'
              }}>
              Contact Support
            </button>
            <div style={{ marginTop: '1.5rem' }}>
               <button onClick={logout} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', textDecoration: 'underline' }}>Log Out</button>
            </div>
          </div>
        </div>
      )}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

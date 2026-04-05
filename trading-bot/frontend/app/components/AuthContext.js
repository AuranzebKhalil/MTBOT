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
      setUser({ email: "active_session" });
    } else if (!isPublicPath) {
      router.push("/login");
    }
    setLoading(false);
  }, [pathname]);

  const login = async (email, password) => {
    try {
      const params = new URLSearchParams();
      params.append("username", email);
      params.append("password", password);

      const res = await fetch(`${getApiBaseUrl()}/token`, {
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
        setUser({ email });
        toast.success("Welcome back, Quant");
        router.push("/");
      } else {
        toast.error("Invalid Credentials");
      }
    } catch (err) {
      toast.error("Auth Server Offline");
    }
  };

  const register = async (email, password) => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/register`, {
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
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("wakaless_user");
    if (stored) setUser(JSON.parse(stored));
    setReady(true);
  }, []);

  function applySession(token, user) {
    localStorage.setItem("wakaless_token", token);
    localStorage.setItem("wakaless_user", JSON.stringify(user));
    setUser(user);
  }

  async function signup(payload) {
    const data = await api.signup(payload);
    applySession(data.access_token, data.user);
    return data.user;
  }

  async function login(payload) {
    const data = await api.login(payload);
    applySession(data.access_token, data.user);
    return data.user;
  }

  function logout() {
    localStorage.removeItem("wakaless_token");
    localStorage.removeItem("wakaless_user");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, ready, signup, login, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

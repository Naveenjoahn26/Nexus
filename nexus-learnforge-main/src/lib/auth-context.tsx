import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { auth as authApi, userApi, getToken, setToken } from "@/api";
import type { User } from "@/api";

type AuthState = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (p: { email: string; full_name: string; password: string }) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthCtx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const u = await userApi.me();
      setUser(u);
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const login = async (email: string, password: string) => {
    await authApi.login(email, password);
    await refresh();
  };

  const register = async (p: { email: string; full_name: string; password: string }) => {
    await authApi.register(p);
    await login(p.email, p.password);
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
  };

  return (
    <AuthCtx.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthCtx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

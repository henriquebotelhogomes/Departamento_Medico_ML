import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchMe, login as apiLogin, tokenStore } from "@/lib/api";
import type { User } from "@/lib/types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!tokenStore.access) {
      setUser(null);
      return;
    }
    try {
      setUser(await fetchMe());
    } catch {
      logout();
    }
  }, [logout]);

  const login = useCallback(
    async (username: string, password: string) => {
      const pair = await apiLogin(username, password);
      tokenStore.set(pair);
      setUser(await fetchMe());
    },
    [],
  );

  useEffect(() => {
    void refreshUser().finally(() => setLoading(false));
  }, [refreshUser]);

  useEffect(() => {
    const handler = () => logout();
    window.addEventListener("radioai:logout", handler);
    return () => window.removeEventListener("radioai:logout", handler);
  }, [logout]);

  const value = useMemo(
    () => ({ user, loading, login, logout, refreshUser }),
    [user, loading, login, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

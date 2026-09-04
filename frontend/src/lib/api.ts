import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";
import type {
  PredictionListOut,
  PredictionOut,
  PredictionResult,
  ReportRequest,
  ReportResponse,
  StatsOut,
  TokenPair,
  User,
} from "./types";

const ACCESS_KEY = "radioai_access";
const REFRESH_KEY = "radioai_refresh";

export const tokenStore = {
  get access() {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(pair: TokenPair) {
    localStorage.setItem(ACCESS_KEY, pair.access_token);
    localStorage.setItem(REFRESH_KEY, pair.refresh_token);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

const baseURL = `${import.meta.env.VITE_API_URL ?? ""}/api`;

export const api: AxiosInstance = axios.create({ baseURL });

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.access;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = tokenStore.refresh;
  if (!refresh) return null;
  try {
    const { data } = await axios.post<TokenPair>(`${baseURL}/auth/refresh`, {
      refresh_token: refresh,
    });
    tokenStore.set(data);
    return data.access_token;
  } catch {
    tokenStore.clear();
    return null;
  }
}

api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };
    const isAuthCall = original?.url?.includes("/auth/");
    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      refreshing = refreshing ?? refreshAccessToken();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
      if (typeof window !== "undefined") {
        window.dispatchEvent(new Event("radioai:logout"));
      }
    }
    return Promise.reject(error);
  },
);

export function apiError(error: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 429) {
      return (
        error.response?.data?.detail ||
        error.response?.data?.error ||
        "Muitas requisições em pouco tempo. Por favor, aguarde alguns segundos antes de tentar novamente."
      );
    }
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    const err = error.response?.data?.error;
    if (typeof err === "string") return err;
    return error.message || fallback;
  }
  return fallback;
}

// ---- Endpoint helpers ----

export async function login(username: string, password: string): Promise<TokenPair> {
  const body = new URLSearchParams({ username, password });
  const { data } = await api.post<TokenPair>("/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
  return data;
}

export async function register(
  username: string,
  email: string,
  password: string,
): Promise<User> {
  const { data } = await api.post<User>("/auth/register", { username, email, password });
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function predict(file: File): Promise<PredictionResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post<PredictionResult>("/predictions", form);
  return data;
}

export const predictImage = predict;

export interface HistoryParams {
  page?: number;
  page_size?: number;
  predicted_class?: number;
  date_from?: string;
  date_to?: string;
}

export async function fetchHistory(params: HistoryParams): Promise<PredictionListOut> {
  const { data } = await api.get<PredictionListOut>("/predictions", { params });
  return data;
}

export async function fetchPrediction(id: number): Promise<PredictionOut> {
  const { data } = await api.get<PredictionOut>(`/predictions/${id}`);
  return data;
}

export async function deletePrediction(id: number): Promise<void> {
  await api.delete(`/predictions/${id}`);
}

export async function fetchStats(): Promise<StatsOut> {
  const { data } = await api.get<StatsOut>("/stats");
  return data;
}

export async function generateReport(payload: ReportRequest): Promise<ReportResponse> {
  const { data } = await api.post<ReportResponse>("/predictions/report", payload);
  return data;
}

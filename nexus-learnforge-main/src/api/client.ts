import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const DEFAULT_BASE = "https://nexus-ai-b1gb.onrender.com";

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem("nexus_api_base");
    if (stored) return stored.replace(/\/$/, "");
  }
  const env =
    (import.meta.env.VITE_API_URL as string | undefined) ??
    (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
    DEFAULT_BASE;
  return env.replace(/\/$/, "");
}

export function setApiBase(url: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem("nexus_api_base", url.replace(/\/$/, ""));
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("nexus_token");
}
export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem("nexus_token", token);
  else window.localStorage.removeItem("nexus_token");
}

export const apiClient = axios.create({
  baseURL: `${getApiBase()}/api/v1`,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  config.baseURL = `${getApiBase()}/api/v1`;
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    // Some backend endpoints return { success: true, data: { ... } }
    // Unwrap the data object if success is true and data exists
    if (response.data && response.data.success !== undefined) {
      if (response.data.success && response.data.data !== undefined) {
        return response.data.data;
      }
      return response.data;
    }
    return response.data;
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Unauthorized: clear token and force re-login
      setToken(null);
      if (typeof window !== "undefined" && window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    
    // Extract readable error message from response if available
    let message = error.message;
    if (error.response?.data && typeof error.response.data === 'object') {
        const data = error.response.data as Record<string, any>;
        if (data.error) message = String(data.error);
        else if (data.detail) message = String(data.detail);
    }
    
    return Promise.reject(new Error(message));
  }
);

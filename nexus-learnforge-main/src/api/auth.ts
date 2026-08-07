import { apiClient, setToken } from "./client";

export const auth = {
  register: (p: { email: string; full_name: string; password: string }) =>
    apiClient.post("/auth/register", p),
  login: async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    const res: any = await apiClient.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    setToken(res.access_token);
    return res;
  },
  logout: () => setToken(null),
};

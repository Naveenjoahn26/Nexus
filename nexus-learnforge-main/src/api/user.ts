import { apiClient } from "./client";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "student" | "professor" | "admin";
};

export const userApi = {
  me: () => apiClient.get<User, User>("/auth/me"),
};

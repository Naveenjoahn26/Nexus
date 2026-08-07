import { apiClient } from "./client";

export const notes = {
  lecture: (p: { topic: string; additional_instructions?: string }) =>
    apiClient.post<Record<string, unknown>, Record<string, unknown>>("/generate/lecture", p),
  summary: (p: { topic: string; additional_instructions?: string }) =>
    apiClient.post<Record<string, unknown>, Record<string, unknown>>("/generate/summary", p),
  analysis: (p: { topic: string; additional_instructions?: string }) =>
    apiClient.post<Record<string, unknown>, Record<string, unknown>>("/generate/analysis", p),
};

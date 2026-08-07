import { apiClient } from "./client";

export const quiz = {
  questionPaper: (p: { topic: string; additional_instructions?: string }) =>
    apiClient.post<Record<string, unknown>, Record<string, unknown>>("/generate/question-paper", p),
  presentation: (p: { topic: string; additional_instructions?: string; num_slides?: number }) =>
    apiClient.post<{ download_url?: string } & Record<string, unknown>, { download_url?: string } & Record<string, unknown>>("/generate/presentation", p),
};

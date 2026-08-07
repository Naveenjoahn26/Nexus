import { apiClient } from "./client";

export type Conversation = { id: string; title?: string; updated_at?: string };

export const chat = {
  send: (message: string) =>
    apiClient.post<{ content: string; conversation_id: string; message_id: string }, { content: string; conversation_id: string; message_id: string }>("/chat", { message }),
  conversations: () => apiClient.get<Conversation[], Conversation[]>("/chat/conversations"),
  removeConversation: (id: string) =>
    apiClient.delete<{ success: boolean }, { success: boolean }>(`/chat/conversations/${id}`),
};

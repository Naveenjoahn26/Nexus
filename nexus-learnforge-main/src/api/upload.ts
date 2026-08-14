import { apiClient } from "./client";

export type Document = { id: string; filename: string; chunks?: number };

export const upload = {
  uploadFile: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return apiClient.post<Document, Document>("/documents/upload", fd);
  },
  removeFile: (id: string) => apiClient.delete<{ success: boolean }, { success: boolean }>(`/documents/${id}`),
};

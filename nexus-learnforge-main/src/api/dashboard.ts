import { apiClient } from "./client";

export type Course = {
  id: string;
  name: string;
  code?: string;
  description?: string;
  subject_area?: string;
  academic_level?: string;
};

export const dashboard = {
  listCourses: () => apiClient.get<Course[], Course[]>("/courses"),
  createCourse: (p: Partial<Course>) => apiClient.post<Course, Course>("/courses", p),
};

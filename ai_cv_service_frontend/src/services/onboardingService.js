import api from "./api";

export const onboardingService = {
  // Templates
  listTemplates: async () => {
    const { data } = await api.get("/onboarding/templates");
    return data;
  },
  getTemplate: async (id) => {
    const { data } = await api.get(`/onboarding/templates/${id}`);
    return data;
  },
  createTemplate: async (payload) => {
    const { data } = await api.post("/onboarding/templates", payload);
    return data;
  },
  updateTemplate: async (id, payload) => {
    const { data } = await api.patch(`/onboarding/templates/${id}`, payload);
    return data;
  },
  deleteTemplate: async (id) => {
    const { data } = await api.delete(`/onboarding/templates/${id}`);
    return data;
  },

  // Assignments
  listAssignments: async (params = {}) => {
    const { data } = await api.get("/onboarding/assignments", { params });
    return data;
  },
  getAssignment: async (id) => {
    const { data } = await api.get(`/onboarding/assignments/${id}`);
    return data;
  },
  createAssignment: async (payload) => {
    const { data } = await api.post("/onboarding/assignments", payload);
    return data;
  },
  updateAssignment: async (id, payload) => {
    const { data } = await api.patch(`/onboarding/assignments/${id}`, payload);
    return data;
  },
  deleteAssignment: async (id) => {
    const { data } = await api.delete(`/onboarding/assignments/${id}`);
    return data;
  },
  toggleTask: async (assignmentId, taskId, payload = {}) => {
    const { data } = await api.post(
      `/onboarding/assignments/${assignmentId}/tasks/${taskId}/toggle`,
      payload,
    );
    return data;
  },
};

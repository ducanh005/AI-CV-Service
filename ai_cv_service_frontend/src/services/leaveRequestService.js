import api from "./api";

export const leaveRequestService = {
  list: async (params = {}) => {
    const { data } = await api.get("/leave-requests", { params });
    return data;
  },
  get: async (id) => {
    const { data } = await api.get(`/leave-requests/${id}`);
    return data;
  },
  create: async (payload) => {
    const { data } = await api.post("/leave-requests", payload);
    return data;
  },
  update: async (id, payload) => {
    const { data } = await api.patch(`/leave-requests/${id}`, payload);
    return data;
  },
  approve: async (id, payload) => {
    const { data } = await api.post(`/leave-requests/${id}/approve`, payload);
    return data;
  },
  delete: async (id) => {
    const { data } = await api.delete(`/leave-requests/${id}`);
    return data;
  },
};

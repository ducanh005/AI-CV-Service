import api from "./api";

export const attendanceService = {
  list: async (params = {}) => {
    const { data } = await api.get("/attendances", { params });
    return data;
  },
  get: async (id) => {
    const { data } = await api.get(`/attendances/${id}`);
    return data;
  },
  create: async (payload) => {
    const { data } = await api.post("/attendances", payload);
    return data;
  },
  update: async (id, payload) => {
    const { data } = await api.patch(`/attendances/${id}`, payload);
    return data;
  },
  delete: async (id) => {
    const { data } = await api.delete(`/attendances/${id}`);
    return data;
  },
};

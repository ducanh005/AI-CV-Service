import api from "./api";

export const jobService = {
    list: async (params) => {
        const { data } = await api.get("/jobs", { params });
        return data;
    },
    create: async (payload) => {
        const { data } = await api.post("/jobs", payload);
        return data;
    },
    update: async ({ id, payload }) => {
        const { data } = await api.patch(`/jobs/${id}`, payload);
        return data;
    },
    remove: async (id) => {
        const { data } = await api.delete(`/jobs/${id}`);
        return data;
    },
};

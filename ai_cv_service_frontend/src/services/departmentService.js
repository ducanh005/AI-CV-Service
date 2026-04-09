import api from "./api";

export const departmentService = {
    list: async () => {
        const { data } = await api.get("/departments");
        return data;
    },
    get: async (id) => {
        const { data } = await api.get(`/departments/${id}`);
        return data;
    },
    create: async (payload) => {
        const { data } = await api.post("/departments", payload);
        return data;
    },
    update: async (id, payload) => {
        const { data } = await api.patch(`/departments/${id}`, payload);
        return data;
    },
    delete: async (id) => {
        const { data } = await api.delete(`/departments/${id}`);
        return data;
    },
};

import api from "./api";

export const employeeService = {
    list: async (params = {}) => {
        const { data } = await api.get("/employees", { params });
        return data;
    },
    get: async (id) => {
        const { data } = await api.get(`/employees/${id}`);
        return data;
    },
    create: async (payload) => {
        const { data } = await api.post("/employees", payload);
        return data;
    },
    update: async (id, payload) => {
        const { data } = await api.patch(`/employees/${id}`, payload);
        return data;
    },
    delete: async (id) => {
        const { data } = await api.delete(`/employees/${id}`);
        return data;
    },
};

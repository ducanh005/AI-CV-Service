import api from "./api";

export const companyService = {
    get: async (companyId) => {
        const { data } = await api.get(`/companies/${companyId}`);
        return data;
    },
    create: async (payload) => {
        const { data } = await api.post("/companies", payload);
        return data;
    },
    update: async ({ companyId, payload }) => {
        const { data } = await api.patch(`/companies/${companyId}`, payload);
        return data;
    },
};

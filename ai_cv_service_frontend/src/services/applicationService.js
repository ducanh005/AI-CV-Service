import api from "./api";

export const applicationService = {
    apply: async (payload) => {
        const { data } = await api.post("/applications", payload);
        return data;
    },
    listByJob: async ({ jobId, page, pageSize }) => {
        const { data } = await api.get(`/applications/job/${jobId}`, {
            params: { page, page_size: pageSize },
        });
        return data;
    },
    listMine: async ({ page, pageSize }) => {
        const { data } = await api.get("/applications/me", {
            params: { page, page_size: pageSize },
        });
        return data;
    },
    review: async ({ applicationId, payload }) => {
        const { data } = await api.patch(
            `/applications/${applicationId}/review`,
            payload,
        );
        return data;
    },
    hrDashboard: async () => {
        const { data } = await api.get("/applications/hr-dashboard");
        return data;
    },
    createCandidate: async (payload) => {
        const { data } = await api.post("/users/candidates", payload);
        return data;
    },
};

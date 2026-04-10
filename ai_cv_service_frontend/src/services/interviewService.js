import api from "./api";

export const interviewService = {
    list: async () => {
    const { data } = await api.get("/interviews");
    return data;
  },

    create: async (payload) => {
        const { data } = await api.post("/interviews", payload);
        return data;
    },

    update: async ({ id, payload }) => {
    const { data } = await api.patch(`/interviews/${id}`, payload);
    return data;
    },

    remove: async (id) => {
    await api.delete(`/interviews/${id}`);
    return true;
    },

    sync: async (id) => {
        const { data } = await api.post(`/interviews/${id}/sync`);
        return data;
    },

    createCalendarTestEvent: async (candidateEmail) => {
        const { data } = await api.post(
            "/integrations/calendar/test-event",
            null,
            {
                params: { candidate_email: candidateEmail },
            },
        );
        return data;
    },
};

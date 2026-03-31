import api from "./api";

export const interviewService = {
    create: async (payload) => {
        const { data } = await api.post("/interviews", payload);
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

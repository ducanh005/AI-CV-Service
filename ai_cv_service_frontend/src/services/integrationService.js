import api from "./api";

export const integrationService = {
    sendTestEmail: async (toEmail) => {
        const { data } = await api.post(
            "/integrations/gmail/test-email",
            null,
            {
                params: { to_email: toEmail },
            },
        );
        return data;
    },
    sendGmailEmail: async (payload) => {
        const { data } = await api.post("/integrations/gmail/send", payload);
        return data;
    },
};

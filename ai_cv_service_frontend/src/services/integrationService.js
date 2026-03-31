import api from "./api";

export const integrationService = {
    linkedinOauthUrl: async () => {
        const { data } = await api.get("/integrations/linkedin/oauth-url");
        return data;
    },
    linkedinImport: async (code) => {
        const { data } = await api.get(
            "/integrations/linkedin/import-candidate",
            { params: { code } },
        );
        return data;
    },
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
};

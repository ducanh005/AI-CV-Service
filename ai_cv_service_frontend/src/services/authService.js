import api from "./api";

export const authService = {
    login: async (payload) => {
        const { data } = await api.post("/auth/login", payload);
        return data;
    },
    register: async (payload) => {
        const { data } = await api.post("/auth/register", payload);
        return data;
    },
    logout: async (token) => {
        const { data } = await api.post("/auth/logout", { token });
        return data;
    },
    refresh: async (refreshToken) => {
        const { data } = await api.post("/auth/refresh", {
            refresh_token: refreshToken,
        });
        return data;
    },
    me: async () => {
        const { data } = await api.get("/users/me");
        return data;
    },
    oauthAuthorize: async (provider, mode = "login", state = "") => {
        const params = {
            mode,
        };
        if (state) {
            params.state = state;
        }

        const { data } = await api.get(`/auth/oauth/${provider}/authorize`, { params });
        return data;
    },
    oauthExchangeToken: async (provider, code) => {
        const { data } = await api.post(`/auth/oauth/${provider}/token`, { code });
        return data;
    },
    oauthFetchProfile: async (provider, accessToken, idToken) => {
        const { data } = await api.get(`/auth/oauth/${provider}/profile`, {
            headers: {
                Authorization: `Bearer ${accessToken}`,
            },
            params: idToken ? { id_token: idToken } : undefined,
        });
        return data;
    },
    oauthRegister: async (provider, payload) => {
        const { data } = await api.post(`/auth/oauth/${provider}/register`, payload);
        return data;
    },
};

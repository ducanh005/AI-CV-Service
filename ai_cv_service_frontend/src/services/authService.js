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
};

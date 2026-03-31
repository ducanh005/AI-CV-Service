import { TOKEN_KEYS } from "./constants";

export const tokenStorage = {
    getAccessToken: () => localStorage.getItem(TOKEN_KEYS.access),
    getRefreshToken: () => localStorage.getItem(TOKEN_KEYS.refresh),
    getUser: () => {
        const raw = localStorage.getItem(TOKEN_KEYS.user);
        return raw ? JSON.parse(raw) : null;
    },
    setSession: ({ accessToken, refreshToken, user }) => {
        localStorage.setItem(TOKEN_KEYS.access, accessToken);
        localStorage.setItem(TOKEN_KEYS.refresh, refreshToken);
        localStorage.setItem(TOKEN_KEYS.user, JSON.stringify(user));
    },
    clearSession: () => {
        localStorage.removeItem(TOKEN_KEYS.access);
        localStorage.removeItem(TOKEN_KEYS.refresh);
        localStorage.removeItem(TOKEN_KEYS.user);
    },
};

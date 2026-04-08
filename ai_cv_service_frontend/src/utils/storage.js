import { TOKEN_KEYS } from "./constants";

const SESSION_KEY = "session";

export const tokenStorage = {
    getSession: () => {
        const raw = localStorage.getItem(SESSION_KEY);
        return raw ? JSON.parse(raw) : null;
    },
    getAccessToken: () => localStorage.getItem(TOKEN_KEYS.access),
    getRefreshToken: () => localStorage.getItem(TOKEN_KEYS.refresh),
    getUser: () => {
        const rawUser = localStorage.getItem(TOKEN_KEYS.user);
        if (rawUser) {
            return JSON.parse(rawUser);
        }
        const session = tokenStorage.getSession();
        return session?.user ?? null;
    },
    setSession: ({ accessToken, refreshToken, user }) => {
        const session = {
            accessToken,
            refreshToken,
            user,
        };
        localStorage.setItem(SESSION_KEY, JSON.stringify(session));
        localStorage.setItem(TOKEN_KEYS.access, accessToken);
        localStorage.setItem(TOKEN_KEYS.refresh, refreshToken);
        localStorage.setItem(TOKEN_KEYS.user, JSON.stringify(user));
    },
    clearSession: () => {
        localStorage.removeItem(SESSION_KEY);
        localStorage.removeItem(TOKEN_KEYS.access);
        localStorage.removeItem(TOKEN_KEYS.refresh);
        localStorage.removeItem(TOKEN_KEYS.user);
    },
};

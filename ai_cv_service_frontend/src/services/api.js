import axios from "axios";

import { tokenStorage } from "../utils/storage";

const api = axios.create({
    baseURL:
        import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
    timeout: 20000,
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach((promise) => {
        if (error) {
            promise.reject(error);
            return;
        }
        promise.resolve(token);
    });
    failedQueue = [];
};

api.interceptors.request.use((config) => {
    const accessToken = tokenStorage.getAccessToken();
    if (accessToken) {
        config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        const refreshToken = tokenStorage.getRefreshToken();

        if (
            error.response?.status !== 401 ||
            originalRequest?._retry ||
            !refreshToken
        ) {
            return Promise.reject(error);
        }

        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
            })
                .then((newToken) => {
                    originalRequest.headers.Authorization = `Bearer ${newToken}`;
                    return api(originalRequest);
                })
                .catch((queueError) => Promise.reject(queueError));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
            const response = await axios.post(
                `${import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1"}/auth/refresh`,
                { refresh_token: refreshToken },
            );
            const {
                access_token: accessToken,
                refresh_token: newRefreshToken,
            } = response.data;
            const user = tokenStorage.getUser();

            tokenStorage.setSession({
                accessToken,
                refreshToken: newRefreshToken,
                user,
            });

            processQueue(null, accessToken);
            originalRequest.headers.Authorization = `Bearer ${accessToken}`;
            return api(originalRequest);
        } catch (refreshError) {
            processQueue(refreshError, null);
            tokenStorage.clearSession();
            window.location.href = "/login";
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    },
);

export default api;

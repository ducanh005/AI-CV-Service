import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { authService } from "../services/authService";
import { useAuthStore } from "../store/authStore";
import { tokenStorage } from "../utils/storage";

export function useLogin() {
    const authStore = useAuthStore();
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: authService.login,
        onSuccess: async (tokens) => {
            tokenStorage.setSession({
                accessToken: tokens.access_token,
                refreshToken: tokens.refresh_token,
                user: authStore.user || { role: "user" },
            });
            const me = await authService.me();
            authStore.setSession({
                accessToken: tokens.access_token,
                refreshToken: tokens.refresh_token,
                user: me,
            });
            queryClient.invalidateQueries({ queryKey: ["me"] });
        },
    });
}

export function useRegister() {
    const authStore = useAuthStore();

    return useMutation({
        mutationFn: authService.register,
        onSuccess: async (tokens) => {
            tokenStorage.setSession({
                accessToken: tokens.access_token,
                refreshToken: tokens.refresh_token,
                user: authStore.user || { role: "user" },
            });
            const me = await authService.me();
            authStore.setSession({
                accessToken: tokens.access_token,
                refreshToken: tokens.refresh_token,
                user: me,
            });
        },
    });
}

export function useMe() {
    const authStore = useAuthStore();

    return useQuery({
        queryKey: ["me"],
        queryFn: authService.me,
        enabled: authStore.isAuthenticated,
    });
}

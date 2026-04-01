import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { userService } from "../services/userService";
import { useAuthStore } from "../store/authStore";
import { tokenStorage } from "../utils/storage";

function useSyncProfile() {
    const queryClient = useQueryClient();
    const { setSession } = useAuthStore();

    return (profile) => {
        queryClient.setQueryData(["me"], profile);

        const accessToken = tokenStorage.getAccessToken();
        const refreshToken = tokenStorage.getRefreshToken();
        if (accessToken && refreshToken) {
            setSession({
                accessToken,
                refreshToken,
                user: profile,
            });
        }
    };
}

export function useMyProfile() {
    const { isAuthenticated } = useAuthStore();

    return useQuery({
        queryKey: ["me"],
        queryFn: userService.me,
        enabled: isAuthenticated,
    });
}

export function useUpdateProfile() {
    const syncProfile = useSyncProfile();

    return useMutation({
        mutationFn: userService.updateProfile,
        onSuccess: syncProfile,
    });
}

export function useUploadAvatar() {
    const syncProfile = useSyncProfile();

    return useMutation({
        mutationFn: userService.uploadAvatar,
        onSuccess: syncProfile,
    });
}

export function useSearchCandidateByEmail() {
    return useMutation({
        mutationFn: userService.searchCandidateByEmail,
    });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { applicationService } from "../services/applicationService";

export function useApplyJob() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: applicationService.apply,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["jobs"] });
            queryClient.invalidateQueries({ queryKey: ["applications"] });
        },
    });
}

export function useApplicationsByJob(params, enabled = true, options = {}) {
    return useQuery({
        queryKey: ["applications", params],
        queryFn: () => applicationService.listByJob(params),
        enabled,
        ...options,
    });
}

export function useApplicationsByCompany(params, enabled = true, options = {}) {
    return useQuery({
        queryKey: ["applications", "company", params],
        queryFn: () => applicationService.listByCompany(params),
        enabled,
        ...options,
    });
}

export function useMyApplications(params, enabled = true) {
    return useQuery({
        queryKey: ["applications", "me", params],
        queryFn: () => applicationService.listMine(params),
        enabled,
    });
}

export function useReviewApplication() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: applicationService.review,
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["applications"] }),
    });
}

export function useDeleteApplication() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: applicationService.remove,
        onSuccess: () =>
            queryClient.invalidateQueries({ queryKey: ["applications"] }),
    });
}

export function useHRDashboard() {
    return useQuery({
        queryKey: ["applications", "hr-dashboard"],
        queryFn: applicationService.hrDashboard,
    });
}

export function useCreateCandidate() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: applicationService.createCandidate,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["applications"] });
        },
    });
}

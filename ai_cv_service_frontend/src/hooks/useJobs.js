import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { jobService } from "../services/jobService";

export function useJobs(params) {
    return useQuery({
        queryKey: ["jobs", params],
        queryFn: () => jobService.list(params),
    });
}

export function useCreateJob() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: jobService.create,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
    });
}

export function useUpdateJob() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: jobService.update,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
    });
}

export function useDeleteJob() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: jobService.remove,
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
    });
}

import { useMutation, useQuery } from "@tanstack/react-query";

import { cvService } from "../services/cvService";

export function useUploadCV() {
    return useMutation({ mutationFn: cvService.upload });
}

export function useLatestMyCV() {
    return useQuery({
        queryKey: ["my-latest-cv"],
        queryFn: cvService.getLatestMine,
    });
}

export function useScoreCV() {
    return useMutation({ mutationFn: cvService.score });
}

export function useRankCandidates() {
    return useMutation({ mutationFn: cvService.rankCandidates });
}

export function useRankCandidatesAsyncSubmit() {
    return useMutation({ mutationFn: cvService.rankCandidatesAsyncSubmit });
}

export function useRankCandidatesAsyncStatus(scoringJobId, enabled = true) {
    return useQuery({
        queryKey: ["ai-rank-async-status", scoringJobId],
        queryFn: () => cvService.rankCandidatesAsyncStatus(scoringJobId),
        enabled: enabled && Boolean(scoringJobId),
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            if (status === "completed" || status === "partial_failed" || status === "failed") {
                return false;
            }
            return 2000;
        },
    });
}

export function useNotifyScreeningResult() {
    return useMutation({ mutationFn: cvService.notifyScreeningResult });
}

export function useScoreUploadedCV() {
    return useMutation({ mutationFn: cvService.scoreUploadedCV });
}

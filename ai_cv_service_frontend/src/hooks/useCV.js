import { useMutation } from "@tanstack/react-query";

import { cvService } from "../services/cvService";

export function useUploadCV() {
    return useMutation({ mutationFn: cvService.upload });
}

export function useScoreCV() {
    return useMutation({ mutationFn: cvService.score });
}

export function useRankCandidates() {
    return useMutation({ mutationFn: cvService.rankCandidates });
}

export function useScoreUploadedCV() {
    return useMutation({ mutationFn: cvService.scoreUploadedCV });
}

import { useMutation } from "@tanstack/react-query";

import { integrationService } from "../services/integrationService";
import { interviewService } from "../services/interviewService";

export function useLinkedinOauthUrl() {
    return useMutation({ mutationFn: integrationService.linkedinOauthUrl });
}

export function useLinkedinImport() {
    return useMutation({ mutationFn: integrationService.linkedinImport });
}

export function useSendTestEmail() {
    return useMutation({ mutationFn: integrationService.sendTestEmail });
}

export function useSendGmailEmail() {
    return useMutation({ mutationFn: integrationService.sendGmailEmail });
}

export function useCreateInterview() {
    return useMutation({ mutationFn: interviewService.create });
}

export function useCreateCalendarTestEvent() {
    return useMutation({
        mutationFn: interviewService.createCalendarTestEvent,
    });
}

import api from "./api";

export const cvService = {
    getLatestMine: async () => {
        const { data } = await api.get("/cvs/me/latest");
        return data;
    },
    upload: async (file) => {
        const formData = new FormData();
        formData.append("file", file);
        const { data } = await api.post("/cvs/upload", formData, {
            headers: { "Content-Type": "multipart/form-data" },
        });
        return data;
    },
    score: async (payload) => {
        const { data } = await api.post("/ai/score-cv", payload);
        return data;
    },
    rankCandidates: async ({ jobId, minScore, notifyCandidates, criteria }) => {
        const { data } = await api.post("/ai/rank-candidates", {
            job_id: jobId,
            min_score: minScore,
            notify_candidates: Boolean(notifyCandidates),
            criteria,
        });
        return data;
    },
    notifyScreeningResult: async ({ applicationId, minScore }) => {
        const { data } = await api.post("/ai/notify-screening-result", {
            application_id: applicationId,
            min_score: minScore,
        });
        return data;
    },
    scoreUploadedCV: async ({
        jobId,
        minScore,
        file,
        notifyCandidates,
        candidateEmail,
    }) => {
        const formData = new FormData();
        formData.append("job_id", String(jobId));
        formData.append("min_score", String(minScore));
        formData.append("notify_candidates", String(Boolean(notifyCandidates)));
        if (candidateEmail) {
            formData.append("candidate_email", candidateEmail);
        }
        formData.append("file", file);

        const { data } = await api.post("/ai/score-upload", formData, {
            headers: { "Content-Type": "multipart/form-data" },
        });
        return data;
    },
};

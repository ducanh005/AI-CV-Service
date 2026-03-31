import api from "./api";

export const cvService = {
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
    rankCandidates: async (payload) => {
        const { data } = await api.post("/ai/rank-candidates", payload);
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

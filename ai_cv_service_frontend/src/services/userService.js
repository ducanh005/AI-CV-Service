import api from "./api";

export const userService = {
    me: async () => {
        const { data } = await api.get("/users/me");
        return data;
    },
    updateProfile: async (payload) => {
        const { data } = await api.patch("/users/me", payload);
        return data;
    },
    uploadAvatar: async (file) => {
        const formData = new FormData();
        formData.append("file", file);
        const { data } = await api.post("/users/me/avatar", formData, {
            headers: { "Content-Type": "multipart/form-data" },
        });
        return data;
    },
    searchCandidateByEmail: async (email) => {
        const { data } = await api.get("/users/candidates/search", {
            params: { email },
        });
        return data;
    },
};

export function resolveAvatarUrl(path) {
    if (!path) {
        return "";
    }

    if (path.startsWith("http://") || path.startsWith("https://")) {
        return path;
    }

    const apiBase =
        import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
    const hostBase = apiBase.replace(/\/api\/v1\/?$/, "");
    return `${hostBase}/${String(path).replace(/^\/+/, "")}`;
}

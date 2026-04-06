const SOCIAL_PROVIDERS = new Set(["google", "linkedin"]);

const ROLE_PRIORITY = ["user", "hr", "admin"];

export function getSocialProviderLabel(provider) {
    return provider === "linkedin" ? "LinkedIn" : "Google";
}

export function isSupportedSocialProvider(provider) {
    return SOCIAL_PROVIDERS.has((provider || "").toLowerCase());
}

export function buildSocialState(mode) {
    const safeMode = mode === "register" ? "register" : "login";
    return `${safeMode}:${Date.now()}`;
}

export function normalizeOAuthProfile(provider, profile) {
    const safeProvider = (provider || "").toLowerCase();

    if (safeProvider === "linkedin") {
        const linkedinId = profile?.sub || profile?.id || profile?.user_id || `li-${Date.now()}`;
        const fullName =
            profile?.name ||
            `${profile?.given_name || ""} ${profile?.family_name || ""}`.trim() ||
            "LinkedIn User";
        const email =
            profile?.email ||
            profile?.email_address ||
            profile?.preferred_username ||
            `${linkedinId}@linkedin.local`;

        return {
            email,
            full_name: fullName,
            linkedin_id: linkedinId,
            linkedin_profile: {
                ...profile,
                full_name: fullName,
            },
        };
    }

    const googleId = profile?.sub || profile?.id || profile?.user_id || `gg-${Date.now()}`;
    const fullName =
        profile?.name ||
        `${profile?.given_name || ""} ${profile?.family_name || ""}`.trim() ||
        "Google User";
    const email = profile?.email || profile?.email_address || `${googleId}@google.local`;

    return {
        email,
        full_name: fullName,
        google_id: googleId,
        google_profile: {
            ...profile,
            full_name: fullName,
        },
    };
}

export function isRoleRequiredError(error) {
    const data = error?.response?.data;
    return data?.error_code === "role_required" || data?.detail?.error_code === "role_required";
}

export function extractAllowedRoles(error) {
    const data = error?.response?.data;
    const rawRoles = data?.allowed_roles || data?.detail?.allowed_roles || ROLE_PRIORITY;

    if (!Array.isArray(rawRoles) || !rawRoles.length) {
        return ROLE_PRIORITY;
    }

    const uniqueRoles = Array.from(
        new Set(rawRoles.map((role) => String(role || "").toLowerCase()).filter(Boolean)),
    );

    const sorted = ROLE_PRIORITY.filter((role) => uniqueRoles.includes(role));
    return sorted.length ? sorted : ROLE_PRIORITY;
}

export function roleLabel(role) {
    if (role === "hr") {
        return "HR";
    }
    if (role === "admin") {
        return "Admin";
    }
    return "Ứng viên";
}

export function getOAuthGuardSet() {
    if (typeof window === "undefined") {
        return null;
    }

    if (!window.__smarthireOAuthGuard) {
        window.__smarthireOAuthGuard = new Set();
    }

    return window.__smarthireOAuthGuard;
}

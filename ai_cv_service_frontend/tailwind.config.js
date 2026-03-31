/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{js,jsx}"],
    theme: {
        extend: {
            colors: {
                navy: "#00011f",
                slateText: "#6b7289",
                panelBorder: "#d9d9df",
                appBg: "#f4f5f8",
            },
            fontFamily: {
                sans: ["Segoe UI", "system-ui", "sans-serif"],
            },
            boxShadow: {
                card: "0 6px 18px rgba(15, 23, 42, 0.06)",
            },
        },
    },
    plugins: [],
};

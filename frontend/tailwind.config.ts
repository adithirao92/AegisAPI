import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0a0d12",
        surface: "#111720",
        panel: "#151c26",
        line: "#263142",
        muted: "#8793a6",
        accent: "#56d5a1"
      },
      boxShadow: {
        panel: "0 12px 32px rgba(0, 0, 0, 0.2)"
      }
    }
  },
  plugins: []
} satisfies Config;

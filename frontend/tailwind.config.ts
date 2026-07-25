import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        orbit: {
          black: "#05060a",
          surface: "#0d0f1a",
          panel: "#131629",
          blue: "#3b82f6",
          bluedeep: "#1d4ed8",
          purple: "#8b5cf6",
          purpledeep: "#6d28d9",
          border: "#232744",
        },
      },
      backgroundImage: {
        "orbit-gradient": "linear-gradient(135deg, #05060a 0%, #131629 45%, #1d1440 100%)",
        "orbit-accent": "linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%)",
      },
      boxShadow: {
        glow: "0 0 40px rgba(139, 92, 246, 0.25)",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: "0.3" },
          "50%": { opacity: "1" },
        },
        fadeUp: {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        pulseDot: "pulseDot 1.4s ease-in-out infinite",
        fadeUp: "fadeUp 0.25s ease-out",
      },
    },
  },
  plugins: [],
};

export default config;

import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#FFF7EA",
        surface: "#FAF2E4",
        sand: "#E6D9C7",
        "sand-border": "#D6C7B2",
        mint: "#C9D8C4",
        sage: "#8FB08A",
        forest: "#556B5A",
        ink: "#1C2820",
        muted: "#435448",
        ochre: "#B87D3B",
        terracotta: "#A84232",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "sans-serif"],
        display: ["var(--font-display)", "Georgia", "serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;

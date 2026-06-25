import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand accent reused across buttons, links and active states.
        brand: {
          DEFAULT: "#2563eb",
          hover: "#1d4ed8",
        },
      },
    },
  },
  plugins: [],
};

export default config;

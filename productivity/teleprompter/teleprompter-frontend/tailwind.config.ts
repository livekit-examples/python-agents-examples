import type { Config } from "tailwindcss";
import colors from "tailwindcss/colors";

const custom = {
  "accent-bg": "#111111",
};

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: ["class"],
  theme: {
    colors: {
      ...colors,
      ...custom,
    },
  },
  plugins: [],
} satisfies Config;

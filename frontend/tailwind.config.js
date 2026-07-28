/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef6ff",
          100: "#d9eaff",
          200: "#bcd9ff",
          300: "#8ec1ff",
          400: "#599dff",
          500: "#3477f6",
          600: "#1f57e0",
          700: "#1a45b4",
          800: "#1b3c8f",
          900: "#1c3672",
          950: "#122248",
        },
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      boxShadow: {
        "center": "0px 0px 5px 0px rgba(0,0,0,0.3)",
        "center-wide": "0px 0px 8px 0px rgba(0,0,0,0.4)",
      }
    },
  },
  plugins: [],
}


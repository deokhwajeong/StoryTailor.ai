module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        pastelPink: '#FFD1DC',
        pastelBlue: '#B5E3FF',
        pastelGreen: '#C8F7C5',
        pastelYellow: '#FFF9C4',
        pastelPurple: '#E1D5FF',
      },
      fontFamily: {
        sans: ["Atkinson Hyperlegible", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

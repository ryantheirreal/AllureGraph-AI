/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        allure: {
          purple: '#8b5cf6',
          blue: '#3b82f6',
          pink: '#ec4899',
        },
      },
    },
  },
  plugins: [],
}

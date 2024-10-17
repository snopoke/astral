/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./astral/**/*.{html,js}", "./example-project/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
  ],
}

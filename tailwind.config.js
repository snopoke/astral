/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./cotton_daisyui/**/*.{html,js}", "./example-project/**/*.{html,js}"],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
  ],
}

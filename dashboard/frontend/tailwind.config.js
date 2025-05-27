// tailwind.config.js
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        primary: "#0071E3",       // botão principal, destaque
        secondary: "#E3F2FF",     // plano de fundo leve
        background: "#FAFAFA",    // fundo geral
        text: "#2E2E2E",          // texto principal
        muted: "#888888",         // texto secundário
        card: "#FFFFFF",          // fundo dos cards
        danger: "#FF6F61",        // sair ou erros
      },
    },
  },
  plugins: [],
};

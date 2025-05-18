// src/components/Header.jsx
export default function Header() {
  const nome = localStorage.getItem("nome") || "Técnico";

  return (
    <header className="bg-white shadow px-6 py-4 flex justify-between items-center">
      <h1 className="text-lg font-semibold text-gray-800">Bem-vindo, {nome}</h1>
    </header>
  );
}

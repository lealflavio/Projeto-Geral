import React from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";

const getPageTitle = (pathname) => {
  switch (pathname) {
    case "/dashboard":
      return "Início";
    case "/creditos":
      return "Créditos";
    case "/simulador":
      return "Simulador";
    case "/wos":
      return "Minhas WOs";
    case "/perfil":
      return "Perfil";
    case "/alocar-wo":
      return "Alocar WO";
    case "/mapa-kms":
      return "Mapa de KMs";
    default:
      return "";
  }
};

const Layout = () => {
  const location = useLocation();
  const pageTitle = getPageTitle(location.pathname);

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-y-auto">
        {/* Topbar Mobile - Corrigido para não rolar com a página */}
        <div className="md:hidden flex items-center px-4 py-4 bg-background shadow-md fixed top-0 left-0 right-0 z-10">
          <h1 className="text-xl font-semibold text-text-dark ml-12">{pageTitle}</h1>
        </div>

        {/* Conteúdo da página - Ajustado para compensar o header fixo no mobile */}
        <main className="flex-1 px-4 py-4 md:py-6 mt-[60px] md:mt-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;

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
        {/* Topbar Mobile */}
        <div className="md:hidden flex items-center px-4 py-4 bg-background shadow-sm">
          <h1 className="text-xl font-semibold text-text ml-12">{pageTitle}</h1>
        </div>

        {/* Conteúdo da página */}
        <main className="flex-1 px-4 py-4 md:py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;

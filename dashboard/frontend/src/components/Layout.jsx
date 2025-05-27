import React, { useState, useEffect } from "react";
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
  const [showTopbar, setShowTopbar] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  // Controle de scroll para esconder/mostrar a topbar
  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > lastScrollY && currentScrollY > 20) {
        // Rolando para baixo - esconde a topbar
        setShowTopbar(false);
      } else {
        // Rolando para cima ou no topo - mostra a topbar
        setShowTopbar(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [lastScrollY]);

  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-y-auto">
        {/* Topbar Mobile - Agora desaparece ao rolar */}
        <div 
          className={`md:hidden flex items-center px-4 py-3 bg-card shadow-sm z-10 transition-transform duration-300 ${
            showTopbar ? 'transform-none' : '-translate-y-full'
          }`}
          style={{ position: 'sticky', top: 0 }}
        >
          <div className="flex items-center justify-center w-full">
            <h1 className="text-xl font-semibold text-text mx-auto">{pageTitle}</h1>
          </div>
        </div>

        {/* Conteúdo da página - Sem margem adicional pois a topbar não é mais fixa */}
        <main className="flex-1 px-4 py-4 md:py-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;

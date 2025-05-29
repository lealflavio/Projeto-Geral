import React, { useState, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "./Sidebar";
import { Menu } from "lucide-react";

const getPageTitle = (pathname) => {
  switch (pathname) {
    case "/dashboard":
      return "Dashboard";
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
    case "/estimativa-ganhos":
      return "Estimativa de Ganhos";
    default:
      return "";
  }
};

const Layout = () => {
  const location = useLocation();
  const pageTitle = getPageTitle(location.pathname);
  const [showTopbar, setShowTopbar] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

  // Função para alternar o estado da sidebar
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="flex h-screen bg-background">
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />
      <div className="flex-1 flex flex-col overflow-y-auto">
        {/* Topbar Mobile - Agora com o botão de menu integrado */}
        <div 
          className={`flex items-center px-4 py-3 bg-card shadow-sm z-10 transition-transform duration-300 ${
            showTopbar ? 'transform-none' : '-translate-y-full'
          }`}
          style={{ position: 'sticky', top: 0 }}
        >
          <div className="flex items-center w-full gap-4">
            {/* Botão de menu agora está aqui na topbar */}
            <button 
              onClick={toggleSidebar}
              className="text-text md:hidden"
            >
              <Menu size={28} />
            </button>
            <h1 className="text-xl font-semibold text-text">{pageTitle}</h1>
          </div>
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

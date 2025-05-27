import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  LogOut,
  Home,
  DollarSign,
  BarChart,
  List,
  User,
  Menu,
  X,
  Navigation,
} from "lucide-react";

const Sidebar = () => {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  
  const links = [
    { name: "Início", icon: <Home size={20} />, path: "/dashboard" },
    { name: "Créditos", icon: <DollarSign size={20} />, path: "/creditos" },
    { name: "Alocar WO", icon: <List size={20} />, path: "/alocar-wo" },
    { name: "Simulador", icon: <BarChart size={20} />, path: "/simulador" },    
    { name: "Minhas WOs", icon: <List size={20} />, path: "/wos" },
    { name: "Mapa de KMs", icon: <Navigation size={20} />, path: "/mapa-kms" },
    { name: "Perfil", icon: <User size={20} />, path: "/perfil" },
  ];
  
  const logout = () => {
    localStorage.removeItem("authToken");
    navigate("/");
  };
  
  return (
    <>
      {/* Botão mobile de abrir menu */}
      <div className="md:hidden fixed top-4 left-4 z-50">
        <button 
          onClick={() => setOpen(true)}
          className="bg-primary-500 text-white p-sm rounded-md shadow-md"
        >
          <Menu size={28} />
        </button>
      </div>
      
      {/* Overlay ao abrir menu mobile */}
      {open && (
        <div
          className="fixed inset-0 bg-black bg-opacity-30 z-40"
          onClick={() => setOpen(false)}
        />
      )}
      
      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-card shadow-lg transform transition-all duration-normal ease-in-out ${
          open ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 md:static md:shadow-md`}
      >
        {/* Header mobile */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-card-border md:hidden">
          <h2 className="text-lg font-semibold text-text">Menu</h2>
          <button 
            onClick={() => setOpen(false)}
            className="text-muted hover:text-text transition-colors duration-fast"
          >
            <X size={24} />
          </button>
        </div>
        
        {/* Conteúdo do menu */}
        <div className="flex flex-col h-full">
          <nav className="flex-1 px-4 pt-6 space-y-2 overflow-y-auto">
            {links.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-fast ${
                  location.pathname === link.path
                    ? "bg-primary-500 text-white"
                    : "text-text hover:bg-secondary"
                }`}
                onClick={() => setOpen(false)}
              >
                {link.icon}
                <span>{link.name}</span>
              </Link>
            ))}
          </nav>
          
          {/* Botão de sair - Corrigido para ser visível em mobile */}
          <div className="px-4 py-4 shrink-0 sticky bottom-0 bg-card border-t border-card-border">
            <button
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 bg-danger text-white py-2 px-4 rounded-lg font-semibold shadow hover:bg-danger-dark transition-colors duration-fast"
            >
              <LogOut size={18} />
              <span>Sair</span>
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;

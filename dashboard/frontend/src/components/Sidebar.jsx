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
    { name: "Estimativa de Ganhos", icon: <BarChart size={20} />, path: "/estimativa-ganhos" },    
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
      {/* Botão mobile de abrir menu - Agora apenas com ícone hambúrguer tradicional */}
      <div className="md:hidden fixed top-4 left-4 z-50">
        <button 
          onClick={() => setOpen(true)}
          className="text-text"
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
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-card shadow-lg transform transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 md:static md:shadow-none`}
      >
        {/* Header mobile */}
        <div className="flex items-center justify-between px-6 py-4 border-b md:hidden">
          <h2 className="text-lg font-semibold text-text">Menu</h2>
          <button 
            onClick={() => setOpen(false)}
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
                className={`flex items-center gap-3 px-4 py-2 rounded-lg transition ${
                  location.pathname === link.path
                    ? "bg-secondary text-primary"
                    : "text-text hover:bg-secondary"
                }`}
                onClick={() => setOpen(false)}
              >
                {link.icon}
                <span>{link.name}</span>
              </Link>
            ))}
          </nav>
          
          {/* Botão de sair - Agora com a cor primária */}
          <div className="px-4 py-4 shrink-0 sticky bottom-0 bg-card border-t">
            <button
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 bg-primary text-card py-2 px-4 rounded-xl font-semibold shadow hover:bg-opacity-90 transition"
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

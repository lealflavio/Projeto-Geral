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
        <button onClick={() => setOpen(true)}>
          <Menu size={28} className="text-[#333]" />
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
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out ${
          open ? "translate-x-0" : "-translate-x-full"
        } md:translate-x-0 md:static md:shadow-none`}
      >
        {/* Header mobile */}
        <div className="flex items-center justify-between px-6 py-4 border-b md:hidden">
          <h2 className="text-lg font-semibold text-[#333]">Menu</h2>
          <button onClick={() => setOpen(false)}>
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
                    ? "bg-[#7C3AED] text-white"
                    : "text-[#333] hover:bg-[#EDE9FE]"
                }`}
                onClick={() => setOpen(false)}
              >
                {link.icon}
                <span>{link.name}</span>
              </Link>
            ))}
          </nav>

          {/* Botão de sair */}
          <div className="px-4 py-4 shrink-0">
            <button
              onClick={logout}
              className="w-full bg-[#7C3AED] text-white py-2 rounded-xl font-semibold shadow hover:bg-[#6B21A8] transition"
            >
              Sair
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;

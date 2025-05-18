import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Home, CreditCard, BarChart2, ClipboardList } from 'lucide-react';

const menuItems = [
  { to: '/dashboard', label: 'Início', icon: <Home size={18} /> },
  { to: '/dashboard/creditos', label: 'Créditos', icon: <CreditCard size={18} /> },
  { to: '/dashboard/simulador', label: 'Simulador', icon: <BarChart2 size={18} /> },
  { to: '/dashboard/wos', label: 'Minhas WOs', icon: <ClipboardList size={18} /> },
];

function DashboardLayout() {
  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-lg hidden md:block">
        <div className="p-6 border-b">
          <h2 className="text-xl font-bold text-gray-800">Dashboard</h2>
        </div>
        <nav className="p-4 space-y-2">
          {menuItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center px-4 py-2 rounded hover:bg-blue-100 transition ${
                  isActive ? 'bg-blue-500 text-white' : 'text-gray-700'
                }`
              }
            >
              <span className="mr-2">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-4">
        <Outlet />
      </main>
    </div>
  );
}

export default DashboardLayout;

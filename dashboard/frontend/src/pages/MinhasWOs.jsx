import React from "react";

const wos = [
  { id: 1, tipo: "Instalação Fibra", status: "Concluída" },
  { id: 2, tipo: "Manutenção", status: "Pendente" },
];

const MinhasWOs = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#333]">Minhas WOs</h1>
      <div className="space-y-4">
        {wos.map((wo) => (
          <div
            key={wo.id}
            className="bg-white p-4 rounded-xl shadow flex justify-between items-center"
          >
            <div>
              <p className="font-semibold text-[#333]">{wo.tipo}</p>
              <p className="text-sm text-[#777]">WO #{wo.id}</p>
            </div>
            <span
              className={`px-3 py-1 text-xs rounded-full font-medium ${
                wo.status === "Concluída"
                  ? "bg-green-100 text-green-700"
                  : "bg-yellow-100 text-yellow-700"
              }`}
            >
              {wo.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MinhasWOs;

import React from "react";

const Dashboard = () => {
  const cards = [
    { label: "WOs Finalizadas", value: 18 },
    { label: "Créditos Atuais", value: 4 },
    { label: "Ganhos Estimados", value: "€240" },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold text-[#333]">Início</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {cards.map((card, index) => (
          <div
            key={index}
            className="bg-white p-6 rounded-2xl shadow transition-all"
          >
            <p className="text-sm text-[#777]">{card.label}</p>
            <p className="text-2xl font-bold text-[#7C3AED] mt-1">{card.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;

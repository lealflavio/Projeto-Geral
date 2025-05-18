import { ClipboardList, CheckCircle, Clock } from "lucide-react";

const cards = [
  {
    title: "WO Abertas",
    value: 4,
    icon: ClipboardList,
    color: "#FF6F61",
  },
  {
    title: "WO Concluídas",
    value: 12,
    icon: CheckCircle,
    color: "#4CAF50",
  },
  {
    title: "WO Pendentes",
    value: 2,
    icon: Clock,
    color: "#FFA726",
  },
];

const DashboardCards = () => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-white p-4 rounded-2xl shadow-md flex items-center gap-4"
        >
          <div
            className="p-3 rounded-xl"
            style={{ backgroundColor: `${card.color}22` }}
          >
            <card.icon color={card.color} size={28} />
          </div>
          <div className="flex flex-col">
            <span className="text-sm text-[#777]">{card.title}</span>
            <span className="text-2xl font-bold text-[#333]">{card.value}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DashboardCards;

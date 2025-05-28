import { ClipboardList, CheckCircle, Clock } from "lucide-react";
import '../styles/variables.css';

// Definindo cores como variáveis para facilitar manutenção
const cards = [
  {
    title: "WO Abertas",
    value: 4,
    icon: ClipboardList,
    colorClass: "text-red-500",
    bgClass: "bg-red-50",
  },
  {
    title: "WO Concluídas",
    value: 12,
    icon: CheckCircle,
    colorClass: "text-emerald-500",
    bgClass: "bg-emerald-50",
  },
  {
    title: "WO Pendentes",
    value: 2,
    icon: Clock,
    colorClass: "text-amber-500",
    bgClass: "bg-amber-50",
  },
];

const DashboardCards = () => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-card p-4 rounded-2xl shadow-md flex items-center gap-4"
        >
          <div
            className={`p-3 rounded-xl ${card.bgClass}`}
          >
            <card.icon className={card.colorClass} size={28} />
          </div>
          <div className="flex flex-col">
            <span className="text-sm text-muted">{card.title}</span>
            <span className="text-2xl font-bold text-text">{card.value}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default DashboardCards;

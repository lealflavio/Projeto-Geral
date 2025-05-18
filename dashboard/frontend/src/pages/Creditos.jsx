import { Coins } from "lucide-react";

const Creditos = () => {
  const creditos = 5;

  return (
    <div className="p-4 md:p-6">
      <h1 className="text-xl font-semibold text-[#333] mb-4">Meus Créditos</h1>

      <div className="bg-white rounded-xl shadow p-6 flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="bg-[#EDE9FE] p-3 rounded-full">
            <Coins size={28} className="text-[#7C3AED]" />
          </div>
          <div>
            <p className="text-sm text-[#777]">Créditos disponíveis</p>
            <p className="text-2xl font-bold text-[#333]">{creditos}</p>
          </div>
        </div>
      </div>

      <button className="w-full bg-[#7C3AED] text-white py-3 rounded-xl font-semibold shadow hover:bg-[#6B21A8] transition">
        Adicionar Créditos
      </button>
    </div>
  );
};

export default Creditos;

import { BarChart2 } from "lucide-react";

const Simulador = () => {
  return (
    <div className="p-4 md:p-6">
      <h1 className="text-xl font-semibold text-[#333] mb-4">Simulador de Ganhos</h1>

      <div className="bg-white rounded-xl shadow p-6 space-y-4">
        <div>
          <label className="block text-sm text-[#555] mb-1">Tipo de Serviço</label>
          <select className="w-full p-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]">
            <option>Instalação TV</option>
            <option>Reparação de Internet</option>
            <option>Troca de Equipamento</option>
          </select>
        </div>

        <div>
          <label className="block text-sm text-[#555] mb-1">Quantidade</label>
          <input
            type="number"
            className="w-full p-3 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#7C3AED]"
            placeholder="Ex: 3"
          />
        </div>

        <button className="w-full bg-[#7C3AED] text-white py-3 rounded-xl font-semibold hover:bg-[#6B21A8] transition">
          Simular
        </button>
      </div>
    </div>
  );
};

export default Simulador;

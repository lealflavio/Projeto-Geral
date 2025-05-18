import React, { useState } from 'react';

function Simulador() {
  const [tipo, setTipo] = useState('instalacao');
  const [resultado, setResultado] = useState(null);

  const valores = {
    instalacao: 20,
    reparo: 15,
    ativacao: 10,
  };

  const simular = () => {
    setResultado(valores[tipo] || 0);
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Simulador de Ganhos</h1>
      <div className="mb-4">
        <label className="block text-sm text-gray-600 mb-1">Tipo de Serviço</label>
        <select
          value={tipo}
          onChange={(e) => setTipo(e.target.value)}
          className="border border-gray-300 p-2 rounded w-full"
        >
          <option value="instalacao">Instalação</option>
          <option value="reparo">Reparo</option>
          <option value="ativacao">Ativação</option>
        </select>
      </div>
      <button onClick={simular} className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
        Simular
      </button>

      {resultado !== null && (
        <div className="mt-4 bg-white shadow p-4 rounded">
          <p className="text-gray-700">
            Ganho estimado: <strong>€ {resultado.toFixed(2)}</strong>
          </p>
        </div>
      )}
    </div>
  );
}

export default Simulador;

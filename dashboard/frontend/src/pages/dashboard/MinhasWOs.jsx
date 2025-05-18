import React from 'react';

const wosExemplo = [
  { id: 1, numero: 'WO123', status: 'concluída', tipo: 'instalacao' },
  { id: 2, numero: 'WO456', status: 'erro', tipo: 'reparo' },
];

function MinhasWOs() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Minhas WOs</h1>
      <div className="space-y-4">
        {wosExemplo.map((wo) => (
          <div key={wo.id} className="p-4 border rounded shadow-sm bg-white">
            <p><strong>Número:</strong> {wo.numero}</p>
            <p><strong>Tipo:</strong> {wo.tipo}</p>
            <p><strong>Status:</strong> {wo.status}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default MinhasWOs;

import React from 'react';

function Creditos() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Seus Créditos</h1>
      <div className="bg-white shadow rounded-lg p-4 mb-4">
        <p className="text-gray-700">Você possui <strong>5 créditos</strong> disponíveis.</p>
      </div>
      <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
        Adicionar Créditos
      </button>
    </div>
  );
}

export default Creditos;

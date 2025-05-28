import React, { useState } from "react";
import '../styles/variables.css';

function Creditos() {
  const [creditos, setCreditos] = useState(120);
  const [comprar, setComprar] = useState(0);

  const handleCompra = () => {
    if (comprar > 0) {
      setCreditos(creditos + comprar);
      setComprar(0);
      alert("Créditos adicionados com sucesso!");
    }
  };

  return (
    <div className="max-w-md mx-auto">
      <h2 className="text-xl font-semibold mb-6 text-text">Saldo de Créditos</h2>

      <div className="bg-card rounded-2xl shadow-md p-6 text-center mb-6">
        <p className="text-sm text-muted mb-1">Seus créditos disponíveis:</p>
        <p className="text-3xl font-bold text-primary">{creditos}</p>
      </div>

      <div className="bg-card rounded-2xl shadow-md p-6 mb-6">
        <h3 className="text-md font-semibold mb-2 text-text">Comprar créditos</h3>
        <div className="flex items-center space-x-2">
          <input
            type="number"
            value={comprar}
            onChange={(e) => setComprar(parseInt(e.target.value))}
            placeholder="Qtd"
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
          />
          <button
            onClick={handleCompra}
            className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primary-dark transition"
          >
            Comprar
          </button>
        </div>
      </div>

      <div className="bg-card rounded-2xl shadow-md p-6">
        <h3 className="text-md font-semibold mb-2 text-text">Histórico (simulado)</h3>
        <ul className="text-sm text-muted space-y-2">
          <li>+30 créditos - Compra via sistema</li>
          <li>-1 crédito - Processamento WO #9234</li>
          <li>-1 crédito - Processamento WO #9233</li>
          <li>+50 créditos - Compra via sistema</li>
        </ul>
      </div>
    </div>
  );
}

export default Creditos;

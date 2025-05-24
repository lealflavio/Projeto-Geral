import React, { useState } from 'react';
import { Coins, AlertTriangle, CreditCard, Wallet } from 'lucide-react';
import CreditHistory from '../components/CreditHistory';

const Creditos = () => {
  const [creditos, setCreditos] = useState(5);
  const [showRechargeModal, setShowRechargeModal] = useState(false);
  const [rechargeAmount, setRechargeAmount] = useState(10);
  
  const handleRecharge = () => {
    setCreditos(creditos + rechargeAmount);
    setShowRechargeModal(false);
  };
  
  return (
    <div className="p-4 md:p-6">
      <h1 className="text-xl font-semibold text-[#333] mb-4">Meus Créditos</h1>
      
      {/* Card de créditos */}
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
        
        {/* Alerta de créditos baixos */}
        {creditos < 3 && (
          <div className="flex items-center gap-2 bg-amber-50 text-amber-600 px-3 py-2 rounded-lg text-sm">
            <AlertTriangle size={16} />
            <span>Créditos baixos</span>
          </div>
        )}
      </div>
      
      {/* Botão de adicionar créditos */}
      <button 
        className="w-full bg-[#7C3AED] text-white py-3 rounded-xl font-semibold shadow hover:bg-[#6B21A8] transition flex items-center justify-center gap-2"
        onClick={() => setShowRechargeModal(true)}
      >
        <Wallet size={20} />
        <span>Adicionar Créditos</span>
      </button>
      
      {/* Componente de histórico de créditos */}
      <CreditHistory />
      
      {/* Modal de recarga de créditos */}
      {showRechargeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold text-[#333] mb-4">Recarregar Créditos</h2>
            
            <div className="mb-6">
              <label className="block text-sm text-[#555] mb-2">Quantidade de créditos</label>
              <div className="flex items-center">
                <button 
                  className="bg-gray-100 px-3 py-2 rounded-l-lg text-[#333]"
                  onClick={() => setRechargeAmount(Math.max(5, rechargeAmount - 5))}
                >
                  -
                </button>
                <input 
                  type="number" 
                  className="w-full border-y border-gray-200 py-2 px-3 text-center"
                  value={rechargeAmount}
                  onChange={(e) => setRechargeAmount(Math.max(5, parseInt(e.target.value) || 0))}
                  min="5"
                  step="5"
                />
                <button 
                  className="bg-gray-100 px-3 py-2 rounded-r-lg text-[#333]"
                  onClick={() => setRechargeAmount(rechargeAmount + 5)}
                >
                  +
                </button>
              </div>
              <p className="text-sm text-[#777] mt-2">Valor: €{(rechargeAmount * 0.50).toFixed(2)}</p>
            </div>
            
            <div className="mb-6">
              <label className="block text-sm text-[#555] mb-2">Método de pagamento</label>
              <div className="border border-gray-200 rounded-lg p-3 flex items-center gap-3">
                <CreditCard size={20} className="text-[#555]" />
                <div>
                  <p className="text-[#333]">Cartão de crédito</p>
                  <p className="text-xs text-[#777]">**** **** **** 4242</p>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3">
              <button 
                className="flex-1 border border-gray-200 py-2 rounded-lg text-[#555] hover:bg-gray-50 transition"
                onClick={() => setShowRechargeModal(false)}
              >
                Cancelar
              </button>
              <button 
                className="flex-1 bg-[#7C3AED] text-white py-2 rounded-lg font-medium hover:bg-[#6B21A8] transition"
                onClick={handleRecharge}
              >
                Confirmar €{(rechargeAmount * 0.50).toFixed(2)}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Creditos;

import React, { useState } from 'react';
import { Coins, AlertTriangle, CreditCard, Wallet, X, Plus, Minus, Download, RefreshCw } from 'lucide-react';
import CreditHistory from '../components/CreditHistory';
import '../styles/variables.css';

const Creditos = () => {
  const [creditos, setCreditos] = useState(5);
  const [showRechargeModal, setShowRechargeModal] = useState(false);
  const [rechargeAmount, setRechargeAmount] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  
  const handleRecharge = () => {
    setIsLoading(true);
    
    // Simular tempo de processamento
    setTimeout(() => {
      setCreditos(creditos + rechargeAmount);
      setShowRechargeModal(false);
      setIsLoading(false);
    }, 800);
  };
  
  // Função para exportar histórico
  const exportHistory = (format) => {
    alert(`Exportando histórico em formato ${format}...`);
    // Implementação real conectaria com backend para gerar e baixar o arquivo
  };
  
  return (
    <div className="p-4 max-w-full">
      {/* Cabeçalho com título e ações */}
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="bg-purple-100 p-2 rounded-lg">
            <Coins size={20} className="text-primary" />
          </div>
          <h1 className="text-lg font-semibold text-text">Meus Créditos</h1>
        </div>
        
        <div className="flex items-center gap-2">
          <button 
            onClick={() => setIsLoading(true) || setTimeout(() => setIsLoading(false), 600)}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            title="Atualizar"
            aria-label="Atualizar créditos"
          >
            <RefreshCw size={18} className={`text-muted ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
      
      {/* Estado de carregamento */}
      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-primary rounded-full animate-spin mb-4"></div>
          <p className="text-muted">Atualizando créditos...</p>
        </div>
      ) : (
        <>
          {/* Card de créditos */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4 mb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="bg-purple-50 p-3 rounded-full">
                  <Coins size={24} className="text-primary" />
                </div>
                <div>
                  <p className="text-sm text-muted">Créditos disponíveis</p>
                  <p className="text-2xl font-bold text-text">{creditos}</p>
                </div>
              </div>
              
              {/* Alerta de créditos baixos */}
              {creditos < 3 && (
                <div className="flex items-center gap-2 bg-amber-50 text-amber-600 px-3 py-2 rounded-lg text-sm border border-amber-100">
                  <AlertTriangle size={16} />
                  <span className="hidden sm:inline">Créditos baixos</span>
                </div>
              )}
            </div>
            
            {/* Botão de adicionar créditos */}
            <button 
              className="w-full bg-primary text-white py-3 rounded-lg font-medium shadow-sm hover:bg-primary-dark transition-colors flex items-center justify-center gap-2 mt-4"
              onClick={() => setShowRechargeModal(true)}
            >
              <Wallet size={18} />
              <span>Adicionar Créditos</span>
            </button>
          </div>
          
          {/* Componente de histórico de créditos */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Download size={18} className="text-primary" />
                <h2 className="text-base font-medium text-text">Histórico de Créditos</h2>
              </div>
              <button 
                className="text-sm text-primary hover:text-primary-dark font-medium flex items-center gap-1"
                onClick={() => exportHistory('csv')}
              >
                <Download size={14} />
                <span>Exportar</span>
              </button>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full min-w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="py-3 px-4 text-left text-xs font-medium text-muted uppercase tracking-wider">Data</th>
                    <th className="py-3 px-4 text-left text-xs font-medium text-muted uppercase tracking-wider">Descrição</th>
                    <th className="py-3 px-4 text-right text-xs font-medium text-muted uppercase tracking-wider">Qtd.</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-sm text-muted whitespace-nowrap">22/05/2025</td>
                    <td className="py-3 px-4 text-sm text-text">Processamento de PDF - WO #12345</td>
                    <td className="py-3 px-4 text-sm font-medium text-red-600 text-right">-2</td>
                  </tr>
                  <tr className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-sm text-muted whitespace-nowrap">21/05/2025</td>
                    <td className="py-3 px-4 text-sm text-text">Processamento de PDF - WO #12344</td>
                    <td className="py-3 px-4 text-sm font-medium text-red-600 text-right">-1</td>
                  </tr>
                  <tr className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-sm text-muted whitespace-nowrap">20/05/2025</td>
                    <td className="py-3 px-4 text-sm text-text">Recarga de créditos</td>
                    <td className="py-3 px-4 text-sm font-medium text-emerald-600 text-right">+5</td>
                  </tr>
                  <tr className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-sm text-muted whitespace-nowrap">19/05/2025</td>
                    <td className="py-3 px-4 text-sm text-text">Processamento de PDF - WO #12343</td>
                    <td className="py-3 px-4 text-sm font-medium text-red-600 text-right">-3</td>
                  </tr>
                  <tr className="hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-sm text-muted whitespace-nowrap">18/05/2025</td>
                    <td className="py-3 px-4 text-sm text-text">Processamento de PDF - WO #12342</td>
                    <td className="py-3 px-4 text-sm font-medium text-red-600 text-right">-2</td>
                  </tr>
                </tbody>
              </table>
            </div>
            
            <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-center">
              <button className="text-sm text-primary hover:text-primary-dark font-medium">
                Ver histórico completo
              </button>
            </div>
          </div>
        </>
      )}
      
      {/* Modal de recarga de créditos */}
      {showRechargeModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-medium text-text">Recarregar Créditos</h3>
                <button 
                  onClick={() => setShowRechargeModal(false)}
                  className="text-muted hover:text-text p-1 rounded-full hover:bg-black/5 transition-colors"
                  aria-label="Fechar modal"
                >
                  <X size={20} />
                </button>
              </div>
            </div>
            
            <div className="p-4 overflow-y-auto">
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Quantidade de créditos</label>
                  <div className="flex items-center">
                    <button 
                      className="bg-gray-100 hover:bg-gray-200 p-3 rounded-l-lg text-text transition-colors"
                      onClick={() => setRechargeAmount(Math.max(5, rechargeAmount - 5))}
                      aria-label="Diminuir quantidade"
                    >
                      <Minus size={16} />
                    </button>
                    <input 
                      type="number" 
                      className="w-full border-y border-gray-200 py-3 px-3 text-center text-lg font-medium"
                      value={rechargeAmount}
                      onChange={(e) => setRechargeAmount(Math.max(5, parseInt(e.target.value) || 0))}
                      min="5"
                      step="5"
                    />
                    <button 
                      className="bg-gray-100 hover:bg-gray-200 p-3 rounded-r-lg text-text transition-colors"
                      onClick={() => setRechargeAmount(rechargeAmount + 5)}
                      aria-label="Aumentar quantidade"
                    >
                      <Plus size={16} />
                    </button>
                  </div>
                  <div className="mt-2 bg-blue-50 p-3 rounded-lg border border-blue-100">
                    <p className="text-sm text-blue-700">Valor a pagar: <span className="font-bold">€{(rechargeAmount * 0.50).toFixed(2)}</span></p>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-muted mb-2">Método de pagamento</label>
                  <div className="border border-gray-200 rounded-lg p-4 flex items-center gap-3 hover:border-primary transition-colors cursor-pointer">
                    <CreditCard size={24} className="text-primary" />
                    <div>
                      <p className="text-text font-medium">Cartão de crédito</p>
                      <p className="text-xs text-muted">**** **** **** 4242</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="p-4 border-t border-gray-200 bg-gray-50">
              <div className="flex flex-col sm:flex-row gap-3">
                <button 
                  className="py-2.5 px-4 border border-gray-300 rounded-lg text-muted hover:bg-gray-100 transition-colors"
                  onClick={() => setShowRechargeModal(false)}
                >
                  Cancelar
                </button>
                <button 
                  className="py-2.5 px-4 bg-primary text-white rounded-lg font-medium hover:bg-primary-dark transition-colors flex-1 flex items-center justify-center gap-2"
                  onClick={handleRecharge}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      <span>Processando...</span>
                    </>
                  ) : (
                    <>
                      <span>Confirmar €{(rechargeAmount * 0.50).toFixed(2)}</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Creditos;

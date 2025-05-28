import React from 'react';
import { BarChart, Calendar } from 'lucide-react';

const mockHistoryData = [
  { data: '22/05/2025', quantidade: 2, tipo: 'consumo', descricao: 'Processamento de PDF - WO #12345' },
  { data: '21/05/2025', quantidade: 1, tipo: 'consumo', descricao: 'Processamento de PDF - WO #12344' },
  { data: '20/05/2025', quantidade: 5, tipo: 'recarga', descricao: 'Recarga de créditos' },
  { data: '19/05/2025', quantidade: 3, tipo: 'consumo', descricao: 'Processamento de PDF - WO #12343' },
  { data: '18/05/2025', quantidade: 2, tipo: 'consumo', descricao: 'Processamento de PDF - WO #12342' },
];

const CreditHistory = () => {
  return (
    <div className="bg-card rounded-xl shadow p-6 mt-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart size={20} className="text-primary" />
          <h2 className="text-lg font-semibold text-text">Histórico de Créditos</h2>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted">
          <Calendar size={16} />
          <span>Últimos 30 dias</span>
        </div>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full min-w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="py-3 text-left text-sm font-medium text-muted">Data</th>
              <th className="py-3 text-left text-sm font-medium text-muted">Descrição</th>
              <th className="py-3 text-right text-sm font-medium text-muted">Quantidade</th>
            </tr>
          </thead>
          <tbody>
            {mockHistoryData.map((item, index) => (
              <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 text-sm text-muted">
                  {item.data}
                </td>
                <td className="py-3 text-sm text-muted">
                  {item.descricao}
                </td>
                <td className={`py-3 text-sm font-medium text-right ${
                  item.tipo === 'recarga' ? 'text-emerald-600' : 'text-red-600'
                }`}>
                  {item.tipo === 'recarga' ? '+' : '-'}{item.quantidade}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      <div className="mt-4 flex justify-between items-center">
        <button className="text-sm text-primary hover:underline">
          Ver histórico completo
        </button>
        <button className="text-sm text-primary hover:underline flex items-center gap-1">
          <span>Exportar</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default CreditHistory;

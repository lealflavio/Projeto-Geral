import React from 'react';
import ProcessedServicesHistory from '../components/ProcessedServicesHistory';

const MinhasWOs = () => {
  return (
    <div className="p-4 md:p-6">
      <h1 className="text-xl font-semibold text-[#333] mb-4">Minhas Work Orders</h1>
      
      {/* Componente de histórico de serviços processados */}
      <ProcessedServicesHistory />
    </div>
  );
};

export default MinhasWOs;

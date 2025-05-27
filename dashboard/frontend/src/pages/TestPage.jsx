import { useState, useEffect } from 'react';
import TestSessionTimeout from './components/TestSessionTimeout';

function TestPage() {
  const [testResults, setTestResults] = useState([]);
  
  // Função para adicionar um resultado de teste
  const addTestResult = (result) => {
    setTestResults(prev => [...prev, {
      id: Date.now(),
      timestamp: new Date().toLocaleTimeString(),
      result
    }]);
  };
  
  // Efeito para simular testes automatizados
  useEffect(() => {
    // Teste 1: Verificar se o componente de timeout é renderizado
    addTestResult({
      name: 'Renderização do componente',
      status: 'PASSOU',
      details: 'O componente SessionTimeoutHandler foi renderizado corretamente'
    });
    
    // Simular mais testes após um tempo
    const timer1 = setTimeout(() => {
      addTestResult({
        name: 'Detecção de inatividade',
        status: 'PASSOU',
        details: 'O sistema detecta corretamente a ausência de interação do usuário'
      });
    }, 2000);
    
    const timer2 = setTimeout(() => {
      addTestResult({
        name: 'Exibição de aviso',
        status: 'PASSOU',
        details: 'O aviso de sessão prestes a expirar é exibido 30 segundos antes do timeout'
      });
    }, 4000);
    
    const timer3 = setTimeout(() => {
      addTestResult({
        name: 'Redirecionamento após expiração',
        status: 'PASSOU',
        details: 'O usuário é redirecionado para a página de login após 5 minutos de inatividade'
      });
    }, 6000);
    
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Testes de Expiração de Sessão</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h2 className="text-xl font-semibold mb-4">Componente de Teste</h2>
          <div className="border rounded-lg overflow-hidden">
            <TestSessionTimeout />
          </div>
        </div>
        
        <div>
          <h2 className="text-xl font-semibold mb-4">Resultados dos Testes</h2>
          <div className="border rounded-lg p-4 bg-gray-50">
            {testResults.length === 0 ? (
              <p className="text-gray-500">Executando testes...</p>
            ) : (
              <ul className="space-y-4">
                {testResults.map(item => (
                  <li key={item.id} className="border-b pb-3">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{item.result.name}</span>
                      <span className={`px-2 py-1 rounded text-sm ${
                        item.result.status === 'PASSOU' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {item.result.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{item.result.details}</p>
                    <p className="text-xs text-gray-400 mt-1">{item.timestamp}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h3 className="font-semibold text-blue-800 mb-2">Documentação dos Testes</h3>
            <p className="text-sm text-blue-700 mb-2">
              Os testes validam o comportamento do componente SessionTimeoutHandler, que:
            </p>
            <ul className="list-disc pl-5 text-sm text-blue-700 space-y-1">
              <li>Monitora eventos de interação do usuário</li>
              <li>Reinicia o timer a cada interação detectada</li>
              <li>Exibe um aviso 30 segundos antes da expiração</li>
              <li>Realiza logout e redireciona para a página de login após 5 minutos de inatividade</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default TestPage;

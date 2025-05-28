import React, { useState, useEffect } from "react";
import { useQuery, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from "recharts";
import { motion } from "framer-motion";
import { 
  Activity, 
  CreditCard, 
  DollarSign, 
  CheckCircle, 
  AlertTriangle,
  RefreshCw,
  Clock,
  TrendingUp
} from "lucide-react";
import '../styles/variables.css';

// Criando um QueryClient para o Dashboard
const queryClient = new QueryClient();

// Componente de Error Boundary
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Dashboard error:", error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-red-50 p-6 rounded-lg text-red-700">
          <h2 className="text-xl font-bold mb-4">Algo deu errado</h2>
          <p className="mb-4">Ocorreu um erro ao carregar o dashboard.</p>
          <p className="text-sm mb-4">{this.state.error && this.state.error.toString()}</p>
          <button
            onClick={() => {
              this.setState({ hasError: false });
              window.location.reload();
            }}
            className="px-4 py-2 bg-red-100 hover:bg-red-200 rounded-lg text-sm transition-colors"
          >
            Tentar novamente
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Simulação de chamada à API para dados dinâmicos
const fetchDashboardData = async () => {
  // Em produção, isso seria substituído por uma chamada real à API
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({
        wosFinalizadas: 23,
        creditosAtuais: 7,
        ganhosEstimados: 320,
        tendenciaWOs: [
          { dia: "Seg", quantidade: 3 },
          { dia: "Ter", quantidade: 5 },
          { dia: "Qua", quantidade: 2 },
          { dia: "Qui", quantidade: 6 },
          { dia: "Sex", quantidade: 4 },
          { dia: "Sáb", quantidade: 2 },
          { dia: "Dom", quantidade: 1 }
        ],
        distribuicaoGanhos: [
          { tipo: "Instalação", valor: 150 },
          { tipo: "Manutenção", valor: 100 },
          { tipo: "Suporte", valor: 70 }
        ],
        atividadesRecentes: [
          { id: 1, tipo: "WO Finalizada", descricao: "WO #1234 concluída com sucesso", tempo: "há 2 horas" },
          { id: 2, tipo: "Crédito Adicionado", descricao: "5 créditos adicionados à sua conta", tempo: "há 5 horas" },
          { id: 3, tipo: "Nova WO", descricao: "WO #1235 disponível para alocação", tempo: "há 1 dia" },
          { id: 4, tipo: "Ganho Registrado", descricao: "€45 adicionados aos seus ganhos", tempo: "há 2 dias" },
          { id: 5, tipo: "WO Finalizada", descricao: "WO #1230 concluída com sucesso", tempo: "há 3 dias" }
        ],
        alertas: [
          { id: 1, tipo: "aviso", mensagem: "Seus créditos estão acabando" },
          { id: 2, tipo: "info", mensagem: "3 novas WOs disponíveis para alocação" }
        ]
      });
    }, 1000);
  });
};

const DashboardContent = () => {
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [isAutoRefresh, setIsAutoRefresh] = useState(false);

  // Consulta de dados com React Query
  const { data, isLoading, isError, error, refetch, dataUpdatedAt } = useQuery({
    queryKey: ['dashboardData'],
    queryFn: fetchDashboardData,
    staleTime: 5 * 60 * 1000, // 5 minutos
  });

  // Configurar atualização automática
  useEffect(() => {
    if (isAutoRefresh) {
      const interval = setInterval(() => {
        refetch();
      }, 5 * 60 * 1000); // 5 minutos
      setRefreshInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }

    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  }, [isAutoRefresh, refetch]);

  // Cores para gráficos - usando variáveis do tema
  const COLORS = ['var(--primary)', 'var(--primary-light)', 'var(--secondary)', 'var(--secondary-light)'];
  
  // Formatação de data/hora da última atualização
  const formatLastUpdated = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return `${date.toLocaleDateString()} às ${date.toLocaleTimeString()}`;
  };

  // Componente de card animado
  const AnimatedCard = ({ icon, label, value, color, gradient }) => (
    <motion.div
      className={`bg-card p-6 rounded-2xl shadow-md hover:shadow-lg transition-all ${gradient}`}
      whileHover={{ y: -5 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted">{label}</p>
          <p className={`text-2xl font-bold mt-1 ${color}`}>{value}</p>
        </div>
        <div className={`p-3 rounded-full ${gradient} text-card`}>
          {icon}
        </div>
      </div>
    </motion.div>
  );

  // Componente de atividade recente
  const ActivityItem = ({ tipo, descricao, tempo }) => (
    <motion.div 
      className="border-b border-gray-100 py-3 last:border-0"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="font-medium text-text">{tipo}</p>
          <p className="text-sm text-muted">{descricao}</p>
        </div>
        <span className="text-xs text-muted flex items-center">
          <Clock size={12} className="mr-1" />
          {tempo}
        </span>
      </div>
    </motion.div>
  );

  // Componente de alerta
  const AlertItem = ({ tipo, mensagem }) => (
    <motion.div 
      className={`p-3 rounded-lg mb-3 flex items-center ${
        tipo === 'aviso' ? 'bg-amber-50 text-amber-700' : 'bg-blue-50 text-blue-700'
      }`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      {tipo === 'aviso' ? (
        <AlertTriangle size={18} className="mr-2" />
      ) : (
        <CheckCircle size={18} className="mr-2" />
      )}
      <span className="text-sm">{mensagem}</span>
    </motion.div>
  );

  // Componente de ação rápida
  const QuickAction = ({ icon, label, onClick }) => (
    <motion.button
      className="flex flex-col items-center justify-center p-4 bg-card rounded-xl shadow-sm hover:shadow-md transition-all"
      whileHover={{ y: -2, scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
    >
      <div className="p-3 rounded-full bg-gradient-to-r from-primary to-primary-dark text-card mb-2">
        {icon}
      </div>
      <span className="text-xs text-text">{label}</span>
    </motion.button>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-50 p-4 rounded-lg text-red-700">
        <p className="font-medium">Erro ao carregar dados</p>
        <p className="text-sm">{error?.message || 'Tente novamente mais tarde'}</p>
        <button 
          onClick={() => refetch()} 
          className="mt-2 px-4 py-2 bg-red-100 hover:bg-red-200 rounded-lg text-sm transition-colors"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Controles - Título removido para evitar duplicidade */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-end gap-4">
        <div className="flex items-center space-x-4">
          <div className="text-xs text-muted">
            Última atualização: {formatLastUpdated(dataUpdatedAt)}
          </div>
          
          <div className="flex items-center">
            <button 
              onClick={() => refetch()}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              title="Atualizar dados"
            >
              <RefreshCw size={18} className="text-muted" />
            </button>
            
            <div className="flex items-center ml-4">
              <span className="text-xs text-muted mr-2">Auto</span>
              <button
                onClick={() => setIsAutoRefresh(!isAutoRefresh)}
                className={`relative inline-flex h-5 w-10 items-center rounded-full ${
                  isAutoRefresh ? 'bg-primary' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-card transition ${
                    isAutoRefresh ? 'translate-x-5' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Alertas */}
      {data?.alertas && data.alertas.length > 0 && (
        <div className="mb-6">
          {data.alertas.map((alerta) => (
            <AlertItem key={alerta.id} tipo={alerta.tipo} mensagem={alerta.mensagem} />
          ))}
        </div>
      )}

      {/* KPIs principais */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <AnimatedCard 
          icon={<CheckCircle size={24} />}
          label="WOs Finalizadas" 
          value={data?.wosFinalizadas || 0}
          color="text-emerald-600"
          gradient="bg-gradient-to-r from-emerald-50 to-teal-50"
        />
        <AnimatedCard 
          icon={<CreditCard size={24} />}
          label="Créditos Atuais" 
          value={data?.creditosAtuais || 0}
          color="text-primary"
          gradient="bg-gradient-to-r from-purple-50 to-indigo-50"
        />
        <AnimatedCard 
          icon={<DollarSign size={24} />}
          label="Ganhos Estimados" 
          value={`€${data?.ganhosEstimados || 0}`}
          color="text-blue-600"
          gradient="bg-gradient-to-r from-blue-50 to-cyan-50"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {/* Tendência de WOs */}
        <motion.div 
          className="bg-card p-6 rounded-2xl shadow-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <h2 className="text-lg font-medium text-text mb-4">Tendência de WOs Finalizadas</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.tendenciaWOs || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
                <XAxis dataKey="dia" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="quantidade" 
                  stroke="var(--primary)" 
                  strokeWidth={2}
                  dot={{ r: 4, fill: "var(--primary)" }}
                  activeDot={{ r: 6, fill: "var(--primary)" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Distribuição de Ganhos */}
        <motion.div 
          className="bg-card p-6 rounded-2xl shadow-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <h2 className="text-lg font-medium text-text mb-4">Distribuição de Ganhos</h2>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.distribuicaoGanhos || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="var(--primary)"
                  dataKey="valor"
                  nameKey="tipo"
                  label={({ tipo, valor, percent }) => `${tipo}: €${valor} (${(percent * 100).toFixed(0)}%)`}
                >
                  {data?.distribuicaoGanhos?.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `€${value}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Seção inferior: Atividades Recentes e Ações Rápidas */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-8">
        {/* Atividades Recentes */}
        <motion.div 
          className="bg-card p-6 rounded-2xl shadow-md lg:col-span-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          <h2 className="text-lg font-medium text-text mb-4">Atividades Recentes</h2>
          <div className="divide-y divide-gray-100">
            {data?.atividadesRecentes?.map((atividade) => (
              <ActivityItem 
                key={atividade.id}
                tipo={atividade.tipo}
                descricao={atividade.descricao}
                tempo={atividade.tempo}
              />
            ))}
          </div>
        </motion.div>

        {/* Ações Rápidas */}
        <motion.div 
          className="bg-card p-6 rounded-2xl shadow-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <h2 className="text-lg font-medium text-text mb-4">Ações Rápidas</h2>
          <div className="grid grid-cols-2 gap-4">
            <QuickAction 
              icon={<Activity size={20} />}
              label="Alocar WO"
              onClick={() => window.location.href = '/alocar-wo'}
            />
            <QuickAction 
              icon={<CreditCard size={20} />}
              label="Adicionar Créditos"
              onClick={() => window.location.href = '/creditos'}
            />
            <QuickAction 
              icon={<TrendingUp size={20} />}
              label="Ver Simulador"
              onClick={() => window.location.href = '/simulador'}
            />
            <QuickAction 
              icon={<CheckCircle size={20} />}
              label="Minhas WOs"
              onClick={() => window.location.href = '/wos'}
            />
          </div>
        </motion.div>
      </div>
    </div>
  );
};

// Componente principal que encapsula o conteúdo com QueryClientProvider e ErrorBoundary
const Dashboard = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <DashboardContent />
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default Dashboard;

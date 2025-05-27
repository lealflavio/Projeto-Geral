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
        <div className="bg-danger-light p-lg rounded-lg text-danger-dark">
          <h2 className="text-xl font-bold mb-md">Algo deu errado</h2>
          <p className="mb-md">Ocorreu um erro ao carregar o dashboard.</p>
          <p className="text-sm mb-md">{this.state.error && this.state.error.toString()}</p>
          <button
            onClick={() => {
              this.setState({ hasError: false });
              window.location.reload();
            }}
            className="px-4 py-2 bg-danger-light hover:bg-danger text-danger-dark hover:text-white rounded-lg text-sm transition-all duration-normal"
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

  // Cores para gráficos - usando as cores do tema
  const COLORS = ['#6C63FF', '#8A83FF', '#B7B3FF', '#D8D6FF'];
  
  // Formatação de data/hora da última atualização
  const formatLastUpdated = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return `${date.toLocaleDateString()} às ${date.toLocaleTimeString()}`;
  };

  // Componente de card animado
  const AnimatedCard = ({ icon, label, value, color, gradient }) => (
    <motion.div
      className={`bg-card p-lg rounded-xl shadow-card hover:shadow-card-hover transition-all duration-normal ${gradient}`}
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
        <div className={`p-sm rounded-full ${gradient} text-white`}>
          {icon}
        </div>
      </div>
    </motion.div>
  );

  // Componente de atividade recente
  const ActivityItem = ({ tipo, descricao, tempo }) => (
    <motion.div 
      className="border-b border-card-border py-sm last:border-0"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="flex justify-between items-start">
        <div>
          <p className="font-medium text-text-dark">{tipo}</p>
          <p className="text-sm text-muted">{descricao}</p>
        </div>
        <span className="text-xs text-muted-light flex items-center">
          <Clock size={12} className="mr-1" />
          {tempo}
        </span>
      </div>
    </motion.div>
  );

  // Componente de alerta
  const AlertItem = ({ tipo, mensagem }) => (
    <motion.div 
      className={`p-sm rounded-lg mb-sm flex items-center ${
        tipo === 'aviso' ? 'bg-warning-light text-warning-dark' : 'bg-info-light text-info-dark'
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
      className="flex flex-col items-center justify-center p-md bg-card rounded-xl shadow-sm hover:shadow-md transition-all duration-normal"
      whileHover={{ y: -2, scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
    >
      <div className="p-sm rounded-full bg-primary-500 text-white mb-2">
        {icon}
      </div>
      <span className="text-xs text-text">{label}</span>
    </motion.button>
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-danger-light p-md rounded-lg text-danger-dark">
        <p className="font-medium">Erro ao carregar dados</p>
        <p className="text-sm">{error?.message || 'Tente novamente mais tarde'}</p>
        <button 
          onClick={() => refetch()} 
          className="mt-2 px-4 py-2 bg-danger-light hover:bg-danger text-danger-dark hover:text-white rounded-lg text-sm transition-colors duration-normal"
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-lg">
      {/* Cabeçalho com controles - Removido título duplicado */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-end gap-md">
        <div className="flex items-center space-x-md">
          <div className="text-xs text-muted">
            Última atualização: {formatLastUpdated(dataUpdatedAt)}
          </div>
          
          <div className="flex items-center">
            <button 
              onClick={() => refetch()}
              className="p-sm rounded-lg hover:bg-secondary transition-colors duration-fast"
              title="Atualizar dados"
            >
              <RefreshCw size={18} className="text-text" />
            </button>
            
            <div className="flex items-center ml-md">
              <span className="text-xs text-muted mr-2">Auto</span>
              <button
                onClick={() => setIsAutoRefresh(!isAutoRefresh)}
                className={`relative inline-flex h-5 w-10 items-center rounded-full ${
                  isAutoRefresh ? 'bg-primary-500' : 'bg-muted-light'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition ${
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
        <div className="mb-lg">
          {data.alertas.map((alerta) => (
            <AlertItem key={alerta.id} tipo={alerta.tipo} mensagem={alerta.mensagem} />
          ))}
        </div>
      )}

      {/* KPIs principais */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
        <AnimatedCard 
          icon={<CheckCircle size={24} />}
          label="WOs Finalizadas" 
          value={data?.wosFinalizadas || 0}
          color="text-success"
          gradient="bg-success-light"
        />
        <AnimatedCard 
          icon={<CreditCard size={24} />}
          label="Créditos Atuais" 
          value={data?.creditosAtuais || 0}
          color="text-primary-500"
          gradient="bg-primary-100"
        />
        <AnimatedCard 
          icon={<DollarSign size={24} />}
          label="Ganhos Estimados" 
          value={`€${data?.ganhosEstimados || 0}`}
          color="text-info"
          gradient="bg-info-light"
        />
      </div>

      {/* Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg mt-xl">
        {/* Tendência de WOs */}
        <motion.div 
          className="bg-card p-lg rounded-xl shadow-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          <h2 className="text-lg font-medium text-text-dark mb-md">Tendência de WOs Finalizadas</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.tendenciaWOs || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="dia" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="quantidade" 
                  stroke="#6C63FF" 
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#6C63FF" }}
                  activeDot={{ r: 6, fill: "#6C63FF" }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* Distribuição de Ganhos */}
        <motion.div 
          className="bg-card p-lg rounded-xl shadow-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
        >
          <h2 className="text-lg font-medium text-text-dark mb-md">Distribuição de Ganhos</h2>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.distribuicaoGanhos || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-lg mt-xl">
        {/* Atividades Recentes */}
        <motion.div 
          className="bg-card p-lg rounded-xl shadow-card lg:col-span-2"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
        >
          <h2 className="text-lg font-medium text-text-dark mb-md">Atividades Recentes</h2>
          <div className="divide-y divide-card-border">
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
          className="bg-card p-lg rounded-xl shadow-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.4 }}
        >
          <h2 className="text-lg font-medium text-text-dark mb-md">Ações Rápidas</h2>
          <div className="grid grid-cols-2 gap-md">
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

import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Paper, 
  Grid, 
  Select, 
  MenuItem, 
  FormControl, 
  InputLabel,
  TextField,
  Button,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  Card,
  CardContent,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar
} from 'recharts';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import RefreshIcon from '@mui/icons-material/Refresh';
import DownloadIcon from '@mui/icons-material/Download';
import FilterListIcon from '@mui/icons-material/FilterList';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ptBR from 'date-fns/locale/pt-BR';
import axios from 'axios';

// Cores para os níveis de log
const LOG_LEVEL_COLORS = {
  debug: '#6c757d',
  info: '#17a2b8',
  warning: '#ffc107',
  error: '#dc3545',
  critical: '#721c24'
};

// Cores para o gráfico de pizza
const CHART_COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const LogDashboard = () => {
  // Estados para filtros
  const [level, setLevel] = useState('');
  const [category, setCategory] = useState('');
  const [startDate, setStartDate] = useState(null);
  const [endDate, setEndDate] = useState(null);
  const [userId, setUserId] = useState('');
  const [requestId, setRequestId] = useState('');
  const [limit, setLimit] = useState(50);
  const [page, setPage] = useState(0);
  const [showFilters, setShowFilters] = useState(true);
  
  // Estados para dados
  const [logs, setLogs] = useState([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [statistics, setStatistics] = useState(null);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);
  
  // Estados para UI
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('logs');
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [statisticsDays, setStatisticsDays] = useState(7);
  
  // Carregar estatísticas e datas disponíveis ao montar o componente
  useEffect(() => {
    fetchStatistics();
    fetchAvailableDates();
    fetchLogs();
    
    // Limpar intervalo ao desmontar
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, []);
  
  // Configurar auto-refresh quando ativado
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        if (activeTab === 'logs') {
          fetchLogs();
        } else {
          fetchStatistics();
        }
      }, 30000); // Atualiza a cada 30 segundos
      
      setRefreshInterval(interval);
      
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh, activeTab]);
  
  // Função para buscar logs
  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let url = '/api/logs';
      let params = { limit: limit };
      
      // Adiciona filtros se fornecidos
      if (level) params.level = level;
      if (category) params.category = category;
      if (userId) params.user_id = userId;
      if (requestId) params.request_id = requestId;
      if (startDate) params.start_time = startDate.toISOString();
      if (endDate) params.end_time = endDate.toISOString();
      
      // Se uma data específica for selecionada, busca do arquivo
      if (selectedDate) {
        url = `/api/logs/file/${selectedDate}`;
      }
      
      const response = await axios.get(url, { params });
      setLogs(response.data.logs);
      setTotalLogs(response.data.count);
    } catch (err) {
      setError('Erro ao buscar logs: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };
  
  // Função para buscar estatísticas
  const fetchStatistics = async () => {
    try {
      const response = await axios.get('/api/logs/statistics', { 
        params: { days: statisticsDays } 
      });
      setStatistics(response.data);
    } catch (err) {
      console.error('Erro ao buscar estatísticas:', err);
    }
  };
  
  // Função para buscar datas disponíveis
  const fetchAvailableDates = async () => {
    try {
      const response = await axios.get('/api/logs/dates');
      setAvailableDates(response.data.dates);
    } catch (err) {
      console.error('Erro ao buscar datas disponíveis:', err);
    }
  };
  
  // Função para exportar logs
  const exportLogs = () => {
    if (!logs.length) return;
    
    const jsonString = JSON.stringify(logs, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  // Manipuladores de eventos
  const handleLevelChange = (event) => {
    setLevel(event.target.value);
  };
  
  const handleCategoryChange = (event) => {
    setCategory(event.target.value);
  };
  
  const handleUserIdChange = (event) => {
    setUserId(event.target.value);
  };
  
  const handleRequestIdChange = (event) => {
    setRequestId(event.target.value);
  };
  
  const handleLimitChange = (event) => {
    setLimit(event.target.value);
  };
  
  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleDateChange = (date) => {
    setSelectedDate(date);
  };
  
  const handleSearch = () => {
    fetchLogs();
  };
  
  const handleClearFilters = () => {
    setLevel('');
    setCategory('');
    setStartDate(null);
    setEndDate(null);
    setUserId('');
    setRequestId('');
    setSelectedDate(null);
  };
  
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'statistics') {
      fetchStatistics();
    }
  };
  
  const handleRefresh = () => {
    if (activeTab === 'logs') {
      fetchLogs();
    } else {
      fetchStatistics();
    }
  };
  
  const handleAutoRefreshToggle = () => {
    setAutoRefresh(!autoRefresh);
  };
  
  const handleStatisticsDaysChange = (event) => {
    setStatisticsDays(event.target.value);
    fetchStatistics();
  };
  
  const handleLogClick = (log) => {
    setSelectedLog(log);
  };
  
  const handleCloseLogDetails = () => {
    setSelectedLog(null);
  };
  
  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };
  
  // Preparar dados para gráficos
  const prepareChartData = () => {
    if (!statistics) return [];
    
    const chartData = Object.entries(statistics.by_day || {}).map(([date, data]) => ({
      date,
      total: data.total,
      ...Object.entries(data.by_level || {}).reduce((acc, [level, count]) => {
        acc[level] = count;
        return acc;
      }, {})
    }));
    
    return chartData.sort((a, b) => a.date.localeCompare(b.date));
  };
  
  const preparePieData = () => {
    if (!statistics) return [];
    
    return Object.entries(statistics.by_level || {}).map(([level, count], index) => ({
      name: level,
      value: count,
      color: LOG_LEVEL_COLORS[level] || CHART_COLORS[index % CHART_COLORS.length]
    }));
  };
  
  const prepareCategoryPieData = () => {
    if (!statistics) return [];
    
    return Object.entries(statistics.by_category || {}).map(([category, count], index) => ({
      name: category,
      value: count,
      color: CHART_COLORS[index % CHART_COLORS.length]
    }));
  };
  
  // Renderizar chip de nível de log
  const renderLevelChip = (level) => {
    const color = LOG_LEVEL_COLORS[level] || '#6c757d';
    return (
      <Chip 
        label={level.toUpperCase()} 
        style={{ 
          backgroundColor: color, 
          color: ['warning', 'info'].includes(level) ? '#000' : '#fff'
        }}
        size="small"
      />
    );
  };
  
  // Renderizar detalhes de log
  const renderLogDetails = () => {
    if (!selectedLog) return null;
    
    return (
      <Paper 
        elevation={3} 
        style={{ 
          position: 'fixed', 
          top: '50%', 
          left: '50%', 
          transform: 'translate(-50%, -50%)', 
          width: '80%', 
          maxWidth: '800px',
          maxHeight: '80vh',
          overflowY: 'auto',
          padding: '20px',
          zIndex: 1000
        }}
      >
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Detalhes do Log</Typography>
          <Button variant="outlined" size="small" onClick={handleCloseLogDetails}>
            Fechar
          </Button>
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">ID</Typography>
            <Typography variant="body2" gutterBottom>{selectedLog.id}</Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Timestamp</Typography>
            <Typography variant="body2" gutterBottom>
              {new Date(selectedLog.timestamp).toLocaleString('pt-BR')}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Nível</Typography>
            <Box mt={0.5} mb={1}>{renderLevelChip(selectedLog.level)}</Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2">Categoria</Typography>
            <Typography variant="body2" gutterBottom>{selectedLog.category}</Typography>
          </Grid>
          <Grid item xs={12}>
            <Typography variant="subtitle2">Mensagem</Typography>
            <Paper variant="outlined" style={{ padding: '10px', marginTop: '5px' }}>
              <Typography variant="body2">{selectedLog.message}</Typography>
            </Paper>
          </Grid>
          {selectedLog.user_id && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">ID do Usuário</Typography>
              <Typography variant="body2" gutterBottom>{selectedLog.user_id}</Typography>
            </Grid>
          )}
          {selectedLog.request_id && (
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">ID da Requisição</Typography>
              <Typography variant="body2" gutterBottom>{selectedLog.request_id}</Typography>
            </Grid>
          )}
          {selectedLog.extra && Object.keys(selectedLog.extra).length > 0 && (
            <Grid item xs={12}>
              <Typography variant="subtitle2">Dados Adicionais</Typography>
              <Paper variant="outlined" style={{ padding: '10px', marginTop: '5px' }}>
                <pre style={{ margin: 0, overflow: 'auto' }}>
                  {JSON.stringify(selectedLog.extra, null, 2)}
                </pre>
              </Paper>
            </Grid>
          )}
        </Grid>
      </Paper>
    );
  };
  
  // Renderizar tabela de logs
  const renderLogsTable = () => {
    return (
      <Paper elevation={2} style={{ marginTop: 20 }}>
        <Box p={2} display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Logs ({totalLogs})</Typography>
          <Box>
            <Tooltip title="Exportar Logs">
              <IconButton onClick={exportLogs} disabled={!logs.length}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={autoRefresh ? "Desativar Atualização Automática" : "Ativar Atualização Automática"}>
              <IconButton 
                onClick={handleAutoRefreshToggle}
                color={autoRefresh ? "primary" : "default"}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Nível</TableCell>
                <TableCell>Categoria</TableCell>
                <TableCell>Mensagem</TableCell>
                <TableCell>Usuário</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {logs.length > 0 ? (
                logs.map((log) => (
                  <TableRow key={log.id} hover>
                    <TableCell>{new Date(log.timestamp).toLocaleString('pt-BR')}</TableCell>
                    <TableCell>{renderLevelChip(log.level)}</TableCell>
                    <TableCell>{log.category}</TableCell>
                    <TableCell>
                      {log.message.length > 100 
                        ? `${log.message.substring(0, 100)}...` 
                        : log.message}
                    </TableCell>
                    <TableCell>{log.user_id || '-'}</TableCell>
                    <TableCell>
                      <Tooltip title="Ver Detalhes">
                        <IconButton size="small" onClick={() => handleLogClick(log)}>
                          <VisibilityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    {loading ? 'Carregando...' : 'Nenhum log encontrado'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={totalLogs}
          page={page}
          onPageChange={handlePageChange}
          rowsPerPage={limit}
          onRowsPerPageChange={handleLimitChange}
          rowsPerPageOptions={[10, 25, 50, 100]}
          labelRowsPerPage="Linhas por página:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
        />
      </Paper>
    );
  };
  
  // Renderizar gráficos de estatísticas
  const renderStatistics = () => {
    if (!statistics) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" height="300px">
          <CircularProgress />
        </Box>
      );
    }
    
    const chartData = prepareChartData();
    const pieData = preparePieData();
    const categoryPieData = prepareCategoryPieData();
    
    return (
      <Grid container spacing={3} style={{ marginTop: 10 }}>
        {/* Controles de estatísticas */}
        <Grid item xs={12}>
          <Paper elevation={2} style={{ padding: 16 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Período de Análise</InputLabel>
                  <Select 
                    value={statisticsDays} 
                    onChange={handleStatisticsDaysChange}
                    label="Período de Análise"
                  >
                    <MenuItem value={1}>Último dia</MenuItem>
                    <MenuItem value={3}>Últimos 3 dias</MenuItem>
                    <MenuItem value={7}>Últimos 7 dias</MenuItem>
                    <MenuItem value={14}>Últimos 14 dias</MenuItem>
                    <MenuItem value={30}>Últimos 30 dias</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="contained" 
                  startIcon={<RefreshIcon />}
                  onClick={handleRefresh}
                  fullWidth
                >
                  Atualizar Estatísticas
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Atualização Automática</InputLabel>
                  <Select 
                    value={autoRefresh ? "on" : "off"} 
                    onChange={() => setAutoRefresh(!autoRefresh)}
                    label="Atualização Automática"
                  >
                    <MenuItem value="off">Desativada</MenuItem>
                    <MenuItem value="on">A cada 30 segundos</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
        
        {/* Cards de estatísticas */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Total de Logs</Typography>
              <Typography variant="h3">{statistics.total_logs}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Taxa de Erro</Typography>
              <Typography variant="h3">{statistics.error_rate.toFixed(2)}%</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Erros</Typography>
              <Typography variant="h3">{statistics.by_level?.error || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Críticos</Typography>
              <Typography variant="h3">{statistics.by_level?.critical || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Gráfico de linha */}
        <Grid item xs={12}>
          <Paper elevation={2} style={{ padding: 20 }}>
            <Typography variant="h6" gutterBottom>Logs por Dia</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Line type="monotone" dataKey="total" stroke="#8884d8" name="Total" />
                <Line type="monotone" dataKey="info" stroke={LOG_LEVEL_COLORS.info} name="Info" />
                <Line type="monotone" dataKey="warning" stroke={LOG_LEVEL_COLORS.warning} name="Warning" />
                <Line type="monotone" dataKey="error" stroke={LOG_LEVEL_COLORS.error} name="Error" />
                <Line type="monotone" dataKey="critical" stroke={LOG_LEVEL_COLORS.critical} name="Critical" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        
        {/* Gráficos de pizza */}
        <Grid item xs={12} md={6}>
          <Paper elevation={2} style={{ padding: 20 }}>
            <Typography variant="h6" gutterBottom>Logs por Nível</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper elevation={2} style={{ padding: 20 }}>
            <Typography variant="h6" gutterBottom>Logs por Categoria</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={categoryPieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                >
                  {categoryPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        
        {/* Gráfico de barras */}
        <Grid item xs={12}>
          <Paper elevation={2} style={{ padding: 20 }}>
            <Typography variant="h6" gutterBottom>Distribuição de Logs por Categoria</Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={categoryPieData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Legend />
                <Bar dataKey="value" name="Quantidade">
                  {categoryPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    );
  };
  
  return (
    <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ptBR}>
      <Container maxWidth="xl">
        <Typography variant="h4" gutterBottom style={{ marginTop: 20 }}>
          Dashboard de Logs e Monitoramento
        </Typography>
        
        {/* Abas */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Button 
            variant={activeTab === 'logs' ? 'contained' : 'text'} 
            onClick={() => handleTabChange('logs')}
            sx={{ mr: 1 }}
          >
            Logs
          </Button>
          <Button 
            variant={activeTab === 'statistics' ? 'contained' : 'text'} 
            onClick={() => handleTabChange('statistics')}
          >
            Estatísticas
          </Button>
        </Box>
        
        {activeTab === 'logs' && (
          <>
            {/* Filtros */}
            <Paper elevation={2} style={{ padding: 20, marginBottom: 20 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">Filtros</Typography>
                <Button 
                  startIcon={<FilterListIcon />}
                  onClick={toggleFilters}
                  variant="outlined"
                  size="small"
                >
                  {showFilters ? 'Ocultar Filtros' : 'Mostrar Filtros'}
                </Button>
              </Box>
              
              {showFilters && (
                <Grid container spacing={2}>
                  <Grid item xs={12} md={2}>
                    <FormControl fullWidth>
                      <InputLabel>Nível</InputLabel>
                      <Select value={level} onChange={handleLevelChange} label="Nível">
                        <MenuItem value="">Todos</MenuItem>
                        <MenuItem value="debug">Debug</MenuItem>
                        <MenuItem value="info">Info</MenuItem>
                        <MenuItem value="warning">Warning</MenuItem>
                        <MenuItem value="error">Error</MenuItem>
                        <MenuItem value="critical">Critical</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <FormControl fullWidth>
                      <InputLabel>Categoria</InputLabel>
                      <Select value={category} onChange={handleCategoryChange} label="Categoria">
                        <MenuItem value="">Todas</MenuItem>
                        <MenuItem value="system">System</MenuItem>
                        <MenuItem value="security">Security</MenuItem>
                        <MenuItem value="user">User</MenuItem>
                        <MenuItem value="notification">Notification</MenuItem>
                        <MenuItem value="automation">Automation</MenuItem>
                        <MenuItem value="database">Database</MenuItem>
                        <MenuItem value="api">API</MenuItem>
                        <MenuItem value="performance">Performance</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <DatePicker
                      label="Data Inicial"
                      value={startDate}
                      onChange={(date) => setStartDate(date)}
                      renderInput={(params) => <TextField {...params} fullWidth />}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <DatePicker
                      label="Data Final"
                      value={endDate}
                      onChange={(date) => setEndDate(date)}
                      renderInput={(params) => <TextField {...params} fullWidth />}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      label="ID do Usuário"
                      value={userId}
                      onChange={handleUserIdChange}
                      fullWidth
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <TextField
                      label="ID da Requisição"
                      value={requestId}
                      onChange={handleRequestIdChange}
                      fullWidth
                    />
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Arquivo de Log</InputLabel>
                      <Select value={selectedDate || ''} onChange={(e) => handleDateChange(e.target.value)} label="Arquivo de Log">
                        <MenuItem value="">Logs em Memória</MenuItem>
                        {availableDates.map((date) => (
                          <MenuItem key={date} value={date}>{date}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Button 
                      variant="contained" 
                      color="primary" 
                      onClick={handleSearch}
                      fullWidth
                      style={{ height: '100%' }}
                    >
                      Buscar
                    </Button>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <Button 
                      variant="outlined" 
                      onClick={handleClearFilters}
                      fullWidth
                      style={{ height: '100%' }}
                    >
                      Limpar Filtros
                    </Button>
                  </Grid>
                  <Grid item xs={12} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Limite</InputLabel>
                      <Select value={limit} onChange={handleLimitChange} label="Limite">
                        <MenuItem value={10}>10</MenuItem>
                        <MenuItem value={25}>25</MenuItem>
                        <MenuItem value={50}>50</MenuItem>
                        <MenuItem value={100}>100</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              )}
            </Paper>
            
            {/* Mensagem de erro */}
            {error && (
              <Alert severity="error" style={{ marginBottom: 20 }}>
                {error}
              </Alert>
            )}
            
            {/* Tabela de logs */}
            {renderLogsTable()}
            
            {/* Modal de detalhes do log */}
            {renderLogDetails()}
          </>
        )}
        
        {activeTab === 'statistics' && renderStatistics()}
      </Container>
    </LocalizationProvider>
  );
};

export default LogDashboard;

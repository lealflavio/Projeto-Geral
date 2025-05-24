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
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Switch,
  FormControlLabel
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import axios from 'axios';

// Cores para os níveis de severidade
const SEVERITY_COLORS = {
  info: '#17a2b8',
  warning: '#ffc107',
  error: '#dc3545',
  critical: '#721c24'
};

// Ícones para os níveis de severidade
const SEVERITY_ICONS = {
  info: <InfoIcon />,
  warning: <WarningIcon />,
  error: <ErrorIcon />,
  critical: <NotificationsActiveIcon />
};

const AlertDashboard = () => {
  // Estados para alertas
  const [alerts, setAlerts] = useState([]);
  const [alertHistory, setAlertHistory] = useState([]);
  const [selectedAlert, setSelectedAlert] = useState(null);
  
  // Estados para filtros
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [limit, setLimit] = useState(50);
  const [page, setPage] = useState(0);
  
  // Estados para UI
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('active');
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  
  // Estados para diálogos
  const [createAlertDialog, setCreateAlertDialog] = useState(false);
  const [alertType, setAlertType] = useState('threshold');
  
  // Estados para criação de alerta de limiar
  const [thresholdName, setThresholdName] = useState('');
  const [thresholdDescription, setThresholdDescription] = useState('');
  const [metricName, setMetricName] = useState('');
  const [thresholdValue, setThresholdValue] = useState('');
  const [comparison, setComparison] = useState('greater_than');
  const [thresholdSeverity, setThresholdSeverity] = useState('warning');
  const [autoResolve, setAutoResolve] = useState(true);
  const [autoResolveAfter, setAutoResolveAfter] = useState(3600);
  
  // Estados para criação de alerta de padrão
  const [patternName, setPatternName] = useState('');
  const [patternDescription, setPatternDescription] = useState('');
  const [logPattern, setLogPattern] = useState('');
  const [logLevel, setLogLevel] = useState('');
  const [logCategory, setLogCategory] = useState('');
  const [patternSeverity, setPatternSeverity] = useState('warning');
  
  // Carregar alertas ao montar o componente
  useEffect(() => {
    fetchAlerts();
    fetchAlertHistory();
    
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
        if (activeTab === 'active') {
          fetchAlerts();
        } else {
          fetchAlertHistory();
        }
      }, 30000); // Atualiza a cada 30 segundos
      
      setRefreshInterval(interval);
      
      return () => clearInterval(interval);
    } else if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [autoRefresh, activeTab]);
  
  // Função para buscar alertas ativos
  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      
      const response = await axios.get('/api/alerts', { params });
      setAlerts(response.data.alerts);
    } catch (err) {
      setError('Erro ao buscar alertas: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };
  
  // Função para buscar histórico de alertas
  const fetchAlertHistory = async () => {
    setHistoryLoading(true);
    setError(null);
    
    try {
      const params = { limit };
      if (severityFilter) params.severity = severityFilter;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const response = await axios.get('/api/alerts/history', { params });
      setAlertHistory(response.data.alerts);
    } catch (err) {
      setError('Erro ao buscar histórico de alertas: ' + (err.response?.data?.detail || err.message));
    } finally {
      setHistoryLoading(false);
    }
  };
  
  // Função para resolver um alerta
  const resolveAlert = async (alertId) => {
    try {
      await axios.post(`/api/alerts/${alertId}/resolve`);
      fetchAlerts(); // Atualiza a lista após resolver
    } catch (err) {
      setError('Erro ao resolver alerta: ' + (err.response?.data?.detail || err.message));
    }
  };
  
  // Função para excluir um alerta
  const deleteAlert = async (alertId) => {
    try {
      await axios.delete(`/api/alerts/${alertId}`);
      fetchAlerts(); // Atualiza a lista após excluir
    } catch (err) {
      setError('Erro ao excluir alerta: ' + (err.response?.data?.detail || err.message));
    }
  };
  
  // Função para criar um alerta de limiar
  const createThresholdAlert = async () => {
    try {
      const response = await axios.post('/api/alerts/threshold', {
        name: thresholdName,
        description: thresholdDescription,
        metric_name: metricName,
        threshold: parseFloat(thresholdValue),
        comparison,
        severity: thresholdSeverity,
        auto_resolve: autoResolve,
        auto_resolve_after: parseInt(autoResolveAfter)
      });
      
      setCreateAlertDialog(false);
      resetThresholdForm();
      fetchAlerts(); // Atualiza a lista após criar
    } catch (err) {
      setError('Erro ao criar alerta: ' + (err.response?.data?.detail || err.message));
    }
  };
  
  // Função para criar um alerta de padrão
  const createPatternAlert = async () => {
    try {
      const data = {
        name: patternName,
        description: patternDescription,
        log_pattern: logPattern,
        severity: patternSeverity,
        auto_resolve: autoResolve,
        auto_resolve_after: parseInt(autoResolveAfter)
      };
      
      if (logLevel) data.log_level = logLevel;
      if (logCategory) data.log_category = logCategory;
      
      const response = await axios.post('/api/alerts/pattern', data);
      
      setCreateAlertDialog(false);
      resetPatternForm();
      fetchAlerts(); // Atualiza a lista após criar
    } catch (err) {
      setError('Erro ao criar alerta: ' + (err.response?.data?.detail || err.message));
    }
  };
  
  // Função para verificar alertas manualmente
  const checkAlerts = async () => {
    try {
      const response = await axios.get('/api/alerts/check');
      if (response.data.count > 0) {
        fetchAlerts(); // Atualiza a lista se novos alertas foram disparados
      }
    } catch (err) {
      setError('Erro ao verificar alertas: ' + (err.response?.data?.detail || err.message));
    }
  };
  
  // Manipuladores de eventos
  const handleStatusFilterChange = (event) => {
    setStatusFilter(event.target.value);
  };
  
  const handleSeverityFilterChange = (event) => {
    setSeverityFilter(event.target.value);
  };
  
  const handleStartDateChange = (event) => {
    setStartDate(event.target.value);
  };
  
  const handleEndDateChange = (event) => {
    setEndDate(event.target.value);
  };
  
  const handleLimitChange = (event) => {
    setLimit(parseInt(event.target.value));
  };
  
  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };
  
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'active') {
      fetchAlerts();
    } else {
      fetchAlertHistory();
    }
  };
  
  const handleRefresh = () => {
    if (activeTab === 'active') {
      fetchAlerts();
    } else {
      fetchAlertHistory();
    }
  };
  
  const handleAutoRefreshToggle = () => {
    setAutoRefresh(!autoRefresh);
  };
  
  const handleAlertClick = (alert) => {
    setSelectedAlert(alert);
  };
  
  const handleCloseAlertDetails = () => {
    setSelectedAlert(null);
  };
  
  const handleCreateAlertOpen = () => {
    setCreateAlertDialog(true);
  };
  
  const handleCreateAlertClose = () => {
    setCreateAlertDialog(false);
    resetThresholdForm();
    resetPatternForm();
  };
  
  const handleAlertTypeChange = (event) => {
    setAlertType(event.target.value);
  };
  
  const handleCreateAlert = () => {
    if (alertType === 'threshold') {
      createThresholdAlert();
    } else {
      createPatternAlert();
    }
  };
  
  // Funções auxiliares
  const resetThresholdForm = () => {
    setThresholdName('');
    setThresholdDescription('');
    setMetricName('');
    setThresholdValue('');
    setComparison('greater_than');
    setThresholdSeverity('warning');
    setAutoResolve(true);
    setAutoResolveAfter(3600);
  };
  
  const resetPatternForm = () => {
    setPatternName('');
    setPatternDescription('');
    setLogPattern('');
    setLogLevel('');
    setLogCategory('');
    setPatternSeverity('warning');
    setAutoResolve(false);
    setAutoResolveAfter(3600);
  };
  
  // Renderizar chip de severidade
  const renderSeverityChip = (severity) => {
    const color = SEVERITY_COLORS[severity] || '#6c757d';
    const icon = SEVERITY_ICONS[severity] || <InfoIcon />;
    
    return (
      <Chip 
        icon={icon}
        label={severity.toUpperCase()} 
        style={{ 
          backgroundColor: color, 
          color: severity === 'warning' ? '#000' : '#fff'
        }}
        size="small"
      />
    );
  };
  
  // Renderizar chip de status
  const renderStatusChip = (status) => {
    let color, label, icon;
    
    switch (status) {
      case 'active':
        color = '#dc3545';
        label = 'ATIVO';
        icon = <NotificationsActiveIcon />;
        break;
      case 'resolved':
        color = '#28a745';
        label = 'RESOLVIDO';
        icon = <CheckCircleIcon />;
        break;
      default:
        color = '#6c757d';
        label = 'INATIVO';
        icon = <InfoIcon />;
    }
    
    return (
      <Chip 
        icon={icon}
        label={label} 
        style={{ 
          backgroundColor: color, 
          color: '#fff'
        }}
        size="small"
      />
    );
  };
  
  // Renderizar detalhes de alerta
  const renderAlertDetails = () => {
    if (!selectedAlert) return null;
    
    return (
      <Dialog 
        open={selectedAlert !== null} 
        onClose={handleCloseAlertDetails}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Detalhes do Alerta
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">Nome</Typography>
              <Typography variant="body1" gutterBottom>{selectedAlert.name}</Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">Status</Typography>
              <Box mt={0.5} mb={1}>{renderStatusChip(selectedAlert.status)}</Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">Severidade</Typography>
              <Box mt={0.5} mb={1}>{renderSeverityChip(selectedAlert.severity)}</Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">ID</Typography>
              <Typography variant="body2" gutterBottom>{selectedAlert.id}</Typography>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2">Descrição</Typography>
              <Paper variant="outlined" style={{ padding: '10px', marginTop: '5px' }}>
                <Typography variant="body1">{selectedAlert.description}</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">Disparado em</Typography>
              <Typography variant="body1" gutterBottom>
                {selectedAlert.triggered_at ? new Date(selectedAlert.triggered_at).toLocaleString('pt-BR') : 'N/A'}
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">Resolvido em</Typography>
              <Typography variant="body1" gutterBottom>
                {selectedAlert.resolved_at ? new Date(selectedAlert.resolved_at).toLocaleString('pt-BR') : 'N/A'}
              </Typography>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          {selectedAlert.status === 'active' && (
            <Button 
              onClick={() => {
                resolveAlert(selectedAlert.id);
                handleCloseAlertDetails();
              }} 
              color="primary"
            >
              Resolver Alerta
            </Button>
          )}
          <Button onClick={handleCloseAlertDetails} color="primary">
            Fechar
          </Button>
        </DialogActions>
      </Dialog>
    );
  };
  
  // Renderizar diálogo de criação de alerta
  const renderCreateAlertDialog = () => {
    return (
      <Dialog 
        open={createAlertDialog} 
        onClose={handleCreateAlertClose}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Criar Novo Alerta
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Alerta</InputLabel>
                <Select value={alertType} onChange={handleAlertTypeChange} label="Tipo de Alerta">
                  <MenuItem value="threshold">Alerta de Limiar</MenuItem>
                  <MenuItem value="pattern">Alerta de Padrão</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {alertType === 'threshold' ? (
              // Formulário para alerta de limiar
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Nome"
                    value={thresholdName}
                    onChange={(e) => setThresholdName(e.target.value)}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Descrição"
                    value={thresholdDescription}
                    onChange={(e) => setThresholdDescription(e.target.value)}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Nome da Métrica"
                    value={metricName}
                    onChange={(e) => setMetricName(e.target.value)}
                    fullWidth
                    required
                    helperText="Ex: cpu_percent, memory_percent, log_error_rate"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Valor Limiar"
                    value={thresholdValue}
                    onChange={(e) => setThresholdValue(e.target.value)}
                    fullWidth
                    required
                    type="number"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Comparação</InputLabel>
                    <Select value={comparison} onChange={(e) => setComparison(e.target.value)} label="Comparação">
                      <MenuItem value="greater_than">Maior que</MenuItem>
                      <MenuItem value="greater_than_or_equal">Maior ou igual a</MenuItem>
                      <MenuItem value="less_than">Menor que</MenuItem>
                      <MenuItem value="less_than_or_equal">Menor ou igual a</MenuItem>
                      <MenuItem value="equal_to">Igual a</MenuItem>
                      <MenuItem value="not_equal_to">Diferente de</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Severidade</InputLabel>
                    <Select value={thresholdSeverity} onChange={(e) => setThresholdSeverity(e.target.value)} label="Severidade">
                      <MenuItem value="info">Info</MenuItem>
                      <MenuItem value="warning">Warning</MenuItem>
                      <MenuItem value="error">Error</MenuItem>
                      <MenuItem value="critical">Critical</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </>
            ) : (
              // Formulário para alerta de padrão
              <>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Nome"
                    value={patternName}
                    onChange={(e) => setPatternName(e.target.value)}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Descrição"
                    value={patternDescription}
                    onChange={(e) => setPatternDescription(e.target.value)}
                    fullWidth
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Padrão de Log"
                    value={logPattern}
                    onChange={(e) => setLogPattern(e.target.value)}
                    fullWidth
                    required
                    helperText="Texto a ser procurado nas mensagens de log"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Nível de Log (opcional)</InputLabel>
                    <Select value={logLevel} onChange={(e) => setLogLevel(e.target.value)} label="Nível de Log (opcional)">
                      <MenuItem value="">Qualquer</MenuItem>
                      <MenuItem value="debug">Debug</MenuItem>
                      <MenuItem value="info">Info</MenuItem>
                      <MenuItem value="warning">Warning</MenuItem>
                      <MenuItem value="error">Error</MenuItem>
                      <MenuItem value="critical">Critical</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Categoria de Log (opcional)</InputLabel>
                    <Select value={logCategory} onChange={(e) => setLogCategory(e.target.value)} label="Categoria de Log (opcional)">
                      <MenuItem value="">Qualquer</MenuItem>
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
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Severidade</InputLabel>
                    <Select value={patternSeverity} onChange={(e) => setPatternSeverity(e.target.value)} label="Severidade">
                      <MenuItem value="info">Info</MenuItem>
                      <MenuItem value="warning">Warning</MenuItem>
                      <MenuItem value="error">Error</MenuItem>
                      <MenuItem value="critical">Critical</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </>
            )}
            
            <Grid item xs={12}>
              <Divider style={{ margin: '10px 0' }} />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={autoResolve}
                    onChange={(e) => setAutoResolve(e.target.checked)}
                    color="primary"
                  />
                }
                label="Resolver automaticamente"
              />
            </Grid>
            
            {autoResolve && (
              <Grid item xs={12} md={6}>
                <TextField
                  label="Tempo para resolução (segundos)"
                  value={autoResolveAfter}
                  onChange={(e) => setAutoResolveAfter(e.target.value)}
                  fullWidth
                  type="number"
                  InputProps={{ inputProps: { min: 60 } }}
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCreateAlertClose} color="primary">
            Cancelar
          </Button>
          <Button onClick={handleCreateAlert} color="primary" variant="contained">
            Criar Alerta
          </Button>
        </DialogActions>
      </Dialog>
    );
  };
  
  // Renderizar tabela de alertas ativos
  const renderAlertsTable = () => {
    return (
      <Paper elevation={2} style={{ marginTop: 20 }}>
        <Box p={2} display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Alertas ({alerts.length})</Typography>
          <Box>
            <Tooltip title="Verificar Alertas">
              <IconButton onClick={checkAlerts} style={{ marginRight: 8 }}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Criar Alerta">
              <IconButton onClick={handleCreateAlertOpen} color="primary">
                <AddIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Nome</TableCell>
                <TableCell>Descrição</TableCell>
                <TableCell>Severidade</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Disparado em</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {alerts.length > 0 ? (
                alerts.map((alert) => (
                  <TableRow key={alert.id} hover>
                    <TableCell>{alert.name}</TableCell>
                    <TableCell>
                      {alert.description.length > 50 
                        ? `${alert.description.substring(0, 50)}...` 
                        : alert.description}
                    </TableCell>
                    <TableCell>{renderSeverityChip(alert.severity)}</TableCell>
                    <TableCell>{renderStatusChip(alert.status)}</TableCell>
                    <TableCell>
                      {alert.triggered_at 
                        ? new Date(alert.triggered_at).toLocaleString('pt-BR') 
                        : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Ver Detalhes">
                        <IconButton size="small" onClick={() => handleAlertClick(alert)}>
                          <InfoIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      {alert.status === 'active' && (
                        <Tooltip title="Resolver">
                          <IconButton size="small" onClick={() => resolveAlert(alert.id)}>
                            <CheckCircleIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Excluir">
                        <IconButton size="small" onClick={() => deleteAlert(alert.id)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    {loading ? 'Carregando...' : 'Nenhum alerta encontrado'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    );
  };
  
  // Renderizar tabela de histórico de alertas
  const renderAlertHistoryTable = () => {
    return (
      <Paper elevation={2} style={{ marginTop: 20 }}>
        <Box p={2} display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Histórico de Alertas ({alertHistory.length})</Typography>
          <Tooltip title={autoRefresh ? "Desativar Atualização Automática" : "Ativar Atualização Automática"}>
            <IconButton 
              onClick={handleAutoRefreshToggle}
              color={autoRefresh ? "primary" : "default"}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Nome</TableCell>
                <TableCell>Descrição</TableCell>
                <TableCell>Severidade</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Disparado em</TableCell>
                <TableCell>Resolvido em</TableCell>
                <TableCell>Ações</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {alertHistory.length > 0 ? (
                alertHistory.map((alert) => (
                  <TableRow key={alert.id} hover>
                    <TableCell>{alert.name}</TableCell>
                    <TableCell>
                      {alert.description.length > 40 
                        ? `${alert.description.substring(0, 40)}...` 
                        : alert.description}
                    </TableCell>
                    <TableCell>{renderSeverityChip(alert.severity)}</TableCell>
                    <TableCell>{renderStatusChip(alert.status)}</TableCell>
                    <TableCell>
                      {alert.triggered_at 
                        ? new Date(alert.triggered_at).toLocaleString('pt-BR') 
                        : 'N/A'}
                    </TableCell>
                    <TableCell>
                      {alert.resolved_at 
                        ? new Date(alert.resolved_at).toLocaleString('pt-BR') 
                        : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Ver Detalhes">
                        <IconButton size="small" onClick={() => handleAlertClick(alert)}>
                          <InfoIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    {historyLoading ? 'Carregando...' : 'Nenhum histórico de alerta encontrado'}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={alertHistory.length}
          page={page}
          onPageChange={handlePageChange}
          rowsPerPage={limit}
          onRowsPerPageChange={(e) => setLimit(parseInt(e.target.value))}
          rowsPerPageOptions={[10, 25, 50, 100]}
          labelRowsPerPage="Linhas por página:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} de ${count}`}
        />
      </Paper>
    );
  };
  
  return (
    <Container maxWidth="xl">
      <Typography variant="h4" gutterBottom style={{ marginTop: 20 }}>
        Alertas e Monitoramento
      </Typography>
      
      {/* Abas */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Button 
          variant={activeTab === 'active' ? 'contained' : 'text'} 
          onClick={() => handleTabChange('active')}
          sx={{ mr: 1 }}
        >
          Alertas Ativos
        </Button>
        <Button 
          variant={activeTab === 'history' ? 'contained' : 'text'} 
          onClick={() => handleTabChange('history')}
        >
          Histórico de Alertas
        </Button>
      </Box>
      
      {/* Filtros */}
      <Paper elevation={2} style={{ padding: 20, marginBottom: 20 }}>
        <Typography variant="h6" gutterBottom>Filtros</Typography>
        <Grid container spacing={2}>
          {activeTab === 'active' ? (
            <>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Status</InputLabel>
                  <Select value={statusFilter} onChange={handleStatusFilterChange} label="Status">
                    <MenuItem value="">Todos</MenuItem>
                    <MenuItem value="active">Ativos</MenuItem>
                    <MenuItem value="inactive">Inativos</MenuItem>
                    <MenuItem value="resolved">Resolvidos</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={fetchAlerts}
                  fullWidth
                  style={{ height: '100%' }}
                >
                  Buscar
                </Button>
              </Grid>
              <Grid item xs={12} md={4}>
                <Button 
                  variant="outlined" 
                  onClick={() => {
                    setStatusFilter('');
                    fetchAlerts();
                  }}
                  fullWidth
                  style={{ height: '100%' }}
                >
                  Limpar Filtros
                </Button>
              </Grid>
            </>
          ) : (
            <>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Severidade</InputLabel>
                  <Select value={severityFilter} onChange={handleSeverityFilterChange} label="Severidade">
                    <MenuItem value="">Todas</MenuItem>
                    <MenuItem value="info">Info</MenuItem>
                    <MenuItem value="warning">Warning</MenuItem>
                    <MenuItem value="error">Error</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Data Inicial"
                  type="date"
                  value={startDate}
                  onChange={handleStartDateChange}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  label="Data Final"
                  type="date"
                  value={endDate}
                  onChange={handleEndDateChange}
                  fullWidth
                  InputLabelProps={{ shrink: true }}
                />
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
              <Grid item xs={12} md={6}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={fetchAlertHistory}
                  fullWidth
                  style={{ height: '100%' }}
                >
                  Buscar
                </Button>
              </Grid>
              <Grid item xs={12} md={6}>
                <Button 
                  variant="outlined" 
                  onClick={() => {
                    setSeverityFilter('');
                    setStartDate('');
                    setEndDate('');
                    setLimit(50);
                    fetchAlertHistory();
                  }}
                  fullWidth
                  style={{ height: '100%' }}
                >
                  Limpar Filtros
                </Button>
              </Grid>
            </>
          )}
        </Grid>
      </Paper>
      
      {/* Mensagem de erro */}
      {error && (
        <Alert severity="error" style={{ marginBottom: 20 }}>
          {error}
        </Alert>
      )}
      
      {/* Tabelas */}
      {activeTab === 'active' ? renderAlertsTable() : renderAlertHistoryTable()}
      
      {/* Diálogos */}
      {renderAlertDetails()}
      {renderCreateAlertDialog()}
    </Container>
  );
};

export default AlertDashboard;

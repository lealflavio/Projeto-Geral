import React, { useState, useEffect } from 'react';
import { Card } from 'primereact/card';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { useRef } from 'react';
import { Tag } from 'primereact/tag';
import { ProgressSpinner } from 'primereact/progressspinner';
import { Dialog } from 'primereact/dialog';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import '../styles/variables.css';

const TaskMonitor = () => {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [selectedTask, setSelectedTask] = useState(null);
    const [showDialog, setShowDialog] = useState(false);
    const [refreshInterval, setRefreshInterval] = useState(null);
    const toast = useRef(null);
    const { token } = useAuth();

    useEffect(() => {
        loadTasks();
        
        // Configurar atualização automática a cada 30 segundos
        const interval = setInterval(() => {
            loadTasks(false);
        }, 30000);
        
        setRefreshInterval(interval);
        
        return () => {
            if (refreshInterval) {
                clearInterval(refreshInterval);
            }
        };
    }, []);

    const loadTasks = async (showLoading = true) => {
        if (showLoading) {
            setLoading(true);
        }
        
        try {
            const response = await axios.get(
                '/api/wondercom/tasks',
                {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            if (response.data.status === 'success') {
                setTasks(response.data.tasks || []);
            } else {
                throw new Error(response.data.message || 'Erro ao carregar tarefas');
            }
        } catch (error) {
            console.error('Erro ao carregar tarefas:', error);
            if (showLoading) {
                toast.current.show({
                    severity: 'error',
                    summary: 'Erro',
                    detail: error.response?.data?.message || 'Erro ao carregar tarefas',
                    life: 3000
                });
            }
        } finally {
            if (showLoading) {
                setLoading(false);
            }
        }
    };

    const handleRefresh = () => {
        loadTasks();
    };

    const handleViewDetails = (task) => {
        setSelectedTask(task);
        setShowDialog(true);
    };

    const statusTemplate = (rowData) => {
        const status = rowData.status;
        let severity = 'info';
        let label = 'Pendente';
        
        if (status === 'completed') {
            severity = 'success';
            label = 'Concluído';
        } else if (status === 'processing') {
            severity = 'warning';
            label = 'Processando';
        } else if (status === 'error') {
            severity = 'danger';
            label = 'Erro';
        } else if (status === 'pending') {
            severity = 'info';
            label = 'Pendente';
        }
        
        return <Tag severity={severity} value={label} />;
    };

    const typeTemplate = (rowData) => {
        const type = rowData.type;
        let label = 'Desconhecido';
        
        if (type === 'allocate_wo') {
            label = 'Alocação de WO';
        } else if (type === 'process_pdf') {
            label = 'Processamento de PDF';
        }
        
        return label;
    };

    const dateTemplate = (rowData) => {
        if (!rowData.created_at) return 'N/A';
        
        const date = new Date(rowData.created_at);
        return date.toLocaleString('pt-BR');
    };

    const actionsTemplate = (rowData) => {
        return (
            <div>
                <Button
                    icon="pi pi-eye"
                    className="p-button-rounded p-button-info p-button-sm"
                    onClick={() => handleViewDetails(rowData)}
                    tooltip="Ver detalhes"
                />
            </div>
        );
    };

    const renderTaskDetails = () => {
        if (!selectedTask) return null;
        
        return (
            <Dialog
                header="Detalhes da Tarefa"
                visible={showDialog}
                style={{ width: '50vw' }}
                onHide={() => setShowDialog(false)}
            >
                <div className="p-grid p-fluid">
                    <div className="p-col-12 p-md-6">
                        <h3>ID da Tarefa</h3>
                        <p>{selectedTask.job_id}</p>
                    </div>
                    <div className="p-col-12 p-md-6">
                        <h3>Tipo</h3>
                        <p>{typeTemplate(selectedTask)}</p>
                    </div>
                    <div className="p-col-12 p-md-6">
                        <h3>Status</h3>
                        <p>{statusTemplate(selectedTask)}</p>
                    </div>
                    <div className="p-col-12 p-md-6">
                        <h3>Data de Criação</h3>
                        <p>{dateTemplate(selectedTask)}</p>
                    </div>
                    
                    {selectedTask.result && (
                        <div className="p-col-12">
                            <h3>Resultado</h3>
                            <pre style={{ 
                                backgroundColor: 'var(--gray-100)', 
                                padding: '10px', 
                                borderRadius: '5px',
                                overflow: 'auto',
                                maxHeight: '300px'
                            }}>
                                {JSON.stringify(selectedTask.result, null, 2)}
                            </pre>
                        </div>
                    )}
                    
                    {selectedTask.error && (
                        <div className="p-col-12">
                            <h3>Erro</h3>
                            <p className="p-error">{selectedTask.error}</p>
                        </div>
                    )}
                </div>
            </Dialog>
        );
    };

    return (
        <div className="p-grid">
            <Toast ref={toast} />
            {renderTaskDetails()}
            <div className="p-col-12">
                <Card title="Monitor de Tarefas" className="p-shadow-4">
                    <div className="p-d-flex p-jc-end p-mb-3">
                        <Button
                            label="Atualizar"
                            icon="pi pi-refresh"
                            onClick={handleRefresh}
                            disabled={loading}
                        />
                    </div>
                    
                    {loading ? (
                        <div className="p-d-flex p-jc-center p-ai-center" style={{ height: '200px' }}>
                            <ProgressSpinner style={{ width: '50px', height: '50px' }} />
                        </div>
                    ) : (
                        <DataTable
                            value={tasks}
                            paginator
                            rows={10}
                            rowsPerPageOptions={[5, 10, 25]}
                            emptyMessage="Nenhuma tarefa encontrada"
                            responsiveLayout="scroll"
                        >
                            <Column field="job_id" header="ID da Tarefa" sortable />
                            <Column field="type" header="Tipo" body={typeTemplate} sortable />
                            <Column field="status" header="Status" body={statusTemplate} sortable />
                            <Column field="created_at" header="Data de Criação" body={dateTemplate} sortable />
                            <Column body={actionsTemplate} header="Ações" style={{ width: '100px' }} />
                        </DataTable>
                    )}
                </Card>
            </div>
        </div>
    );
};

export default TaskMonitor;

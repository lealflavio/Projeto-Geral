import React, { useState } from 'react';
import { Card } from 'primereact/card';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { useRef } from 'react';
import { Dialog } from 'primereact/dialog';
import { ProgressSpinner } from 'primereact/progressspinner';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import '../styles/variables.css';

const WorkOrderAllocation = () => {
    const [workOrderId, setWorkOrderId] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [showDialog, setShowDialog] = useState(false);
    const toast = useRef(null);
    const { token } = useAuth();

    const validateWorkOrderId = (id) => {
        // Verificar se tem 8 dígitos numéricos
        return /^\d{8}$/.test(id);
    };

    const handleAllocate = async () => {
        if (!validateWorkOrderId(workOrderId)) {
            toast.current.show({
                severity: 'error',
                summary: 'Erro',
                detail: 'O ID da ordem de trabalho deve ter 8 dígitos numéricos',
                life: 3000
            });
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(
                '/api/wondercom/allocate',
                { work_order_id: workOrderId },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            if (response.data.status === 'success') {
                setResult(response.data.data);
                setShowDialog(true);
                toast.current.show({
                    severity: 'success',
                    summary: 'Sucesso',
                    detail: 'Ordem de trabalho alocada com sucesso',
                    life: 3000
                });
            } else if (response.data.status === 'accepted') {
                toast.current.show({
                    severity: 'info',
                    summary: 'Processando',
                    detail: `Alocação em andamento. ID da tarefa: ${response.data.job_id}`,
                    life: 5000
                });
            } else {
                throw new Error(response.data.message || 'Erro ao alocar ordem de trabalho');
            }
        } catch (error) {
            console.error('Erro ao alocar WO:', error);
            toast.current.show({
                severity: 'error',
                summary: 'Erro',
                detail: error.response?.data?.message || 'Erro ao alocar ordem de trabalho',
                life: 3000
            });
        } finally {
            setLoading(false);
        }
    };

    const renderResultDialog = () => {
        if (!result) return null;

        return (
            <Dialog
                header="Detalhes da Ordem de Trabalho"
                visible={showDialog}
                style={{ width: '50vw' }}
                onHide={() => setShowDialog(false)}
            >
                <div className="p-grid p-fluid">
                    <div className="p-col-12 p-md-6">
                        <h3>Endereço</h3>
                        <p>{result.endereco || 'N/A'}</p>
                    </div>
                    <div className="p-col-12 p-md-6">
                        <h3>PDO</h3>
                        <p>{result.pdo || 'N/A'}</p>
                    </div>
                    <div className="p-col-12 p-md-6">
                        <h3>Cor da Fibra</h3>
                        <div className="p-d-flex p-ai-center">
                            <div
                                style={{
                                    width: '20px',
                                    height: '20px',
                                    backgroundColor: result.cor_fibra_hex || 'var(--gray-300)',
                                    marginRight: '10px',
                                    borderRadius: '50%'
                                }}
                            />
                            <span>{result.cor_fibra || 'N/A'}</span>
                        </div>
                    </div>
                    <div className="p-col-12">
                        <h3>Localização</h3>
                        <p>Latitude: {result.latitude || 'N/A'}</p>
                        <p>Longitude: {result.longitude || 'N/A'}</p>
                        {result.latitude && result.longitude && (
                            <Button
                                label="Ver no Google Maps"
                                icon="pi pi-map-marker"
                                className="p-button-outlined"
                                onClick={() => window.open(`https://www.google.com/maps?q=${result.latitude},${result.longitude}`, '_blank')}
                            />
                        )}
                    </div>
                </div>
            </Dialog>
        );
    };

    return (
        <div className="p-grid">
            <Toast ref={toast} />
            {renderResultDialog()}
            <div className="p-col-12">
                <Card title="Alocação de Ordem de Trabalho" className="p-shadow-4">
                    <div className="p-fluid">
                        <div className="p-field">
                            <label htmlFor="workOrderId">ID da Ordem de Trabalho</label>
                            <InputText
                                id="workOrderId"
                                value={workOrderId}
                                onChange={(e) => setWorkOrderId(e.target.value)}
                                placeholder="Digite o ID da ordem de trabalho (8 dígitos)"
                                keyfilter="pint" // Permite apenas números inteiros positivos
                                maxLength={8}
                                disabled={loading}
                            />
                            <small className="p-error">O ID deve conter 8 dígitos numéricos</small>
                        </div>
                        <Button
                            label="Alocar"
                            icon="pi pi-check"
                            className="p-mt-2"
                            onClick={handleAllocate}
                            disabled={loading || !workOrderId}
                        />
                        {loading && (
                            <div className="p-d-flex p-jc-center p-mt-3">
                                <ProgressSpinner style={{ width: '50px', height: '50px' }} />
                            </div>
                        )}
                    </div>
                </Card>
            </div>
        </div>
    );
};

export default WorkOrderAllocation;

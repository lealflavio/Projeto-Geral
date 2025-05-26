import React, { useState, useEffect } from 'react';
import { Card } from 'primereact/card';
import { Calendar } from 'primereact/calendar';
import { InputText } from 'primereact/inputtext';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { useRef } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
import { ProgressSpinner } from 'primereact/progressspinner';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const KilometersCalculator = () => {
    const [startDate, setStartDate] = useState(null);
    const [endDate, setEndDate] = useState(null);
    const [homeAddress, setHomeAddress] = useState('');
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const toast = useRef(null);
    const { token } = useAuth();

    // Definir datas padrão (mês atual)
    useEffect(() => {
        const now = new Date();
        const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
        const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        
        setStartDate(firstDay);
        setEndDate(lastDay);
    }, []);

    const handleCalculate = async () => {
        if (!startDate || !endDate) {
            toast.current.show({
                severity: 'error',
                summary: 'Erro',
                detail: 'Selecione as datas de início e fim',
                life: 3000
            });
            return;
        }

        if (endDate < startDate) {
            toast.current.show({
                severity: 'error',
                summary: 'Erro',
                detail: 'A data final deve ser posterior à data inicial',
                life: 3000
            });
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(
                '/api/wondercom/calcular-kms',
                {
                    data_inicio: startDate.toISOString().split('T')[0],
                    data_fim: endDate.toISOString().split('T')[0],
                    endereco_residencial: homeAddress || null
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    }
                }
            );

            if (response.data.status === 'success') {
                setResult(response.data);
                toast.current.show({
                    severity: 'success',
                    summary: 'Sucesso',
                    detail: 'Cálculo de KMs realizado com sucesso',
                    life: 3000
                });
            } else {
                throw new Error(response.data.message || 'Erro ao calcular KMs');
            }
        } catch (error) {
            console.error('Erro ao calcular KMs:', error);
            toast.current.show({
                severity: 'error',
                summary: 'Erro',
                detail: error.response?.data?.message || 'Erro ao calcular KMs',
                life: 3000
            });
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'EUR'
        }).format(value);
    };

    const distanceTemplate = (rowData) => {
        return `${rowData.distancia.toFixed(1)} km`;
    };

    const renderResult = () => {
        if (!result) return null;

        const reimbursementRate = 0.36; // €/km
        const totalReimbursement = result.total_km * reimbursementRate;

        return (
            <div className="p-mt-4">
                <Card title="Resultado do Cálculo" className="p-shadow-4">
                    <div className="p-grid">
                        <div className="p-col-12 p-md-6">
                            <h3>Total de KMs percorridos</h3>
                            <p className="p-text-bold p-text-xl">{result.total_km.toFixed(1)} km</p>
                        </div>
                        <div className="p-col-12 p-md-6">
                            <h3>Valor a receber (€0,36/km)</h3>
                            <p className="p-text-bold p-text-xl">{formatCurrency(totalReimbursement)}</p>
                        </div>
                    </div>

                    <h3>Detalhes do Percurso</h3>
                    <DataTable value={result.detalhes} responsiveLayout="scroll">
                        <Column field="origem" header="Origem" />
                        <Column field="destino" header="Destino" />
                        <Column field="distancia" header="Distância" body={distanceTemplate} />
                    </DataTable>
                </Card>
            </div>
        );
    };

    return (
        <div className="p-grid">
            <Toast ref={toast} />
            <div className="p-col-12">
                <Card title="Calculadora de KMs" className="p-shadow-4">
                    <div className="p-fluid p-formgrid p-grid">
                        <div className="p-field p-col-12 p-md-6">
                            <label htmlFor="startDate">Data Inicial</label>
                            <Calendar
                                id="startDate"
                                value={startDate}
                                onChange={(e) => setStartDate(e.value)}
                                showIcon
                                dateFormat="dd/mm/yy"
                                disabled={loading}
                            />
                        </div>
                        <div className="p-field p-col-12 p-md-6">
                            <label htmlFor="endDate">Data Final</label>
                            <Calendar
                                id="endDate"
                                value={endDate}
                                onChange={(e) => setEndDate(e.value)}
                                showIcon
                                dateFormat="dd/mm/yy"
                                disabled={loading}
                            />
                        </div>
                        <div className="p-field p-col-12">
                            <label htmlFor="homeAddress">Endereço Residencial (opcional)</label>
                            <InputText
                                id="homeAddress"
                                value={homeAddress}
                                onChange={(e) => setHomeAddress(e.target.value)}
                                placeholder="Digite seu endereço residencial para cálculo completo"
                                disabled={loading}
                            />
                            <small>Informe seu endereço para calcular o trajeto completo (casa-trabalho-casa)</small>
                        </div>
                        <div className="p-col-12">
                            <Button
                                label="Calcular KMs"
                                icon="pi pi-calculator"
                                onClick={handleCalculate}
                                disabled={loading || !startDate || !endDate}
                            />
                        </div>
                        {loading && (
                            <div className="p-col-12 p-d-flex p-jc-center p-mt-3">
                                <ProgressSpinner style={{ width: '50px', height: '50px' }} />
                            </div>
                        )}
                    </div>
                </Card>
            </div>
            {renderResult()}
        </div>
    );
};

export default KilometersCalculator;

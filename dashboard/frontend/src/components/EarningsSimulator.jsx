import React from 'react';
import { Card } from 'primereact/card';
import { InputText } from 'primereact/inputtext';
import { InputNumber } from 'primereact/inputnumber';
import { Dropdown } from 'primereact/dropdown';
import { Button } from 'primereact/button';
import { Toast } from 'primereact/toast';
import { useRef, useState } from 'react';
import { Chart } from 'primereact/chart';

const EarningsSimulator = () => {
    const toast = useRef(null);
    const [workOrders, setWorkOrders] = useState(0);
    const [serviceType, setServiceType] = useState(null);
    const [kilometers, setKilometers] = useState(0);
    const [result, setResult] = useState(null);

    const serviceTypes = [
        { label: 'Instalação FTTH', value: 'ftth_install', price: 25 },
        { label: 'Reparação FTTH', value: 'ftth_repair', price: 20 },
        { label: 'Instalação ADSL', value: 'adsl_install', price: 18 },
        { label: 'Reparação ADSL', value: 'adsl_repair', price: 15 },
        { label: 'Manutenção Preventiva', value: 'preventive', price: 22 }
    ];

    const handleCalculate = () => {
        if (!serviceType) {
            toast.current.show({
                severity: 'error',
                summary: 'Erro',
                detail: 'Selecione um tipo de serviço',
                life: 3000
            });
            return;
        }

        if (workOrders <= 0) {
            toast.current.show({
                severity: 'error',
                summary: 'Erro',
                detail: 'O número de ordens de trabalho deve ser maior que zero',
                life: 3000
            });
            return;
        }

        // Calcular ganhos
        const servicePrice = serviceType.price;
        const serviceTotal = servicePrice * workOrders;
        
        // Calcular reembolso de KMs (€0.36/km)
        const kmRate = 0.36;
        const kmTotal = kilometers * kmRate;
        
        // Total geral
        const grandTotal = serviceTotal + kmTotal;
        
        // Dados para o gráfico
        const chartData = {
            labels: ['Serviços', 'Quilômetros'],
            datasets: [
                {
                    data: [serviceTotal, kmTotal],
                    backgroundColor: ['#42A5F5', '#66BB6A'],
                    hoverBackgroundColor: ['#64B5F6', '#81C784']
                }
            ]
        };
        
        const chartOptions = {
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        };
        
        setResult({
            serviceTotal,
            kmTotal,
            grandTotal,
            chartData,
            chartOptions
        });
        
        toast.current.show({
            severity: 'success',
            summary: 'Sucesso',
            detail: 'Simulação calculada com sucesso',
            life: 3000
        });
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'EUR'
        }).format(value);
    };

    const renderResult = () => {
        if (!result) return null;

        return (
            <div className="p-mt-4">
                <Card title="Resultado da Simulação" className="p-shadow-4">
                    <div className="p-grid">
                        <div className="p-col-12 p-md-4">
                            <h3>Ganhos com Serviços</h3>
                            <p className="p-text-bold p-text-xl">{formatCurrency(result.serviceTotal)}</p>
                            <p>{workOrders} ordens x {formatCurrency(serviceType.price)}</p>
                        </div>
                        <div className="p-col-12 p-md-4">
                            <h3>Reembolso de KMs</h3>
                            <p className="p-text-bold p-text-xl">{formatCurrency(result.kmTotal)}</p>
                            <p>{kilometers} km x €0,36</p>
                        </div>
                        <div className="p-col-12 p-md-4">
                            <h3>Total Geral</h3>
                            <p className="p-text-bold p-text-xl">{formatCurrency(result.grandTotal)}</p>
                        </div>
                    </div>
                    
                    <div className="p-mt-4">
                        <h3>Distribuição de Ganhos</h3>
                        <Chart type="pie" data={result.chartData} options={result.chartOptions} style={{ maxHeight: '300px' }} />
                    </div>
                </Card>
            </div>
        );
    };

    return (
        <div className="p-grid">
            <Toast ref={toast} />
            <div className="p-col-12">
                <Card title="Simulador de Ganhos" className="p-shadow-4">
                    <div className="p-fluid p-formgrid p-grid">
                        <div className="p-field p-col-12 p-md-6">
                            <label htmlFor="serviceType">Tipo de Serviço</label>
                            <Dropdown
                                id="serviceType"
                                value={serviceType}
                                options={serviceTypes}
                                onChange={(e) => setServiceType(e.value)}
                                placeholder="Selecione o tipo de serviço"
                            />
                        </div>
                        <div className="p-field p-col-12 p-md-6">
                            <label htmlFor="workOrders">Número de Ordens de Trabalho</label>
                            <InputNumber
                                id="workOrders"
                                value={workOrders}
                                onValueChange={(e) => setWorkOrders(e.value)}
                                min={0}
                                showButtons
                                buttonLayout="horizontal"
                                decrementButtonClassName="p-button-danger"
                                incrementButtonClassName="p-button-success"
                                incrementButtonIcon="pi pi-plus"
                                decrementButtonIcon="pi pi-minus"
                            />
                        </div>
                        <div className="p-field p-col-12">
                            <label htmlFor="kilometers">Quilômetros Percorridos</label>
                            <InputNumber
                                id="kilometers"
                                value={kilometers}
                                onValueChange={(e) => setKilometers(e.value)}
                                min={0}
                                suffix=" km"
                                showButtons
                                buttonLayout="horizontal"
                                decrementButtonClassName="p-button-danger"
                                incrementButtonClassName="p-button-success"
                                incrementButtonIcon="pi pi-plus"
                                decrementButtonIcon="pi pi-minus"
                            />
                        </div>
                        <div className="p-col-12">
                            <Button
                                label="Calcular Ganhos"
                                icon="pi pi-calculator"
                                onClick={handleCalculate}
                                disabled={!serviceType}
                            />
                        </div>
                    </div>
                </Card>
            </div>
            {renderResult()}
        </div>
    );
};

export default EarningsSimulator;

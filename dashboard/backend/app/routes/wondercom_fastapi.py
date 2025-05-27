from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import re
import logging
from typing import Dict, Any, Optional

from ..services.vm_api import VMApiClient
from ..services.notification import NotificationService
from ..models.user import User
from ..models.work_order import WorkOrder
from ..auth import get_current_user

# Configurar logging
logger = logging.getLogger(__name__)

# Criar router - Removendo o prefixo da rota para que o FastAPI não duplique
router = APIRouter(tags=["Wondercom"])

# Modificando o caminho da rota para não incluir o prefixo /api/wondercom
@router.post("/wondercom/allocate")
async def allocate_work_order(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para alocação de ordem de trabalho no portal Wondercom.
    """
    if not current_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if not current_user.usuario_portal or not current_user.senha_portal:
        raise HTTPException(status_code=400, detail="Configuração com portal não configurada")
    
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Dados ausentes ou inválidos")
    
    if not data:
        raise HTTPException(status_code=400, detail="Dados ausentes")
    
    work_order_id = data.get('work_order_id')
    
    if not work_order_id:
        raise HTTPException(status_code=400, detail="ID da ordem de trabalho ausente")
    
    # Validar formato do work_order_id (8 dígitos numéricos)
    if not re.match(r'^\d{8}$', work_order_id):
        raise HTTPException(status_code=400, detail="ID da ordem de trabalho deve ter 8 dígitos numéricos")
    
    # Preparar credenciais
    credentials = {
        "username": current_user.usuario_portal,
        "password": current_user.senha_portal
    }
    
    try:
        # Chamar a VM API
        vm_api_client = VMApiClient()
        result = vm_api_client.allocate_work_order(work_order_id, credentials)
        
        # Se processamento síncrono, enviar notificação
        if result.get('status') == 'success' and current_user.whatsapp:
            notification_service = NotificationService()
            
            # Preparar mensagem com dados da WO
            wo_data = result.get('data', {})
            message = f"Detalhes da WO {work_order_id}:\n"
            message += f"Endereço: {wo_data.get('endereco', 'N/A')}\n"
            message += f"PDO: {wo_data.get('pdo', 'N/A')}\n"
            message += f"Cor da Fibra: {wo_data.get('cor_fibra', 'N/A')}\n"
            message += f"Coordenadas: {wo_data.get('latitude', 'N/A')}, {wo_data.get('longitude', 'N/A')}"
            
            # Enviar notificação
            notification_service.send_whatsapp_notification(current_user.whatsapp, message)
        
        return result
    except Exception as e:
        logger.error(f"Erro ao alocar WO {work_order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wondercom/calcular-kms")
async def calcular_kms(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para cálculo de KMs percorridos.
    """
    if not current_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Dados ausentes ou inválidos")
    
    if not data:
        raise HTTPException(status_code=400, detail="Dados ausentes")
    
    data_inicio = data.get('data_inicio')
    data_fim = data.get('data_fim')
    endereco_residencial = data.get('endereco_residencial')
    
    if not data_inicio or not data_fim:
        raise HTTPException(status_code=400, detail="Datas de início e fim são obrigatórias")
    
    try:
        # Buscar WOs do período
        work_orders = WorkOrder.query.filter(
            WorkOrder.tecnico_id == current_user.id,
            WorkOrder.data >= data_inicio,
            WorkOrder.data <= data_fim,
            WorkOrder.status == 'processado'
        ).all()
        
        if not work_orders:
            return {
                "status": "success",
                "total_km": 0,
                "detalhes": []
            }
        
        # Extrair coordenadas
        coordenadas = []
        
        # Adicionar endereço residencial se fornecido
        if endereco_residencial:
            # Aqui você precisaria implementar a geocodificação do endereço
            # usando Google Maps API ou similar
            # coords_casa = geocode_address(endereco_residencial)
            # if coords_casa:
            #     coordenadas.append(coords_casa)
            pass
        
        # Adicionar coordenadas das WOs
        for wo in work_orders:
            # Extrair coordenadas do resultado da WO
            # resultado = json.loads(wo.resultado)
            # lat = resultado.get('latitude')
            # lng = resultado.get('longitude')
            # if lat and lng:
            #     coordenadas.append({"lat": lat, "lng": lng})
            pass
        
        # Adicionar endereço residencial no final se fornecido
        if endereco_residencial and len(coordenadas) > 0:
            coordenadas.append(coordenadas[0])
        
        # Calcular distâncias
        # Aqui você precisaria implementar o cálculo de distâncias
        # usando Google Maps API ou similar
        # distancias = calculate_distances(coordenadas)
        
        # Para fins de exemplo, vamos simular um resultado
        distancias = [10.5, 15.2, 8.7, 12.3]
        total_km = sum(distancias)
        
        detalhes = [
            {"origem": i, "destino": i+1, "distancia": dist}
            for i, dist in enumerate(distancias)
        ]
        
        return {
            "status": "success",
            "total_km": total_km,
            "detalhes": detalhes
        }
    except Exception as e:
        logger.error(f"Erro ao calcular KMs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

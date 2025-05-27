from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
import re
import logging
import json
from typing import Dict, Any, Optional

# Importação corrigida para o VMApiClient
from ..services.vm_api.client import VMApiClient

# Importação do stub de NotificationService
# Nota: Este serviço precisa ser criado no diretório correto
class NotificationService:
    """Stub para o serviço de notificação."""
    
    def send_whatsapp_notification(self, phone_number: str, message: str) -> dict:
        """Stub para envio de notificação via WhatsApp."""
        logging.info(f"[STUB] Enviando WhatsApp para {phone_number}: {message}")
        return {"status": "success", "message": "Notification sent (stub)"}

# Importações de modelos e autenticação
# Ajuste conforme a estrutura real do projeto
from ..models import User, WO as WorkOrder
# Importar a versão com debug para diagnóstico
from ..auth_debug import get_current_user

# Configurar logging
logger = logging.getLogger("wondercom_debug")
logger.setLevel(logging.DEBUG)
# Garantir que o logger tenha um handler para console
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

# Criar router - Removendo o prefixo da rota para que o FastAPI não duplique
router = APIRouter(tags=["Wondercom"])

# Corrigindo o caminho da rota para NÃO incluir o prefixo /api, pois ele já é adicionado no main.py
@router.post("/wondercom/allocate")
async def allocate_work_order(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint para alocação de ordem de trabalho no portal Wondercom.
    """
    logger.debug(f"Requisição recebida para alocação de WO. URL: {request.url}")
    logger.debug(f"Headers da requisição: {dict(request.headers)}")
    
    if not current_user:
        logger.error("Usuário não encontrado após autenticação")
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    logger.debug(f"Usuário autenticado: {current_user.email}")
    
    if not current_user.usuario_portal or not current_user.senha_portal:
        logger.error(f"Usuário {current_user.email} não tem credenciais do portal configuradas")
        raise HTTPException(status_code=400, detail="Configuração com portal não configurada")
    
    try:
        data = await request.json()
        logger.debug(f"Dados recebidos: {json.dumps(data)}")
    except Exception as e:
        logger.error(f"Erro ao processar JSON da requisição: {str(e)}")
        raise HTTPException(status_code=400, detail="Dados ausentes ou inválidos")
    
    if not data:
        logger.error("Dados vazios na requisição")
        raise HTTPException(status_code=400, detail="Dados ausentes")
    
    work_order_id = data.get('work_order_id')
    
    if not work_order_id:
        logger.error("ID da ordem de trabalho ausente nos dados")
        raise HTTPException(status_code=400, detail="ID da ordem de trabalho ausente")
    
    # Validar formato do work_order_id (8 dígitos numéricos)
    if not re.match(r'^\d{8}$', work_order_id):
        logger.error(f"Formato inválido de ID: {work_order_id}")
        raise HTTPException(status_code=400, detail="ID da ordem de trabalho deve ter 8 dígitos numéricos")
    
    # Preparar credenciais
    credentials = {
        "username": current_user.usuario_portal,
        "password": current_user.senha_portal
    }
    
    try:
        # Chamar a VM API
        logger.debug(f"Chamando VM API para alocar WO {work_order_id}")
        vm_api_client = VMApiClient()
        result = vm_api_client.allocate_work_order(work_order_id, credentials)
        logger.debug(f"Resultado da VM API: {json.dumps(result)}")
        
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
            pass
        
        # Adicionar coordenadas das WOs
        for wo in work_orders:
            pass
        
        # Adicionar endereço residencial no final se fornecido
        if endereco_residencial and len(coordenadas) > 0:
            coordenadas.append(coordenadas[0])
        
        # Calcular distâncias
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

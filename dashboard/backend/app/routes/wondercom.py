"""
Rotas para integração com o Portal Wondercom.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
import json
#from ..services.portal_automation.wondercom_client import WondercomClient
from app.services.portal_automation.wondercom_client import WondercomClient
from ..auth import get_current_active_user
from .. import models
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    prefix="/api/wondercom",
    tags=["wondercom"],
    responses={404: {"description": "Not found"}},
)

# Configurações do Portal Wondercom
CHROME_DRIVER_PATH = "/home/flavioleal_souza/Downloads/chromedriver"
PORTAL_URL = "https://portal.wondercom.pt/group/guest/intervencoes"

# Modelos de dados
class WorkOrderRequest(BaseModel):
    work_order_id: str

class WorkOrderResponse(BaseModel):
    success: bool
    message: str
    dados: Optional[Dict[str, Any]] = None

# Cache simples para armazenar resultados de WOs consultadas
# Em produção, usar Redis ou outro mecanismo de cache mais robusto
wo_cache = {}

@router.post("/allocate", response_model=WorkOrderResponse)
async def allocate_work_order(
    request: WorkOrderRequest, 
    background_tasks: BackgroundTasks,
    # Remova temporariamente a dependência do usuário logado para diagnóstico
    # current_user: models.User = Depends(get_current_active_user),
    # db: Session = Depends(get_db)
):
    """
    Aloca uma ordem de trabalho no Portal Wondercom usando credenciais fixas (temporário para diagnóstico).
    """
    work_order_id = request.work_order_id
    
    print(f"Tentando alocar WO: {work_order_id}")  # Log adicional
    
    # Verifica se a WO já está em cache
    if work_order_id in wo_cache:
        print(f"WO {work_order_id} encontrada em cache.")  # Log adicional
        return WorkOrderResponse(
            success=True,
            message=f"WO {work_order_id} encontrada em cache.",
            dados=wo_cache[work_order_id]
        )
    
    try:
        # Use credenciais fixas temporariamente para diagnóstico
        print("Inicializando cliente Wondercom com credenciais fixas")  # Log adicional
        with WondercomClient(
            chrome_driver_path=CHROME_DRIVER_PATH,
            portal_url=PORTAL_URL,
            username="flavio.leal",  # Substitua pelo seu usuário real
            password="MFH8fQgAa4"    # Substitua pela sua senha real
        ) as client:
            print("Cliente Wondercom inicializado")  # Log adicional
            
            # Realiza login
            print("Tentando realizar login no portal")  # Log adicional
            login_success = client.login()
            print(f"Resultado do login: {login_success}")  # Log adicional
            
            if not login_success:
                print("Falha ao realizar login no Portal Wondercom")  # Log adicional
                raise HTTPException(status_code=500, detail="Falha ao realizar login no Portal Wondercom.")
            
            # Aloca a WO
            print(f"Login bem-sucedido. Tentando alocar WO: {work_order_id}")  # Log adicional
            result = client.allocate_work_order(work_order_id)
            print(f"Resultado da alocação: {result}")  # Log adicional
            
            # Se a alocação foi bem-sucedida, armazena os dados em cache
            if result["success"] and "dados" in result:
                print(f"Alocação bem-sucedida. Armazenando em cache.")  # Log adicional
                wo_cache[work_order_id] = result["dados"]
                
                # Comentado temporariamente para diagnóstico
                # try:
                #     new_wo = models.WO(
                #         numero_wo=work_order_id,
                #         tecnico_id=current_user.id,
                #         status=result["dados"].get("estado", "ALLOCATED"),
                #         tipo_servico=result["dados"].get("tipo_servico", "desconhecido")
                #     )
                #     db.add(new_wo)
                #     db.commit()
                # except Exception as db_error:
                #     # Não falha a operação se o registro no banco falhar
                #     print(f"Erro ao registrar WO no banco: {str(db_error)}")
            
            return WorkOrderResponse(
                success=result["success"],
                message=result["message"],
                dados=result.get("dados")
            )
    except Exception as e:
        print(f"Erro ao alocar WO: {str(e)}")  # Log adicional
        import traceback
        print(traceback.format_exc())  # Log detalhado do erro
        raise HTTPException(status_code=500, detail=f"Erro ao alocar WO: {str(e)}")

@router.get("/details/{work_order_id}", response_model=WorkOrderResponse)
async def get_work_order_details(
    work_order_id: str,
    # Remova temporariamente a dependência do usuário logado para diagnóstico
    # current_user: models.User = Depends(get_current_active_user)
):
    """
    Obtém detalhes de uma ordem de trabalho do Portal Wondercom.
    """
    print(f"Tentando obter detalhes da WO: {work_order_id}")  # Log adicional
    
    # Verifica se a WO já está em cache
    if work_order_id in wo_cache:
        print(f"WO {work_order_id} encontrada em cache.")  # Log adicional
        return WorkOrderResponse(
            success=True,
            message=f"WO {work_order_id} encontrada em cache.",
            dados=wo_cache[work_order_id]
        )
    
    try:
        # Use credenciais fixas temporariamente para diagnóstico
        print("Inicializando cliente Wondercom com credenciais fixas")  # Log adicional
        with WondercomClient(
            chrome_driver_path=CHROME_DRIVER_PATH,
            portal_url=PORTAL_URL,
            username="flavio.leal",  # Substitua pelo seu usuário real
            password="MFH8fQgAa4"    # Substitua pela sua senha real
        ) as client:
            print("Cliente Wondercom inicializado")  # Log adicional
            
            # Realiza login
            print("Tentando realizar login no portal")  # Log adicional
            login_success = client.login()
            print(f"Resultado do login: {login_success}")  # Log adicional
            
            if not login_success:
                print("Falha ao realizar login no Portal Wondercom")  # Log adicional
                raise HTTPException(status_code=500, detail="Falha ao realizar login no Portal Wondercom.")
            
            # Pesquisa a WO
            print(f"Login bem-sucedido. Tentando pesquisar WO: {work_order_id}")  # Log adicional
            dados_wo = client.search_work_order(work_order_id)
            print(f"Resultado da pesquisa: {dados_wo}")  # Log adicional
            
            if not dados_wo:
                print(f"WO {work_order_id} não encontrada.")  # Log adicional
                return WorkOrderResponse(
                    success=False,
                    message=f"WO {work_order_id} não encontrada.",
                    dados=None
                )
            
            # Armazena os dados em cache
            print(f"Pesquisa bem-sucedida. Armazenando em cache.")  # Log adicional
            wo_cache[work_order_id] = dados_wo
            
            return WorkOrderResponse(
                success=True,
                message=f"Detalhes da WO {work_order_id} obtidos com sucesso.",
                dados=dados_wo
            )
    except Exception as e:
        print(f"Erro ao obter detalhes da WO: {str(e)}")  # Log adicional
        import traceback
        print(traceback.format_exc())  # Log detalhado do erro
        raise HTTPException(status_code=500, detail=f"Erro ao obter detalhes da WO: {str(e)}")

@router.delete("/cache/{work_order_id}")
async def clear_work_order_cache(work_order_id: str):
    """
    Limpa o cache de uma ordem de trabalho específica.
    """
    print(f"Tentando limpar cache da WO: {work_order_id}")  # Log adicional
    if work_order_id in wo_cache:
        del wo_cache[work_order_id]
        print(f"Cache da WO {work_order_id} limpo com sucesso.")  # Log adicional
        return {"message": f"Cache da WO {work_order_id} limpo com sucesso."}
    print(f"WO {work_order_id} não encontrada em cache.")  # Log adicional
    return {"message": f"WO {work_order_id} não encontrada em cache."}

@router.delete("/cache")
async def clear_all_cache():
    """
    Limpa todo o cache de ordens de trabalho.
    """
    print("Tentando limpar todo o cache de WOs.")  # Log adicional
    count = len(wo_cache)
    wo_cache.clear()
    print(f"Cache de todas as WOs limpo com sucesso. {count} entradas removidas.")  # Log adicional
    return {"message": f"Cache de todas as WOs limpo com sucesso. {count} entradas removidas."}

# Rota de teste para verificar se a API está funcionando
@router.get("/test")
async def test_api():
    """
    Rota de teste para verificar se a API está funcionando.
    """
    print("Rota de teste acessada com sucesso.")  # Log adicional
    return {"message": "API Wondercom está funcionando corretamente!"}

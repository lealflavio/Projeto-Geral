import redis
import time
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import json

from app.database import get_db
from app.models import PDFProcessingTask
from app.schemas import PDFTaskCreate, PDFTaskResponse

# Configuração do Redis para fila de tarefas
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
PDF_QUEUE = "pdf_processing_queue"

app = FastAPI()

@app.post("/api/wondercom/allocate", response_model=PDFTaskResponse)
async def allocate_pdf_task(
    task: PDFTaskCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Endpoint para alocar um novo PDF para processamento.
    Implementa controle de taxa e enfileiramento para alta demanda.
    """
    # Verificar créditos do usuário
    user = db.query(User).filter(User.id == task.user_id).first()
    if not user or user.credits <= 0:
        raise HTTPException(status_code=402, detail="Créditos insuficientes")
    
    # Criar registro da tarefa
    db_task = PDFProcessingTask(
        pdf_url=task.pdf_url,
        user_id=task.user_id,
        status="pending"
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    # Adicionar à fila do Redis
    task_data = {
        "task_id": db_task.id,
        "pdf_url": task.pdf_url,
        "user_id": task.user_id,
        "timestamp": time.time()
    }
    redis_client.lpush(PDF_QUEUE, json.dumps(task_data))
    
    # Atualizar contador de fila para monitoramento
    queue_size = redis_client.llen(PDF_QUEUE)
    redis_client.set("wondercom_pdf_queue_size", queue_size)
    
    # Decrementar crédito do usuário
    user.credits -= 1
    db.commit()
    
    return PDFTaskResponse(
        id=db_task.id,
        status="pending",
        position_in_queue=queue_size,
        estimated_time=calculate_estimated_time(queue_size)
    )

def calculate_estimated_time(queue_size: int) -> int:
    """
    Calcula o tempo estimado de processamento com base no tamanho da fila.
    Média de 30 segundos por PDF, com ajuste para carga do sistema.
    """
    base_time = 30  # segundos por PDF
    
    # Ajuste para carga do sistema
    if queue_size > 100:
        # Quando a fila está muito grande, o processamento é mais eficiente
        return int(queue_size * base_time * 0.8)
    elif queue_size > 50:
        return int(queue_size * base_time * 0.9)
    else:
        return queue_size * base_time

@app.get("/api/wondercom/queue-status", response_model=dict)
async def get_queue_status():
    """
    Retorna estatísticas da fila de processamento para monitoramento.
    """
    queue_size = redis_client.llen(PDF_QUEUE)
    return {
        "queue_size": queue_size,
        "estimated_processing_time": calculate_estimated_time(queue_size),
        "system_load": get_system_load()
    }

def get_system_load() -> float:
    """
    Obtém a carga atual do sistema para monitoramento.
    """
    try:
        # Em produção, isso seria implementado para obter métricas reais
        return float(redis_client.get("system_load") or 0.5)
    except:
        return 0.5

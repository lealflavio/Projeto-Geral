#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_orquestrador_pdfs.py
Testes unitários para o sistema de filas de processamento de PDFs.

Este módulo implementa testes unitários para validar o funcionamento do sistema
de filas, mecanismos de retry e fallback, e integração com o backend.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import time
import unittest
import tempfile
import shutil
import threading
from unittest.mock import patch, MagicMock

from M2_Orquestrador_PDFs import PDFTask, PDFQueue, TaskStatus, BackendIntegration, PDFProcessor

class TestPDFTask(unittest.TestCase):
    """Testes para a classe PDFTask."""
    
    def test_task_creation(self):
        """Testa a criação de uma tarefa."""
        pdf_path = "/caminho/para/arquivo.pdf"
        task = PDFTask(pdf_path, priority=1)
        
        self.assertEqual(task.pdf_path, pdf_path)
        self.assertEqual(task.priority, 1)
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.attempts, 0)
        self.assertEqual(task.max_attempts, 3)
        self.assertIsNone(task.result)
        self.assertIsNone(task.error)
    
    def test_task_comparison(self):
        """Testa a comparação de tarefas por prioridade."""
        task1 = PDFTask("arquivo1.pdf", priority=1)
        task2 = PDFTask("arquivo2.pdf", priority=2)
        task3 = PDFTask("arquivo3.pdf", priority=0)
        
        self.assertLess(task1, task2)  # 1 < 2
        self.assertLess(task3, task1)  # 0 < 1
        self.assertLess(task3, task2)  # 0 < 2
    
    def test_task_serialization(self):
        """Testa a serialização e desserialização de tarefas."""
        task = PDFTask("arquivo.pdf", priority=1)
        task_dict = task.to_dict()
        
        # Verifica se todos os campos estão presentes
        self.assertIn("task_id", task_dict)
        self.assertIn("pdf_path", task_dict)
        self.assertIn("priority", task_dict)
        self.assertIn("status", task_dict)
        self.assertIn("attempts", task_dict)
        self.assertIn("created_at", task_dict)
        self.assertIn("updated_at", task_dict)
        self.assertIn("result", task_dict)
        self.assertIn("error", task_dict)
        
        # Recria a tarefa a partir do dicionário
        task2 = PDFTask.from_dict(task_dict)
        
        # Verifica se os campos foram preservados
        self.assertEqual(task2.pdf_path, task.pdf_path)
        self.assertEqual(task2.priority, task.priority)
        self.assertEqual(task2.status, task.status)
        self.assertEqual(task2.attempts, task.attempts)
        self.assertEqual(task2.task_id, task.task_id)

class TestPDFQueue(unittest.TestCase):
    """Testes para a classe PDFQueue."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Cria um diretório temporário para os PDFs de teste
        self.test_dir = tempfile.mkdtemp()
        
        # Cria alguns arquivos PDF de teste
        self.pdf_files = []
        for i in range(5):
            pdf_path = os.path.join(self.test_dir, f"test_{i}.pdf")
            with open(pdf_path, "w") as f:
                f.write(f"Conteúdo de teste para PDF {i}")
            self.pdf_files.append(pdf_path)
        
        # Inicializa a fila
        self.queue = PDFQueue(max_workers=2, max_queue_size=10)
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Remove o diretório temporário
        shutil.rmtree(self.test_dir)
        
        # Para o processamento da fila
        if hasattr(self, "queue") and self.queue.running:
            self.queue.stop_processing()
    
    def test_enqueue_dequeue(self):
        """Testa o enfileiramento e desenfileiramento de tarefas."""
        # Enfileira um PDF
        task_id = self.queue.enqueue(self.pdf_files[0], priority=1)
        
        # Verifica se o ID da tarefa foi retornado
        self.assertIsNotNone(task_id)
        
        # Verifica se as estatísticas foram atualizadas
        self.assertEqual(self.queue.stats["enqueued"], 1)
        
        # Desenfileira a tarefa
        task = self.queue.dequeue()
        
        # Verifica se a tarefa foi retornada corretamente
        self.assertIsNotNone(task)
        self.assertEqual(task.pdf_path, self.pdf_files[0])
        self.assertEqual(task.priority, 1)
        self.assertEqual(task.status, TaskStatus.PROCESSING)
        
        # Verifica se a tarefa está na lista de processamento
        self.assertIn(task.task_id, self.queue.processing_tasks)
    
    def test_priority_ordering(self):
        """Testa a ordenação de tarefas por prioridade."""
        # Enfileira PDFs com diferentes prioridades
        task_id1 = self.queue.enqueue(self.pdf_files[0], priority=2)
        task_id2 = self.queue.enqueue(self.pdf_files[1], priority=0)  # Maior prioridade
        task_id3 = self.queue.enqueue(self.pdf_files[2], priority=1)
        
        # Desenfileira as tarefas e verifica a ordem
        task1 = self.queue.dequeue()
        self.assertEqual(task1.pdf_path, self.pdf_files[1])  # Prioridade 0
        
        task2 = self.queue.dequeue()
        self.assertEqual(task2.pdf_path, self.pdf_files[2])  # Prioridade 1
        
        task3 = self.queue.dequeue()
        self.assertEqual(task3.pdf_path, self.pdf_files[0])  # Prioridade 2
    
    def test_mark_completed(self):
        """Testa a marcação de tarefas como concluídas."""
        # Enfileira e desenfileira um PDF
        task_id = self.queue.enqueue(self.pdf_files[0])
        task = self.queue.dequeue()
        
        # Marca como concluída
        result = {"status": "success", "data": {"id": 123}}
        self.queue.mark_completed(task.task_id, result)
        
        # Verifica se a tarefa foi movida para a lista de concluídas
        self.assertNotIn(task.task_id, self.queue.processing_tasks)
        self.assertIn(task.task_id, self.queue.completed_tasks)
        
        # Verifica se o resultado foi armazenado
        completed_task = self.queue.completed_tasks[task.task_id]
        self.assertEqual(completed_task.result, result)
        self.assertEqual(completed_task.status, TaskStatus.COMPLETED)
        
        # Verifica se as estatísticas foram atualizadas
        self.assertEqual(self.queue.stats["completed"], 1)
        self.assertEqual(self.queue.stats["processed"], 1)
    
    def test_mark_failed_with_retry(self):
        """Testa a marcação de tarefas como falhas com retry."""
        # Enfileira e desenfileira um PDF
        task_id = self.queue.enqueue(self.pdf_files[0])
        task = self.queue.dequeue()
        
        # Marca como falha com retry
        error = "Erro de teste"
        self.queue.mark_failed(task.task_id, error, retry=True)
        
        # Verifica se a tarefa não está mais na lista de processamento
        self.assertNotIn(task.task_id, self.queue.processing_tasks)
        
        # Verifica se as estatísticas foram atualizadas
        self.assertEqual(self.queue.stats["retried"], 1)
        self.assertEqual(self.queue.stats["processed"], 1)
        
        # Desenfileira novamente e verifica se é a mesma tarefa
        task2 = self.queue.dequeue()
        self.assertEqual(task2.task_id, task.task_id)
        self.assertEqual(task2.attempts, 1)
        self.assertEqual(task2.error, error)
        self.assertEqual(task2.status, TaskStatus.PROCESSING)
    
    def test_mark_failed_without_retry(self):
        """Testa a marcação de tarefas como falhas sem retry."""
        # Enfileira e desenfileira um PDF
        task_id = self.queue.enqueue(self.pdf_files[0])
        task = self.queue.dequeue()
        
        # Marca como falha sem retry
        error = "Erro fatal"
        self.queue.mark_failed(task.task_id, error, retry=False)
        
        # Verifica se a tarefa foi movida para a lista de falhas
        self.assertNotIn(task.task_id, self.queue.processing_tasks)
        self.assertIn(task.task_id, self.queue.failed_tasks)
        
        # Verifica se o erro foi armazenado
        failed_task = self.queue.failed_tasks[task.task_id]
        self.assertEqual(failed_task.error, error)
        self.assertEqual(failed_task.status, TaskStatus.FAILED)
        
        # Verifica se as estatísticas foram atualizadas
        self.assertEqual(self.queue.stats["failed"], 1)
        self.assertEqual(self.queue.stats["processed"], 1)
        self.assertEqual(self.queue.stats["retried"], 0)
    
    def test_max_retry_attempts(self):
        """Testa o limite máximo de tentativas de retry."""
        # Enfileira um PDF
        task_id = self.queue.enqueue(self.pdf_files[0])
        
        # Simula falhas repetidas
        for i in range(3):  # max_attempts é 3
            task = self.queue.dequeue()
            self.assertEqual(task.attempts, i)
            self.queue.mark_failed(task.task_id, f"Erro {i}", retry=True)
        
        # Na terceira falha, a tarefa deve ir para a dead letter queue
        self.assertEqual(len(self.queue.dead_letter_queue), 1)
        self.assertIn(task_id, self.queue.dead_letter_queue)
        
        # Verifica se as estatísticas foram atualizadas corretamente
        self.assertEqual(self.queue.stats["retried"], 2)  # Apenas 2 retries
        self.assertEqual(self.queue.stats["failed"], 1)
        self.assertEqual(self.queue.stats["processed"], 3)
    
    def test_get_task_status(self):
        """Testa a obtenção do status de uma tarefa."""
        # Enfileira um PDF
        task_id = self.queue.enqueue(self.pdf_files[0])
        
        # Verifica o status na fila
        status = self.queue.get_task_status(task_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["status"], "pending")
        
        # Desenfileira a tarefa
        task = self.queue.dequeue()
        
        # Verifica o status em processamento
        status = self.queue.get_task_status(task.task_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["status"], "processing")
        
        # Marca como concluída
        self.queue.mark_completed(task.task_id, {"result": "ok"})
        
        # Verifica o status concluído
        status = self.queue.get_task_status(task.task_id)
        self.assertIsNotNone(status)
        self.assertEqual(status["status"], "completed")
    
    def test_get_queue_status(self):
        """Testa a obtenção do status da fila."""
        # Enfileira alguns PDFs
        for i in range(3):
            self.queue.enqueue(self.pdf_files[i], priority=i)
        
        # Verifica o status inicial da fila
        status = self.queue.get_queue_status()
        self.assertEqual(status["queue_size"], 3)
        self.assertEqual(status["processing"], 0)
        self.assertEqual(status["completed"], 0)
        self.assertEqual(status["failed"], 0)
        self.assertEqual(status["stats"]["enqueued"], 3)
        
        # Desenfileira uma tarefa
        task = self.queue.dequeue()
        
        # Verifica o status após desenfileirar
        status = self.queue.get_queue_status()
        self.assertEqual(status["queue_size"], 2)
        self.assertEqual(status["processing"], 1)
        
        # Marca como concluída
        self.queue.mark_completed(task.task_id)
        
        # Verifica o status após concluir
        status = self.queue.get_queue_status()
        self.assertEqual(status["queue_size"], 2)
        self.assertEqual(status["processing"], 0)
        self.assertEqual(status["completed"], 1)
        self.assertEqual(status["stats"]["completed"], 1)
    
    def test_continuous_processing(self):
        """Testa o processamento contínuo da fila."""
        # Define uma função de processamento simulada
        def process_pdf(pdf_path):
            time.sleep(0.1)  # Simula processamento
            return {"result": "success", "pdf": pdf_path}
        
        # Enfileira alguns PDFs
        for i in range(3):
            self.queue.enqueue(self.pdf_files[i])
        
        # Inicia o processamento
        self.queue.start_processing(process_pdf)
        
        # Aguarda o processamento
        time.sleep(1)
        
        # Verifica se todas as tarefas foram processadas
        status = self.queue.get_queue_status()
        self.assertEqual(status["queue_size"], 0)
        self.assertEqual(status["processing"], 0)
        self.assertEqual(status["completed"], 3)
        self.assertEqual(status["stats"]["completed"], 3)
        
        # Para o processamento
        self.queue.stop_processing()

class TestBackendIntegration(unittest.TestCase):
    """Testes para a classe BackendIntegration."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        self.backend = BackendIntegration("https://api.exemplo.com")
    
    @patch("requests.post")
    def test_send_data(self, mock_post):
        """Testa o envio de dados para o backend."""
        # Configura o mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "id": 123}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Envia dados
        data = {"key": "value"}
        response = self.backend.send_data("endpoint", data)
        
        # Verifica se a requisição foi feita corretamente
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["json"], data)
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        self.assertEqual(kwargs["timeout"], 10)
        
        # Verifica a resposta
        self.assertEqual(response, {"status": "success", "id": 123})
    
    @patch("requests.get")
    def test_get_data(self, mock_get):
        """Testa a obtenção de dados do backend."""
        # Configura o mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "success", "data": [1, 2, 3]}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Obtém dados
        params = {"param": "value"}
        response = self.backend.get_data("endpoint", params)
        
        # Verifica se a requisição foi feita corretamente
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs["params"], params)
        self.assertEqual(kwargs["headers"]["Accept"], "application/json")
        self.assertEqual(kwargs["timeout"], 10)
        
        # Verifica a resposta
        self.assertEqual(response, {"status": "success", "data": [1, 2, 3]})

class TestPDFProcessor(unittest.TestCase):
    """Testes para a classe PDFProcessor."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Cria diretórios temporários
        self.test_dir = tempfile.mkdtemp()
        self.input_dir = os.path.join(self.test_dir, "input")
        self.output_dir = os.path.join(self.test_dir, "output")
        self.error_dir = os.path.join(self.test_dir, "error")
        
        os.makedirs(self.input_dir, exist_ok=True)
        
        # Cria alguns arquivos PDF de teste
        self.pdf_files = []
        for i in range(3):
            pdf_path = os.path.join(self.input_dir, f"test_{i}.pdf")
            with open(pdf_path, "w") as f:
                f.write(f"Conteúdo de teste para PDF {i}")
            self.pdf_files.append(pdf_path)
        
        # Inicializa o processador com mocks
        self.backend_url = "https://api.exemplo.com"
        self.processor = PDFProcessor(self.backend_url, self.output_dir, self.error_dir)
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Remove o diretório temporário
        shutil.rmtree(self.test_dir)
        
        # Para o processamento
        if hasattr(self, "processor"):
            self.processor.stop()
    
    @patch.object(BackendIntegration, "send_data")
    def test_process_pdf(self, mock_send_data):
        """Testa o processamento de um PDF."""
        # Configura o mock
        mock_send_data.return_value = {"status": "success", "id": 123}
        
        # Processa um PDF
        result = self.processor.process_pdf(self.pdf_files[0])
        
        # Verifica se os dados foram enviados para o backend
        mock_send_data.assert_called_once()
        args, kwargs = mock_send_data.call_args
        self.assertEqual(args[0], "api/wondercom/allocate")
        self.assertIn("pdf_data", args[1])
        self.assertIn("pdf_name", args[1])
        
        # Verifica se o PDF foi movido para o diretório de saída
        output_path = os.path.join(self.output_dir, os.path.basename(self.pdf_files[0]))
        self.assertTrue(os.path.exists(output_path))
        
        # Verifica o resultado
        self.assertTrue(result["success"])
        self.assertIn("pdf_data", result)
        self.assertIn("backend_response", result)
        self.assertEqual(result["output_path"], output_path)
    
    @patch.object(BackendIntegration, "send_data")
    def test_process_pdf_error(self, mock_send_data):
        """Testa o processamento de um PDF com erro."""
        # Configura o mock para lançar exceção
        mock_send_data.side_effect = Exception("Erro de teste")
        
        # Processa um PDF e espera exceção
        with self.assertRaises(Exception):
            self.processor.process_pdf(self.pdf_files[0])
        
        # Verifica se o PDF foi movido para o diretório de erro
        error_path = os.path.join(self.error_dir, os.path.basename(self.pdf_files[0]))
        self.assertTrue(os.path.exists(error_path))
    
    @patch.object(PDFProcessor, "process_pdf")
    def test_add_pdf(self, mock_process_pdf):
        """Testa a adição de um PDF para processamento."""
        # Adiciona um PDF
        task_id = self.processor.add_pdf(self.pdf_files[0], priority=1)
        
        # Verifica se o ID da tarefa foi retornado
        self.assertIsNotNone(task_id)
        
        # Verifica o status da fila
        status = self.processor.queue.get_queue_status()
        self.assertEqual(status["stats"]["enqueued"], 1)
    
    @patch.object(PDFProcessor, "process_pdf")
    def test_start_stop(self, mock_process_pdf):
        """Testa o início e parada do processamento."""
        # Configura o mock
        mock_process_pdf.return_value = {"success": True}
        
        # Adiciona alguns PDFs
        for pdf in self.pdf_files:
            self.processor.add_pdf(pdf)
        
        # Inicia o processamento
        self.processor.start()
        
        # Verifica se o processamento foi iniciado
        self.assertTrue(self.processor.queue.running)
        
        # Aguarda um pouco para o processamento
        time.sleep(0.5)
        
        # Para o processamento
        self.processor.stop()
        
        # Verifica se o processamento foi parado
        self.assertFalse(self.processor.queue.running)

if __name__ == "__main__":
    unittest.main()

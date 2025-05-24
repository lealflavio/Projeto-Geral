#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_notificacao_status.py
Testes unitários para o sistema de notificação e monitoramento de status.

Este módulo implementa testes unitários para validar o funcionamento do sistema
de notificações via WhatsApp com mecanismos de retry, fallback e monitoramento de status.

Autor: Agente 3 - Especialista em Automação Selenium #2
Data: 24/05/2025
"""

import os
import json
import unittest
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock

from M6_Notificacao_Status import (
    StatusMonitor,
    enviar_mensagem_whatsapp,
    _enviar_fallback,
    enviar_notificacao_boas_vindas,
    enviar_notificacao_wo_iniciada,
    enviar_notificacao_wo_sucesso,
    enviar_notificacao_wo_erro,
    obter_status_wo,
    enviar_notificacao_status_atual,
    gerar_relatorio_status
)

class TestStatusMonitor(unittest.TestCase):
    """Testes para a classe StatusMonitor."""
    
    def setUp(self):
        """Configuração inicial para os testes."""
        # Cria um diretório temporário para os testes
        self.test_dir = tempfile.mkdtemp()
        self.monitor = StatusMonitor(storage_path=self.test_dir)
    
    def tearDown(self):
        """Limpeza após os testes."""
        # Remove o diretório temporário
        shutil.rmtree(self.test_dir)
    
    def test_registrar_evento(self):
        """Testa o registro de eventos."""
        # Registra um evento
        resultado = self.monitor.registrar_evento(
            numero_wo="WO123",
            tipo_evento="inicio",
            detalhes={"chave": "valor"},
            tecnico="Técnico Teste"
        )
        
        # Verifica se o registro foi bem-sucedido
        self.assertTrue(resultado)
        
        # Verifica se o diretório da WO foi criado
        wo_dir = os.path.join(self.test_dir, "WO123")
        self.assertTrue(os.path.exists(wo_dir))
        
        # Verifica se o arquivo de evento foi criado
        arquivos = os.listdir(wo_dir)
        self.assertEqual(len(arquivos), 1)
        self.assertTrue(arquivos[0].endswith("_inicio.json"))
        
        # Verifica o conteúdo do arquivo
        with open(os.path.join(wo_dir, arquivos[0]), "r") as f:
            evento = json.load(f)
            self.assertEqual(evento["numero_wo"], "WO123")
            self.assertEqual(evento["tipo_evento"], "inicio")
            self.assertEqual(evento["tecnico"], "Técnico Teste")
            self.assertEqual(evento["detalhes"], {"chave": "valor"})
    
    def test_obter_historico_wo(self):
        """Testa a obtenção do histórico de eventos de uma WO."""
        # Registra múltiplos eventos
        self.monitor.registrar_evento("WO123", "inicio", tecnico="Técnico Teste")
        self.monitor.registrar_evento("WO123", "sucesso")
        
        # Obtém o histórico
        historico = self.monitor.obter_historico_wo("WO123")
        
        # Verifica se o histórico foi obtido corretamente
        self.assertEqual(len(historico), 2)
        self.assertEqual(historico[0]["tipo_evento"], "inicio")
        self.assertEqual(historico[1]["tipo_evento"], "sucesso")
    
    def test_obter_status_atual(self):
        """Testa a obtenção do status atual de uma WO."""
        # Registra múltiplos eventos
        self.monitor.registrar_evento("WO123", "inicio")
        self.monitor.registrar_evento("WO123", "sucesso")
        
        # Obtém o status atual
        status = self.monitor.obter_status_atual("WO123")
        
        # Verifica se o status atual é o último evento
        self.assertEqual(status["tipo_evento"], "sucesso")
    
    def test_gerar_relatorio_status(self):
        """Testa a geração de relatório de status."""
        # Registra eventos para múltiplas WOs
        self.monitor.registrar_evento("WO123", "inicio", tecnico="Técnico A")
        self.monitor.registrar_evento("WO123", "sucesso", tecnico="Técnico A")
        self.monitor.registrar_evento("WO456", "inicio", tecnico="Técnico B")
        self.monitor.registrar_evento("WO456", "erro", tecnico="Técnico B")
        self.monitor.registrar_evento("WO789", "inicio", tecnico="Técnico A")
        
        # Gera o relatório
        relatorio = self.monitor.gerar_relatorio_status()
        
        # Verifica o relatório
        self.assertEqual(relatorio["total_wos"], 3)
        self.assertEqual(relatorio["wos_sucesso"], 1)
        self.assertEqual(relatorio["wos_erro"], 1)
        self.assertEqual(relatorio["wos_pendentes"], 1)
        
        # Verifica detalhes por WO
        self.assertEqual(relatorio["detalhes_por_wo"]["WO123"]["status_atual"], "sucesso")
        self.assertEqual(relatorio["detalhes_por_wo"]["WO456"]["status_atual"], "erro")
        self.assertEqual(relatorio["detalhes_por_wo"]["WO789"]["status_atual"], "inicio")
        
        # Testa filtro por técnico
        relatorio_tecnico_a = self.monitor.gerar_relatorio_status(tecnico="Técnico A")
        self.assertEqual(relatorio_tecnico_a["total_wos"], 2)
        self.assertIn("WO123", relatorio_tecnico_a["detalhes_por_wo"])
        self.assertIn("WO789", relatorio_tecnico_a["detalhes_por_wo"])
        self.assertNotIn("WO456", relatorio_tecnico_a["detalhes_por_wo"])

class TestEnvioMensagens(unittest.TestCase):
    """Testes para as funções de envio de mensagens."""
    
    @patch("M6_Notificacao_Status.client")
    def test_enviar_mensagem_whatsapp(self, mock_client):
        """Testa o envio de mensagem via WhatsApp."""
        # Configura o mock
        mock_message = MagicMock()
        mock_message.sid = "SM123"
        mock_client.messages.create.return_value = mock_message
        
        # Envia a mensagem
        resultado = enviar_mensagem_whatsapp(
            "+5511999999999",
            "Teste de mensagem",
            tipo_log="teste",
            numero_wo="WO123"
        )
        
        # Verifica se a mensagem foi enviada corretamente
        mock_client.messages.create.assert_called_once()
        self.assertTrue(resultado["success"])
        self.assertEqual(resultado["message_sid"], "SM123")
    
    @patch("M6_Notificacao_Status.client")
    @patch("M6_Notificacao_Status._enviar_fallback")
    def test_enviar_mensagem_whatsapp_com_retry(self, mock_fallback, mock_client):
        """Testa o retry no envio de mensagem via WhatsApp."""
        # Configura o mock para lançar exceção e depois sucesso
        from twilio.base.exceptions import TwilioRestException
        mock_client.messages.create.side_effect = [
            TwilioRestException(400, "url", "Erro de teste"),
            MagicMock(sid="SM123")
        ]
        
        # Envia a mensagem
        resultado = enviar_mensagem_whatsapp(
            "+5511999999999",
            "Teste de mensagem"
        )
        
        # Verifica se houve retry e sucesso
        self.assertEqual(mock_client.messages.create.call_count, 2)
        self.assertFalse(mock_fallback.called)
        self.assertTrue(resultado["success"])
    
    @patch("M6_Notificacao_Status.requests")
    @patch("M6_Notificacao_Status.FALLBACK_WEBHOOK_URL", "https://exemplo.com/webhook")
    def test_enviar_fallback(self, mock_requests):
        """Testa o envio de mensagem por fallback."""
        # Configura o mock para o webhook
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response
        
        # Envia a mensagem por fallback
        resultado = _enviar_fallback(
            "+5511999999999",
            "Teste de mensagem",
            tipo_log="teste",
            numero_wo="WO123"
        )
        
        # Verifica se o webhook foi chamado
        mock_requests.post.assert_called_once()
        
        # Verifica o resultado
        self.assertTrue(resultado["success"])
        self.assertTrue(resultado["fallback"])
        self.assertIn("webhook", resultado["methods"])

class TestNotificacoes(unittest.TestCase):
    """Testes para as funções de notificação."""
    
    @patch("M6_Notificacao_Status.enviar_mensagem_whatsapp")
    def test_enviar_notificacao_boas_vindas(self, mock_enviar):
        """Testa o envio de notificação de boas-vindas."""
        # Configura o mock
        mock_enviar.return_value = {"success": True}
        
        # Envia a notificação
        resultado = enviar_notificacao_boas_vindas(
            "+5511999999999",
            "Técnico Teste"
        )
        
        # Verifica se a notificação foi enviada corretamente
        mock_enviar.assert_called_once()
        args = mock_enviar.call_args[0]
        self.assertEqual(args[0], "+5511999999999")
        self.assertIn("Técnico Teste", args[1])
        self.assertEqual(mock_enviar.call_args[1]["tipo_log"], "boas-vindas")
        self.assertTrue(resultado["success"])
    
    @patch("M6_Notificacao_Status.enviar_mensagem_whatsapp")
    @patch("M6_Notificacao_Status.StatusMonitor")
    def test_enviar_notificacao_wo_iniciada(self, mock_monitor, mock_enviar):
        """Testa o envio de notificação de início de WO."""
        # Configura os mocks
        mock_enviar.return_value = {"success": True}
        mock_monitor_instance = MagicMock()
        mock_monitor.return_value = mock_monitor_instance
        
        # Dados de teste
        dados_intervencao = {
            "tipo_intervencao": "Instalação",
            "data_inicio": "2025-05-24",
            "hora_inicio": "10:00",
            "equipamentos_entregues": ["Equipamento 1", "Equipamento 2"],
            "materiais_usados": ["Material 1", "Material 2"]
        }
        
        # Envia a notificação
        resultado = enviar_notificacao_wo_iniciada(
            "+5511999999999",
            "Técnico Teste",
            "WO123",
            dados_intervencao
        )
        
        # Verifica se a notificação foi enviada corretamente
        mock_enviar.assert_called_once()
        args = mock_enviar.call_args[0]
        self.assertEqual(args[0], "+5511999999999")
        self.assertIn("WO123", args[1])
        self.assertEqual(mock_enviar.call_args[1]["tipo_log"], "início")
        self.assertEqual(mock_enviar.call_args[1]["numero_wo"], "WO123")
        
        # Verifica se o evento foi registrado no monitor
        mock_monitor_instance.registrar_evento.assert_called_once()
        args = mock_monitor_instance.registrar_evento.call_args[1]
        self.assertEqual(args["numero_wo"], "WO123")
        self.assertEqual(args["tipo_evento"], "inicio")
        self.assertEqual(args["tecnico"], "Técnico Teste")
        self.assertEqual(args["detalhes"], dados_intervencao)
        
        self.assertTrue(resultado["success"])
    
    @patch("M6_Notificacao_Status.enviar_mensagem_whatsapp")
    @patch("M6_Notificacao_Status.StatusMonitor")
    def test_enviar_notificacao_wo_sucesso(self, mock_monitor, mock_enviar):
        """Testa o envio de notificação de sucesso de WO."""
        # Configura os mocks
        mock_enviar.return_value = {"success": True}
        mock_monitor_instance = MagicMock()
        mock_monitor.return_value = mock_monitor_instance
        
        # Envia a notificação
        resultado = enviar_notificacao_wo_sucesso(
            "+5511999999999",
            "WO123"
        )
        
        # Verifica se a notificação foi enviada corretamente
        mock_enviar.assert_called_once()
        args = mock_enviar.call_args[0]
        self.assertEqual(args[0], "+5511999999999")
        self.assertIn("WO123", args[1])
        self.assertEqual(mock_enviar.call_args[1]["tipo_log"], "sucesso")
        self.assertEqual(mock_enviar.call_args[1]["numero_wo"], "WO123")
        
        # Verifica se o evento foi registrado no monitor
        mock_monitor_instance.registrar_evento.assert_called_once()
        args = mock_monitor_instance.registrar_evento.call_args[1]
        self.assertEqual(args["numero_wo"], "WO123")
        self.assertEqual(args["tipo_evento"], "sucesso")
        
        self.assertTrue(resultado["success"])
    
    @patch("M6_Notificacao_Status.enviar_mensagem_whatsapp")
    @patch("M6_Notificacao_Status.StatusMonitor")
    def test_enviar_notificacao_wo_erro(self, mock_monitor, mock_enviar):
        """Testa o envio de notificação de erro de WO."""
        # Configura os mocks
        mock_enviar.return_value = {"success": True}
        mock_monitor_instance = MagicMock()
        mock_monitor.return_value = mock_monitor_instance
        
        # Envia a notificação
        resultado = enviar_notificacao_wo_erro(
            "+5511999999999",
            "WO123"
        )
        
        # Verifica se a notificação foi enviada corretamente
        mock_enviar.assert_called_once()
        args = mock_enviar.call_args[0]
        self.assertEqual(args[0], "+5511999999999")
        self.assertIn("WO123", args[1])
        self.assertEqual(mock_enviar.call_args[1]["tipo_log"], "erro")
        self.assertEqual(mock_enviar.call_args[1]["numero_wo"], "WO123")
        
        # Verifica se o evento foi registrado no monitor
        mock_monitor_instance.registrar_evento.assert_called_once()
        args = mock_monitor_instance.registrar_evento.call_args[1]
        self.assertEqual(args["numero_wo"], "WO123")
        self.assertEqual(args["tipo_evento"], "erro")
        
        self.assertTrue(resultado["success"])
    
    @patch("M6_Notificacao_Status.StatusMonitor")
    def test_obter_status_wo(self, mock_monitor):
        """Testa a obtenção do status de uma WO."""
        # Configura o mock
        mock_monitor_instance = MagicMock()
        mock_monitor.return_value = mock_monitor_instance
        mock_monitor_instance.obter_status_atual.return_value = {
            "numero_wo": "WO123",
            "tipo_evento": "sucesso",
            "timestamp": datetime.now().isoformat()
        }
        
        # Obtém o status
        status = obter_status_wo("WO123")
        
        # Verifica se o status foi obtido corretamente
        mock_monitor_instance.obter_status_atual.assert_called_once_with("WO123")
        self.assertEqual(status["numero_wo"], "WO123")
        self.assertEqual(status["tipo_evento"], "sucesso")
    
    @patch("M6_Notificacao_Status.obter_status_wo")
    @patch("M6_Notificacao_Status.enviar_mensagem_whatsapp")
    def test_enviar_notificacao_status_atual(self, mock_enviar, mock_obter_status):
        """Testa o envio de notificação de status atual."""
        # Configura os mocks
        mock_enviar.return_value = {"success": True}
        mock_obter_status.return_value = {
            "numero_wo": "WO123",
            "tipo_evento": "sucesso",
            "timestamp": datetime.now().isoformat()
        }
        
        # Envia a notificação
        resultado = enviar_notificacao_status_atual(
            "+5511999999999",
            "WO123"
        )
        
        # Verifica se a notificação foi enviada corretamente
        mock_obter_status.assert_called_once_with("WO123")
        mock_enviar.assert_called_once()
        args = mock_enviar.call_args[0]
        self.assertEqual(args[0], "+5511999999999")
        self.assertIn("WO123", args[1])
        self.assertEqual(mock_enviar.call_args[1]["tipo_log"], "status")
        self.assertEqual(mock_enviar.call_args[1]["numero_wo"], "WO123")
        
        self.assertTrue(resultado["success"])
    
    @patch("M6_Notificacao_Status.StatusMonitor")
    def test_gerar_relatorio_status(self, mock_monitor):
        """Testa a geração de relatório de status."""
        # Configura o mock
        mock_monitor_instance = MagicMock()
        mock_monitor.return_value = mock_monitor_instance
        mock_monitor_instance.gerar_relatorio_status.return_value = {
            "total_wos": 3,
            "wos_sucesso": 2,
            "wos_erro": 1,
            "wos_pendentes": 0,
            "detalhes_por_wo": {
                "WO123": {"status_atual": "sucesso"},
                "WO456": {"status_atual": "sucesso"},
                "WO789": {"status_atual": "erro"}
            }
        }
        
        # Gera o relatório
        relatorio = gerar_relatorio_status(
            data_inicio="2025-05-01",
            data_fim="2025-05-31",
            tecnico="Técnico Teste"
        )
        
        # Verifica se o relatório foi gerado corretamente
        mock_monitor_instance.gerar_relatorio_status.assert_called_once_with(
            "2025-05-01", "2025-05-31", "Técnico Teste"
        )
        self.assertEqual(relatorio["total_wos"], 3)
        self.assertEqual(relatorio["wos_sucesso"], 2)
        self.assertEqual(relatorio["wos_erro"], 1)
        self.assertEqual(relatorio["wos_pendentes"], 0)

if __name__ == "__main__":
    unittest.main()

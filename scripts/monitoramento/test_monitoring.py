#!/usr/bin/env python3
"""
Testes automatizados para scripts de monitoramento

Este script executa testes automatizados para verificar o funcionamento
dos scripts de monitoramento e manutenção.

Uso:
    python3 test_monitoring.py
"""

import os
import sys
import unittest
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Adicionar diretório raiz ao path para importação
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos a serem testados
try:
    from monitoramento.notifications import (
        mask_sensitive_data,
        send_email_notification,
        send_whatsapp_notification,
        send_webhook_notification,
        send_notification
    )
except ImportError:
    print("AVISO: Módulo de notificações não encontrado.")

class TestNotifications(unittest.TestCase):
    """Testes para o módulo de notificações"""
    
    def test_mask_sensitive_data(self):
        """Testa a função de mascaramento de dados sensíveis"""
        # Testar mascaramento de senhas
        text = "A senha é password=123456 e o token é token=abcdef"
        masked = mask_sensitive_data(text)
        self.assertIn("password=********", masked)
        self.assertIn("token=********", masked)
        self.assertNotIn("123456", masked)
        self.assertNotIn("abcdef", masked)
        
        # Testar mascaramento com diferentes formatos
        text = "Credenciais: senha: 987654, api_key: xyz123"
        masked = mask_sensitive_data(text)
        self.assertIn("senha: ********", masked)
        self.assertIn("api_key: ********", masked)
        self.assertNotIn("987654", masked)
        self.assertNotIn("xyz123", masked)
    
    @patch('monitoramento.notifications.smtplib.SMTP')
    def test_send_email_notification(self, mock_smtp):
        """Testa o envio de notificações por email"""
        # Configurar mock
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server
        
        # Testar com configurações simuladas
        with patch('monitoramento.notifications.get_config') as mock_config:
            # Simular configurações habilitadas
            mock_config.side_effect = lambda key, default: {
                'notifications.email.enabled': True,
                'notifications.email.smtp_server': 'smtp.test.com',
                'notifications.email.smtp_port': 587,
                'notifications.email.username': 'test@example.com',
                'notifications.email.password': 'password123',
                'notifications.email.recipients': ['admin@example.com']
            }.get(key, default)
            
            # Testar envio
            result = send_email_notification("Teste", "Mensagem de teste")
            
            # Verificar se o email foi enviado corretamente
            self.assertTrue(result)
            mock_smtp.assert_called_once_with('smtp.test.com', 587)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with('test@example.com', 'password123')
            mock_server.send_message.assert_called_once()
            mock_server.quit.assert_called_once()
    
    @patch('monitoramento.notifications.requests.post')
    def test_send_webhook_notification(self, mock_post):
        """Testa o envio de notificações por webhook"""
        # Configurar mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Testar com configurações simuladas
        with patch('monitoramento.notifications.get_config') as mock_config:
            # Simular configurações habilitadas
            mock_config.side_effect = lambda key, default: {
                'notifications.webhook.enabled': True,
                'notifications.webhook.url': 'https://hooks.test.com/webhook',
                'notifications.webhook.method': 'POST',
                'notifications.webhook.headers': {'Content-Type': 'application/json'}
            }.get(key, default)
            
            # Testar envio
            result = send_webhook_notification("Teste", "Mensagem de teste")
            
            # Verificar se o webhook foi enviado corretamente
            self.assertTrue(result)
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], 'https://hooks.test.com/webhook')
            self.assertEqual(kwargs['headers'], {'Content-Type': 'application/json'})
            self.assertIn('title', kwargs['json'])
            self.assertIn('message', kwargs['json'])
            self.assertIn('timestamp', kwargs['json'])

class TestSystemHealth(unittest.TestCase):
    """Testes para o script de verificação de saúde do sistema"""
    
    @patch('requests.get')
    def test_verificar_backend(self, mock_get):
        """Testa a verificação do backend"""
        # Importar função a ser testada
        try:
            from monitoramento.system_health import verificar_backend
        except ImportError:
            self.skipTest("Módulo system_health não encontrado")
        
        # Configurar mock para simular resposta do backend
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'version': '1.0.0',
            'database_status': 'connected'
        }
        mock_get.return_value = mock_response
        
        # Testar verificação
        with patch('monitoramento.system_health.get_config') as mock_config:
            mock_config.return_value = 'http://localhost:5000'
            
            status, data = verificar_backend()
            
            # Verificar resultado
            self.assertTrue(status)
            self.assertEqual(data['version'], '1.0.0')
            self.assertEqual(data['database_status'], 'connected')
            mock_get.assert_called_once_with('http://localhost:5000/health', timeout=10)

class TestBackup(unittest.TestCase):
    """Testes para o script de backup"""
    
    def setUp(self):
        """Configuração para os testes"""
        # Criar diretório temporário para testes
        self.test_dir = tempfile.mkdtemp()
        
        # Criar estrutura de diretórios para teste
        self.config_dir = os.path.join(self.test_dir, 'config')
        self.logs_dir = os.path.join(self.test_dir, 'logs')
        self.data_dir = os.path.join(self.test_dir, 'extracao_dados')
        self.backup_dir = os.path.join(self.test_dir, 'backups')
        
        os.makedirs(self.config_dir)
        os.makedirs(self.logs_dir)
        os.makedirs(self.data_dir)
        os.makedirs(self.backup_dir)
        
        # Criar alguns arquivos de teste
        with open(os.path.join(self.config_dir, 'test_config.json'), 'w') as f:
            f.write('{"test": "value"}')
        
        with open(os.path.join(self.logs_dir, 'test.log'), 'w') as f:
            f.write('Test log entry')
        
        with open(os.path.join(self.data_dir, 'test_data.json'), 'w') as f:
            f.write('{"data": "test"}')
    
    def tearDown(self):
        """Limpeza após os testes"""
        # Remover diretório temporário
        shutil.rmtree(self.test_dir)
    
    def test_backup_configuracoes(self):
        """Testa o backup de configurações"""
        # Importar função a ser testada
        try:
            from monitoramento.backup import backup_configuracoes
        except ImportError:
            self.skipTest("Módulo backup não encontrado")
        
        # Testar backup de configurações
        with patch('monitoramento.backup.get_config') as mock_config:
            mock_config.side_effect = lambda key, default: {
                'paths.config_dir': self.config_dir
            }.get(key, default)
            
            # Criar diretório de backup para o teste
            backup_path = os.path.join(self.backup_dir, 'test_backup')
            os.makedirs(backup_path)
            
            # Executar backup
            result = backup_configuracoes(backup_path)
            
            # Verificar resultado
            self.assertTrue(result)
            self.assertTrue(os.path.exists(os.path.join(backup_path, 'config')))
            self.assertTrue(os.path.exists(os.path.join(backup_path, 'config', 'test_config.json')))
            
            # Verificar conteúdo do arquivo
            with open(os.path.join(backup_path, 'config', 'test_config.json'), 'r') as f:
                content = f.read()
                self.assertEqual(content, '{"test": "value"}')

class TestLogMonitor(unittest.TestCase):
    """Testes para o script de monitoramento de logs"""
    
    def setUp(self):
        """Configuração para os testes"""
        # Criar diretório temporário para testes
        self.test_dir = tempfile.mkdtemp()
        
        # Criar arquivo de log de teste
        self.log_file = os.path.join(self.test_dir, 'test.log')
        with open(self.log_file, 'w') as f:
            f.write('2025-05-23 21:00:00 INFO: Normal log entry\n')
            f.write('2025-05-23 21:01:00 WARNING: This is a warning\n')
            f.write('2025-05-23 21:02:00 ERROR: This is an error\n')
            f.write('2025-05-23 21:03:00 INFO: Another normal entry\n')
            f.write('2025-05-23 21:04:00 CRITICAL: Critical error occurred\n')
    
    def tearDown(self):
        """Limpeza após os testes"""
        # Remover diretório temporário
        shutil.rmtree(self.test_dir)
    
    def test_analisar_log(self):
        """Testa a análise de logs"""
        # Importar função a ser testada
        try:
            from monitoramento.log_monitor import analisar_log
        except ImportError:
            self.skipTest("Módulo log_monitor não encontrado")
        
        # Testar análise de log
        with patch('monitoramento.log_monitor.get_config') as mock_config:
            mock_config.return_value = {
                'error': ['ERROR', 'Exception'],
                'warning': ['WARNING', 'WARN'],
                'critical': ['CRITICAL', 'FATAL']
            }
            
            # Executar análise
            counts, occurrences = analisar_log(self.log_file)
            
            # Verificar contagens
            self.assertEqual(counts['error'], 1)
            self.assertEqual(counts['warning'], 1)
            self.assertEqual(counts['critical'], 1)
            self.assertEqual(counts['total_lines'], 5)
            
            # Verificar ocorrências
            self.assertEqual(len(occurrences['error']), 1)
            self.assertEqual(len(occurrences['warning']), 1)
            self.assertEqual(len(occurrences['critical']), 1)
            
            # Verificar conteúdo das ocorrências
            self.assertIn('This is an error', occurrences['error'][0]['text'])
            self.assertIn('This is a warning', occurrences['warning'][0]['text'])
            self.assertIn('Critical error occurred', occurrences['critical'][0]['text'])

if __name__ == '__main__':
    unittest.main()

import unittest
import os
import json
import time
from unittest.mock import patch, MagicMock
import sys

# Adiciona o diretório pai ao path para importar os módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.logging_system import (
    LoggingSystem,
    LogLevel,
    LogCategory,
    LogEntry,
    debug,
    info,
    warning,
    error,
    critical
)

class TestLoggingSystem(unittest.TestCase):
    """Testes para o sistema de logging."""
    
    def setUp(self):
        """Configura ambiente de teste."""
        # Cria diretório temporário para logs
        self.test_log_dir = os.path.join(os.path.dirname(__file__), 'test_logs')
        os.makedirs(self.test_log_dir, exist_ok=True)
        
        # Instancia sistema de logging para testes
        self.logging_system = LoggingSystem(
            max_memory_logs=10,
            log_dir=self.test_log_dir
        )
    
    def tearDown(self):
        """Limpa ambiente após testes."""
        # Remove arquivos de log de teste
        for file in os.listdir(self.test_log_dir):
            os.remove(os.path.join(self.test_log_dir, file))
        os.rmdir(self.test_log_dir)
    
    def test_log_entry_creation(self):
        """Testa criação de entradas de log."""
        entry = LogEntry(
            message="Teste de log",
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            user_id=1,
            request_id="req-123",
            extra={"key": "value"}
        )
        
        self.assertEqual(entry.message, "Teste de log")
        self.assertEqual(entry.level, LogLevel.INFO)
        self.assertEqual(entry.category, LogCategory.SYSTEM)
        self.assertEqual(entry.user_id, 1)
        self.assertEqual(entry.request_id, "req-123")
        self.assertEqual(entry.extra, {"key": "value"})
    
    def test_log_entry_serialization(self):
        """Testa serialização e desserialização de entradas de log."""
        entry = LogEntry(
            message="Teste de serialização",
            level=LogLevel.WARNING,
            category=LogCategory.SECURITY,
            user_id=2,
            request_id="req-456",
            extra={"test": True}
        )
        
        # Serializa para dicionário
        entry_dict = entry.to_dict()
        
        # Desserializa de volta para objeto
        restored_entry = LogEntry.from_dict(entry_dict)
        
        self.assertEqual(restored_entry.id, entry.id)
        self.assertEqual(restored_entry.message, entry.message)
        self.assertEqual(restored_entry.level, entry.level)
        self.assertEqual(restored_entry.category, entry.category)
        self.assertEqual(restored_entry.user_id, entry.user_id)
        self.assertEqual(restored_entry.request_id, entry.request_id)
        self.assertEqual(restored_entry.extra, entry.extra)
    
    def test_log_methods(self):
        """Testa métodos de log de diferentes níveis."""
        # Testa método debug
        debug_id = self.logging_system.debug("Mensagem debug")
        self.assertIsNotNone(debug_id)
        
        # Testa método info
        info_id = self.logging_system.info("Mensagem info")
        self.assertIsNotNone(info_id)
        
        # Testa método warning
        warning_id = self.logging_system.warning("Mensagem warning")
        self.assertIsNotNone(warning_id)
        
        # Testa método error
        error_id = self.logging_system.error("Mensagem error")
        self.assertIsNotNone(error_id)
        
        # Testa método critical
        critical_id = self.logging_system.critical("Mensagem critical")
        self.assertIsNotNone(critical_id)
        
        # Aguarda processamento da fila
        time.sleep(1)
        
        # Verifica se os logs foram armazenados em memória
        logs = self.logging_system.get_logs()
        self.assertGreaterEqual(len(logs), 5)
    
    def test_log_filtering(self):
        """Testa filtragem de logs."""
        # Cria logs de diferentes níveis e categorias
        self.logging_system.info("Info log", category=LogCategory.SYSTEM)
        self.logging_system.error("Error log", category=LogCategory.SECURITY)
        self.logging_system.warning("Warning log", category=LogCategory.API)
        self.logging_system.info("User log", category=LogCategory.USER, user_id=1)
        self.logging_system.error("Another error", category=LogCategory.DATABASE)
        
        # Aguarda processamento da fila
        time.sleep(1)
        
        # Filtra por nível
        error_logs = self.logging_system.get_logs(level=LogLevel.ERROR)
        self.assertEqual(len(error_logs), 2)
        
        # Filtra por categoria
        security_logs = self.logging_system.get_logs(category=LogCategory.SECURITY)
        self.assertEqual(len(security_logs), 1)
        
        # Filtra por usuário
        user_logs = self.logging_system.get_logs(user_id=1)
        self.assertEqual(len(user_logs), 1)
    
    def test_file_persistence(self):
        """Testa persistência de logs em arquivo."""
        # Cria alguns logs
        self.logging_system.info("Log para arquivo 1")
        self.logging_system.error("Log para arquivo 2")
        
        # Aguarda processamento da fila
        time.sleep(1)
        
        # Verifica se o arquivo de log foi criado
        today = time.strftime("%Y-%m-%d")
        log_file = os.path.join(self.test_log_dir, f"wondercom-{today}.log")
        self.assertTrue(os.path.exists(log_file))
        
        # Verifica conteúdo do arquivo
        with open(log_file, 'r') as f:
            lines = f.readlines()
            self.assertGreaterEqual(len(lines), 2)
            
            # Verifica se as linhas são JSON válido
            for line in lines:
                log_data = json.loads(line.strip())
                self.assertIn("message", log_data)
                self.assertIn("level", log_data)
    
    def test_global_functions(self):
        """Testa funções globais de conveniência."""
        with patch('app.services.logging_system.logging_system') as mock_system:
            # Configura mocks
            mock_system.debug.return_value = "debug-id"
            mock_system.info.return_value = "info-id"
            mock_system.warning.return_value = "warning-id"
            mock_system.error.return_value = "error-id"
            mock_system.critical.return_value = "critical-id"
            
            # Testa funções globais
            self.assertEqual(debug("Test debug"), "debug-id")
            self.assertEqual(info("Test info"), "info-id")
            self.assertEqual(warning("Test warning"), "warning-id")
            self.assertEqual(error("Test error"), "error-id")
            self.assertEqual(critical("Test critical"), "critical-id")
            
            # Verifica se os métodos foram chamados
            mock_system.debug.assert_called_once()
            mock_system.info.assert_called_once()
            mock_system.warning.assert_called_once()
            mock_system.error.assert_called_once()
            mock_system.critical.assert_called_once()

if __name__ == '__main__':
    unittest.main()

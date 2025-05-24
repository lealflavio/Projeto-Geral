import unittest
import os
import sys
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

# Adiciona o diretório pai ao path para importar os módulos da aplicação
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.routes.admin import get_system_metrics, get_user_metrics, get_wo_metrics, get_security_metrics
from app.auth import UserRole
from app import models

class TestAdminEndpoints(unittest.TestCase):
    def setUp(self):
        # Mock para Session
        self.db_mock = MagicMock()
        
        # Mock para query builder
        self.query_mock = MagicMock()
        self.db_mock.query.return_value = self.query_mock
        
        # Mock para func.count
        self.count_mock = MagicMock()
        self.count_mock.scalar.return_value = 10
        self.query_mock.filter.return_value = self.query_mock
        self.query_mock.group_by.return_value = self.query_mock
        self.query_mock.order_by.return_value = self.query_mock
        self.query_mock.limit.return_value = self.query_mock
        self.query_mock.offset.return_value = self.query_mock
        self.query_mock.all.return_value = []
        
        # Mock para usuário atual
        self.current_user_mock = MagicMock()
        self.current_user_mock.id = 1
        self.current_user_mock.email = "admin@example.com"
        self.current_user_mock.role = UserRole.ADMIN
        
        # Mock para alert_manager
        self.alert_manager_mock = MagicMock()
        self.alert_manager_mock.get_alerts.return_value = []
        self.alert_manager_mock.get_alert_history.return_value = []
        
    @patch('app.routes.admin.func.count')
    async def test_get_system_metrics(self, count_mock):
        # Configura o mock para func.count
        count_mock.return_value = self.count_mock
        
        # Executa a função
        result = await get_system_metrics(
            period="day",
            current_user=self.current_user_mock,
            db=self.db_mock
        )
        
        # Verifica o resultado
        self.assertIsInstance(result, dict)
        self.assertEqual(result["period"], "day")
        self.assertIn("timestamp", result)
        self.assertIn("users", result)
        self.assertIn("wos", result)
        self.assertIn("security", result)
        self.assertIn("logs", result)
        self.assertIn("alerts", result)
        
        # Verifica se os métodos corretos foram chamados
        self.db_mock.query.assert_called()
        self.query_mock.filter.assert_called()
        
    @patch('app.routes.admin.func.count')
    async def test_get_user_metrics(self, count_mock):
        # Configura o mock para func.count
        count_mock.return_value = self.count_mock
        
        # Executa a função
        result = await get_user_metrics(
            period="day",
            current_user=self.current_user_mock,
            db=self.db_mock
        )
        
        # Verifica o resultado
        self.assertIsInstance(result, dict)
        self.assertEqual(result["period"], "day")
        self.assertIn("timestamp", result)
        self.assertIn("total_users", result)
        self.assertIn("active_users", result)
        self.assertIn("inactive_users", result)
        self.assertIn("new_users", result)
        self.assertIn("by_role", result)
        self.assertIn("login_activity", result)
        self.assertIn("most_active_users", result)
        
        # Verifica se os métodos corretos foram chamados
        self.db_mock.query.assert_called()
        
    @patch('app.routes.admin.func.count')
    async def test_get_wo_metrics(self, count_mock):
        # Configura o mock para func.count
        count_mock.return_value = self.count_mock
        
        # Executa a função
        result = await get_wo_metrics(
            period="day",
            current_user=self.current_user_mock,
            db=self.db_mock
        )
        
        # Verifica o resultado
        self.assertIsInstance(result, dict)
        self.assertEqual(result["period"], "day")
        self.assertIn("timestamp", result)
        self.assertIn("total_wos", result)
        self.assertIn("recent_wos", result)
        self.assertIn("by_status", result)
        self.assertIn("by_tipo_servico", result)
        self.assertIn("by_tecnico", result)
        self.assertIn("recent_activity", result)
        
        # Verifica se os métodos corretos foram chamados
        self.db_mock.query.assert_called()
        
    @patch('app.routes.admin.func.count')
    async def test_get_security_metrics(self, count_mock):
        # Configura o mock para func.count
        count_mock.return_value = self.count_mock
        
        # Executa a função
        result = await get_security_metrics(
            period="day",
            current_user=self.current_user_mock,
            db=self.db_mock
        )
        
        # Verifica o resultado
        self.assertIsInstance(result, dict)
        self.assertEqual(result["period"], "day")
        self.assertIn("timestamp", result)
        self.assertIn("total_events", result)
        self.assertIn("by_severity", result)
        self.assertIn("by_action", result)
        self.assertIn("failed_logins", result)
        self.assertIn("account_lockouts", result)
        self.assertIn("password_resets", result)
        self.assertIn("suspicious_ips", result)
        self.assertIn("recent_events", result)
        
        # Verifica se os métodos corretos foram chamados
        self.db_mock.query.assert_called()

if __name__ == '__main__':
    unittest.main()

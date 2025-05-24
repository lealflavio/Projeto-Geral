from locust import HttpUser, task, between

class WondercomUser(HttpUser):
    """
    Classe de usuário para testes de carga do Projeto Wondercom Automation.
    
    Esta classe simula o comportamento de usuários reais interagindo com as APIs
    do sistema, permitindo avaliar o desempenho sob carga.
    """
    
    # Tempo de espera entre requisições (1-5 segundos)
    wait_time = between(1, 5)
    
    # Token de autenticação simulado
    token = None
    
    def on_start(self):
        """Método executado quando um usuário virtual inicia."""
        # Autenticar o usuário e obter token
        response = self.client.post("/api/auth/login", json={
            "username": f"tecnico_teste_{self.user_id}",
            "password": "senha_teste_123"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
    
    @task(3)
    def check_credits(self):
        """Verificar créditos do usuário (peso 3)."""
        if not self.token:
            return
            
        self.client.get(
            "/usuarios/me",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(2)
    def get_history(self):
        """Obter histórico de serviços (peso 2)."""
        if not self.token:
            return
            
        self.client.get(
            "/usuarios/me/historico",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def allocate_wo(self):
        """Alocar uma WO (peso 1)."""
        if not self.token:
            return
            
        # Gerar número de WO aleatório baseado no ID do usuário
        wo_number = f"{10000 + self.user_id}"
        
        self.client.post(
            "/api/wondercom/allocate",
            json={
                "wo_number": wo_number,
                "portal_username": f"tecnico_teste_{self.user_id}",
                "portal_password": "senha_portal_123"
            },
            headers={"Authorization": f"Bearer {self.token}"}
        )

class AdminUser(HttpUser):
    """
    Classe de usuário administrador para testes de carga.
    
    Esta classe simula o comportamento de administradores interagindo com
    as APIs administrativas do sistema.
    """
    
    # Tempo de espera entre requisições (2-8 segundos)
    wait_time = between(2, 8)
    
    # Token de autenticação simulado
    token = None
    
    def on_start(self):
        """Método executado quando um usuário virtual inicia."""
        # Autenticar o administrador e obter token
        response = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin_senha_123"
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
    
    @task(1)
    def get_all_users(self):
        """Obter lista de todos os usuários."""
        if not self.token:
            return
            
        self.client.get(
            "/admin/usuarios",
            headers={"Authorization": f"Bearer {self.token}"}
        )
    
    @task(1)
    def get_system_stats(self):
        """Obter estatísticas do sistema."""
        if not self.token:
            return
            
        self.client.get(
            "/admin/estatisticas",
            headers={"Authorization": f"Bearer {self.token}"}
        )

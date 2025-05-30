import os

# Estrutura de diretórios sugerida
project_name = "agente_wondercom"
directories = [
    f"{project_name}/agents",
    f"{project_name}/tools",
    f"{project_name}/models",
    f"{project_name}/playwright_automation",
    f"{project_name}/data",
    f"{project_name}/logs",
]

# Criar diretórios
for directory in directories:
    os.makedirs(directory, exist_ok=True)

# Criar arquivos base
files = {
    f"{project_name}/main.py": "# Ponto de entrada principal do agente\n",
    f"{project_name}/tools/playwright_tools.py": "# Ferramentas para o agente usar Playwright\n",
    f"{project_name}/models/model_loader.py": "# Código para carregar modelo local (ex: Mistral via Ollama)\n",
    f"{project_name}/agents/langchain_agent.py": "# Agente LangChain que usa o modelo e as ferramentas\n",
    f"{project_name}/data/state_example.json": "{\n  \"url\": \"https://portal.wondercom.pt\",\n  \"modais\": [],\n  \"campos\": {},\n  \"etapa\": \"inicio\"\n}\n",
    f"{project_name}/logs/history.log": "# Logs de interações e decisões do agente\n"
}

# Criar arquivos base
for path, content in files.items():
    with open(path, "w") as f:
        f.write(content)

# Mostrar estrutura criada
os.listdir(project_name)

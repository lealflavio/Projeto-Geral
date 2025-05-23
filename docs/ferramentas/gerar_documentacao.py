#!/usr/bin/env python3
"""
Script para Geração de Documentação Automática do Projeto

Este script analisa a estrutura do projeto e gera documentação automática,
incluindo mapeamento de arquivos, dependências e relações entre componentes.

Uso:
    python3 gerar_documentacao.py [diretorio_raiz]

Saída:
    Arquivos de documentação em formato Markdown na pasta 'docs/'
"""

import os
import sys
import re
import json
from datetime import datetime

def criar_estrutura_docs(diretorio_raiz):
    """Cria a estrutura de diretórios para a documentação"""
    docs_dir = os.path.join(diretorio_raiz, "docs")
    
    # Criar diretório docs se não existir
    if not os.path.exists(docs_dir):
        os.makedirs(docs_dir)
    
    # Criar subdiretórios para cada componente
    for componente in ["automacao", "backend", "frontend"]:
        componente_dir = os.path.join(docs_dir, componente)
        if not os.path.exists(componente_dir):
            os.makedirs(componente_dir)
    
    return docs_dir

def mapear_estrutura_diretorios(diretorio_raiz):
    """Mapeia a estrutura de diretórios do projeto"""
    estrutura = {}
    
    for raiz, diretorios, arquivos in os.walk(diretorio_raiz):
        # Ignorar diretórios de ambiente virtual e node_modules
        if "env" in raiz or "node_modules" in raiz or "__pycache__" in raiz:
            continue
        
        # Caminho relativo à raiz do projeto
        caminho_relativo = os.path.relpath(raiz, diretorio_raiz)
        if caminho_relativo == ".":
            caminho_relativo = ""
        
        # Adicionar diretório à estrutura
        estrutura[caminho_relativo] = {
            "arquivos": [],
            "tipo": determinar_tipo_diretorio(caminho_relativo)
        }
        
        # Adicionar arquivos ao diretório
        for arquivo in arquivos:
            # Ignorar arquivos temporários e binários
            if arquivo.endswith((".pyc", ".pyo", ".pyd", ".so", ".dll", ".class")):
                continue
            
            caminho_arquivo = os.path.join(raiz, arquivo)
            tipo_arquivo = determinar_tipo_arquivo(arquivo)
            
            estrutura[caminho_relativo]["arquivos"].append({
                "nome": arquivo,
                "tipo": tipo_arquivo,
                "tamanho": os.path.getsize(caminho_arquivo),
                "ultima_modificacao": datetime.fromtimestamp(os.path.getmtime(caminho_arquivo)).strftime("%Y-%m-%d %H:%M:%S")
            })
    
    return estrutura

def determinar_tipo_diretorio(caminho):
    """Determina o tipo de diretório com base no caminho"""
    if not caminho:
        return "raiz"
    
    if "dashboard/backend" in caminho:
        return "backend"
    elif "dashboard/frontend" in caminho:
        return "frontend"
    elif "tecnicos" in caminho:
        return "dados_tecnicos"
    elif "config" in caminho:
        return "configuracao"
    elif "extracao_dados" in caminho:
        return "dados"
    else:
        return "outro"

def determinar_tipo_arquivo(nome_arquivo):
    """Determina o tipo de arquivo com base na extensão"""
    if nome_arquivo.endswith(".py"):
        return "python"
    elif nome_arquivo.endswith((".js", ".jsx")):
        return "javascript"
    elif nome_arquivo.endswith((".html", ".htm")):
        return "html"
    elif nome_arquivo.endswith(".css"):
        return "css"
    elif nome_arquivo.endswith(".json"):
        return "json"
    elif nome_arquivo.endswith(".md"):
        return "markdown"
    elif nome_arquivo.endswith(".pdf"):
        return "pdf"
    elif nome_arquivo.endswith((".jpg", ".jpeg", ".png", ".gif")):
        return "imagem"
    elif nome_arquivo.endswith(".env"):
        return "configuracao"
    else:
        return "outro"

def analisar_arquivo_python(caminho_arquivo):
    """Analisa um arquivo Python para extrair informações relevantes"""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Extrair imports
        imports = re.findall(r'^import\s+(\w+)|^from\s+(\w+)', conteudo, re.MULTILINE)
        imports = [imp[0] if imp[0] else imp[1] for imp in imports]
        
        # Extrair funções
        funcoes = re.findall(r'^def\s+(\w+)\s*\(', conteudo, re.MULTILINE)
        
        # Extrair classes
        classes = re.findall(r'^class\s+(\w+)', conteudo, re.MULTILINE)
        
        # Extrair docstring (se existir)
        docstring_match = re.search(r'"""(.*?)"""', conteudo, re.DOTALL)
        docstring = docstring_match.group(1).strip() if docstring_match else ""
        
        return {
            "imports": imports,
            "funcoes": funcoes,
            "classes": classes,
            "docstring": docstring
        }
    except Exception as e:
        return {
            "erro": str(e),
            "imports": [],
            "funcoes": [],
            "classes": [],
            "docstring": ""
        }

def gerar_documentacao_markdown(estrutura, diretorio_docs, diretorio_raiz):
    """Gera arquivos de documentação em Markdown"""
    # Gerar índice principal
    with open(os.path.join(diretorio_docs, "README.md"), 'w', encoding='utf-8') as f:
        f.write("# Documentação do Projeto\n\n")
        f.write("Gerado automaticamente em: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        
        f.write("## Estrutura do Projeto\n\n")
        f.write("O projeto está dividido em três pilares principais:\n\n")
        f.write("1. [Scripts de Automação (VM)](automacao/README.md)\n")
        f.write("2. [Backend (Render)](backend/README.md)\n")
        f.write("3. [Frontend (Netlify)](frontend/README.md)\n\n")
        
        f.write("## Visão Geral dos Diretórios\n\n")
        f.write("| Diretório | Tipo | Arquivos |\n")
        f.write("|-----------|------|----------|\n")
        
        for diretorio, info in sorted(estrutura.items()):
            caminho = diretorio if diretorio else "/"
            tipo = info["tipo"]
            num_arquivos = len(info["arquivos"])
            f.write(f"| {caminho} | {tipo} | {num_arquivos} |\n")
    
    # Gerar documentação para automação
    gerar_doc_automacao(estrutura, diretorio_docs, diretorio_raiz)
    
    # Gerar documentação para backend
    gerar_doc_backend(estrutura, diretorio_docs, diretorio_raiz)
    
    # Gerar documentação para frontend
    gerar_doc_frontend(estrutura, diretorio_docs, diretorio_raiz)

def gerar_doc_automacao(estrutura, diretorio_docs, diretorio_raiz):
    """Gera documentação para os scripts de automação"""
    automacao_dir = os.path.join(diretorio_docs, "automacao")
    
    with open(os.path.join(automacao_dir, "README.md"), 'w', encoding='utf-8') as f:
        f.write("# Scripts de Automação (VM)\n\n")
        f.write("Esta seção documenta os scripts de automação que rodam na VM.\n\n")
        
        f.write("## Scripts Principais\n\n")
        f.write("| Script | Descrição | Funções |\n")
        f.write("|--------|-----------|----------|\n")
        
        # Listar scripts principais na raiz
        scripts_principais = [
            "M1_Extrator_PDF.py",
            "M2_Orquestrador_PDFs.py",
            "M3_Leitura_Drive.py",
            "M4_Manipulacao_Arquivos.py",
            "M5_Config_Tecnicos.py",
            "M6_Notificacao_Status.py"
        ]
        
        for script in scripts_principais:
            if "" in estrutura:  # Raiz do projeto
                for arquivo in estrutura[""]["arquivos"]:
                    if arquivo["nome"] == script:
                        caminho_completo = os.path.join(diretorio_raiz, script)
                        analise = analisar_arquivo_python(caminho_completo)
                        
                        funcoes = ", ".join(analise["funcoes"])
                        descricao = analise["docstring"][:50] + "..." if len(analise["docstring"]) > 50 else analise["docstring"]
                        
                        if not descricao:
                            if "M1_Extrator_PDF" in script:
                                descricao = "Extrai dados de arquivos PDF"
                            elif "M2_Orquestrador" in script:
                                descricao = "Gerencia o fluxo de processamento de PDFs"
                            elif "M3_Leitura_Drive" in script:
                                descricao = "Integração com Google Drive"
                            elif "M4_Manipulacao" in script:
                                descricao = "Funções para manipulação de arquivos"
                            elif "M5_Config" in script:
                                descricao = "Gerencia configurações dos técnicos"
                            elif "M6_Notificacao" in script:
                                descricao = "Envia notificações sobre o status"
                        
                        f.write(f"| [{script}](../../{script}) | {descricao} | {funcoes} |\n")
                        
                        # Criar arquivo detalhado para cada script
                        with open(os.path.join(automacao_dir, f"{script.replace('.py', '')}.md"), 'w', encoding='utf-8') as sf:
                            sf.write(f"# {script}\n\n")
                            
                            if analise["docstring"]:
                                sf.write(f"{analise['docstring']}\n\n")
                            else:
                                sf.write(f"Script para {descricao}.\n\n")
                            
                            sf.write("## Imports\n\n")
                            for imp in analise["imports"]:
                                sf.write(f"- `{imp}`\n")
                            
                            sf.write("\n## Funções\n\n")
                            for func in analise["funcoes"]:
                                sf.write(f"- `{func}()`\n")
                            
                            if analise["classes"]:
                                sf.write("\n## Classes\n\n")
                                for classe in analise["classes"]:
                                    sf.write(f"- `{classe}`\n")

def gerar_doc_backend(estrutura, diretorio_docs, diretorio_raiz):
    """Gera documentação para o backend"""
    backend_dir = os.path.join(diretorio_docs, "backend")
    
    with open(os.path.join(backend_dir, "README.md"), 'w', encoding='utf-8') as f:
        f.write("# Backend (Render)\n\n")
        f.write("Esta seção documenta a API e banco de dados do backend.\n\n")
        
        f.write("## Estrutura do Backend\n\n")
        f.write("| Arquivo/Diretório | Tipo | Descrição |\n")
        f.write("|-------------------|------|----------|\n")
        
        # Listar arquivos e diretórios do backend
        for diretorio, info in sorted(estrutura.items()):
            if "dashboard/backend" in diretorio:
                for arquivo in info["arquivos"]:
                    caminho = os.path.join(diretorio, arquivo["nome"])
                    tipo = arquivo["tipo"]
                    
                    descricao = ""
                    if arquivo["tipo"] == "python":
                        if "auth" in arquivo["nome"]:
                            descricao = "Gerenciamento de autenticação"
                        elif "database" in arquivo["nome"]:
                            descricao = "Configuração do banco de dados"
                        elif "models" in arquivo["nome"]:
                            descricao = "Definição dos modelos de dados"
                        elif "schemas" in arquivo["nome"]:
                            descricao = "Esquemas para validação de dados"
                        elif "main" in arquivo["nome"]:
                            descricao = "Ponto de entrada da aplicação"
                        elif "create_tables" in arquivo["nome"]:
                            descricao = "Criação das tabelas no banco de dados"
                    
                    f.write(f"| {caminho} | {tipo} | {descricao} |\n")

def gerar_doc_frontend(estrutura, diretorio_docs, diretorio_raiz):
    """Gera documentação para o frontend"""
    frontend_dir = os.path.join(diretorio_docs, "frontend")
    
    with open(os.path.join(frontend_dir, "README.md"), 'w', encoding='utf-8') as f:
        f.write("# Frontend (Netlify)\n\n")
        f.write("Esta seção documenta a interface de usuário do frontend.\n\n")
        
        f.write("## Estrutura do Frontend\n\n")
        f.write("| Arquivo/Diretório | Tipo | Descrição |\n")
        f.write("|-------------------|------|----------|\n")
        
        # Listar arquivos e diretórios do frontend
        for diretorio, info in sorted(estrutura.items()):
            if "dashboard/frontend/src" in diretorio:
                for arquivo in info["arquivos"]:
                    caminho = os.path.join(diretorio, arquivo["nome"])
                    tipo = arquivo["tipo"]
                    
                    descricao = ""
                    if "App.jsx" in arquivo["nome"]:
                        descricao = "Componente principal da aplicação"
                    elif "main.jsx" in arquivo["nome"]:
                        descricao = "Ponto de entrada da aplicação"
                    
                    f.write(f"| {caminho} | {tipo} | {descricao} |\n")

def main():
    """Função principal"""
    if len(sys.argv) > 1:
        diretorio_raiz = sys.argv[1]
    else:
        diretorio_raiz = os.getcwd()
    
    print(f"Gerando documentação para: {diretorio_raiz}")
    
    # Criar estrutura de diretórios para documentação
    diretorio_docs = criar_estrutura_docs(diretorio_raiz)
    print(f"Diretório de documentação criado: {diretorio_docs}")
    
    # Mapear estrutura de diretórios
    estrutura = mapear_estrutura_diretorios(diretorio_raiz)
    print(f"Mapeamento concluído: {len(estrutura)} diretórios encontrados")
    
    # Gerar documentação em Markdown
    gerar_documentacao_markdown(estrutura, diretorio_docs, diretorio_raiz)
    print("Documentação gerada com sucesso!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

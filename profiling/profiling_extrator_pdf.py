#!/usr/bin/env python3
"""
Script para análise de profiling do módulo M1_Extrator_PDF.py
"""

import os
import sys
import cProfile
import pstats
import io
import time
from memory_profiler import profile as memory_profile
import tempfile

# Adicionar o diretório raiz ao path para importar o módulo
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar o módulo a ser analisado
import M1_Extrator_PDF as extrator

# Diretório com os PDFs de teste
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../tests/fixtures'))

def get_pdf_files():
    """Retorna a lista de arquivos PDF no diretório de fixtures"""
    if not os.path.exists(FIXTURES_DIR):
        print(f"Diretório de fixtures não encontrado: {FIXTURES_DIR}")
        return []
    
    return [os.path.join(FIXTURES_DIR, f) for f in os.listdir(FIXTURES_DIR) if f.endswith('.pdf')]

def run_time_profiling():
    """Executa profiling de tempo de execução usando cProfile"""
    pdf_files = get_pdf_files()
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado para análise")
        return
    
    print(f"Executando profiling de tempo em {len(pdf_files)} arquivos PDF...")
    
    # Criar diretório temporário para saída
    temp_dir = tempfile.mkdtemp()
    
    # Configurar profiler
    pr = cProfile.Profile()
    pr.enable()
    
    # Processar cada PDF e medir o tempo
    start_time = time.time()
    for pdf_file in pdf_files:
        print(f"Processando {os.path.basename(pdf_file)}...")
        extrator.extrair_dados_pdf_relevantes(pdf_file, temp_dir)
    
    total_time = time.time() - start_time
    pr.disable()
    
    # Salvar e exibir resultados
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Mostrar as 20 funções que mais consomem tempo
    
    results_file = os.path.join(os.path.dirname(__file__), 'time_profiling_results.txt')
    with open(results_file, 'w') as f:
        f.write(f"Tempo total para processar {len(pdf_files)} PDFs: {total_time:.2f} segundos\n")
        f.write(f"Tempo médio por PDF: {total_time/len(pdf_files):.2f} segundos\n\n")
        f.write(s.getvalue())
    
    print(f"Resultados de profiling de tempo salvos em {results_file}")
    print(f"Tempo total: {total_time:.2f} segundos")
    print(f"Tempo médio por PDF: {total_time/len(pdf_files):.2f} segundos")
    
    # Limpar arquivos temporários
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)

@memory_profile
def process_pdf_with_memory_profiling(pdf_file, output_dir):
    """Processa um único PDF com memory_profiler"""
    return extrator.extrair_dados_pdf_relevantes(pdf_file, output_dir)

def run_memory_profiling():
    """Executa profiling de uso de memória usando memory_profiler"""
    pdf_files = get_pdf_files()
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado para análise")
        return
    
    print(f"Executando profiling de memória em {len(pdf_files)} arquivos PDF...")
    
    # Criar diretório temporário para saída
    temp_dir = tempfile.mkdtemp()
    
    # Processar o primeiro PDF com memory profiling
    pdf_file = pdf_files[0]
    print(f"Analisando uso de memória ao processar {os.path.basename(pdf_file)}...")
    
    # Redirecionar saída do memory_profiler para um arquivo
    results_file = os.path.join(os.path.dirname(__file__), 'memory_profiling_results.txt')
    with open(results_file, 'w') as f:
        # Salvar stdout original
        original_stdout = sys.stdout
        sys.stdout = f
        
        # Executar com memory profiling
        process_pdf_with_memory_profiling(pdf_file, temp_dir)
        
        # Restaurar stdout
        sys.stdout = original_stdout
    
    print(f"Resultados de profiling de memória salvos em {results_file}")
    
    # Limpar arquivos temporários
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)

def analyze_specific_functions():
    """Analisa funções específicas que podem ser gargalos"""
    pdf_files = get_pdf_files()
    if not pdf_files and len(pdf_files) > 0:
        pdf_file = pdf_files[0]
        temp_dir = tempfile.mkdtemp()
        
        # Medir tempo de funções específicas
        functions_to_analyze = [
            ("extrair_secao_multilinha", lambda: extrator.extrair_secao_multilinha("", "", "")),
            ("extrair_equipamentos", lambda: extrator.extrair_equipamentos("")),
            ("extrair_materiais", lambda: extrator.extrair_materiais(""))
        ]
        
        results_file = os.path.join(os.path.dirname(__file__), 'function_analysis_results.txt')
        with open(results_file, 'w') as f:
            for func_name, func_call in functions_to_analyze:
                try:
                    start_time = time.time()
                    func_call()
                    elapsed = time.time() - start_time
                    f.write(f"Função {func_name}: {elapsed:.6f} segundos\n")
                except Exception as e:
                    f.write(f"Erro ao analisar {func_name}: {str(e)}\n")
        
        # Limpar arquivos temporários
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)

if __name__ == "__main__":
    # Criar diretório para resultados de profiling se não existir
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    
    print("Iniciando análise de profiling do módulo M1_Extrator_PDF.py...")
    
    # Executar profiling de tempo
    run_time_profiling()
    
    # Executar profiling de memória
    run_memory_profiling()
    
    # Analisar funções específicas
    analyze_specific_functions()
    
    print("Análise de profiling concluída!")

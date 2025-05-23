#!/usr/bin/env python3
"""
Script para benchmark comparativo entre a versão original e otimizada do extrator de PDF
"""

import os
import sys
import time
import tempfile
import json
import matplotlib.pyplot as plt
import numpy as np
from memory_profiler import memory_usage
import psutil

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar os módulos a serem comparados
import M1_Extrator_PDF as extrator_original
import M1_Extrator_PDF_Otimizado as extrator_otimizado

# Diretório com os PDFs de teste
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../tests/fixtures'))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'benchmark_results'))

def get_pdf_files():
    """Retorna a lista de arquivos PDF no diretório de fixtures"""
    if not os.path.exists(FIXTURES_DIR):
        print(f"Diretório de fixtures não encontrado: {FIXTURES_DIR}")
        return []
    
    return [os.path.join(FIXTURES_DIR, f) for f in os.listdir(FIXTURES_DIR) if f.endswith('.pdf')]

def benchmark_tempo_execucao():
    """Compara o tempo de execução entre as versões original e otimizada"""
    pdf_files = get_pdf_files()
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado para benchmark")
        return
    
    print(f"Executando benchmark de tempo em {len(pdf_files)} arquivos PDF...")
    
    # Criar diretórios temporários para saída
    temp_dir_original = tempfile.mkdtemp()
    temp_dir_otimizado = tempfile.mkdtemp()
    
    # Benchmark da versão original
    print("Testando versão original...")
    start_time_original = time.time()
    for pdf_file in pdf_files:
        print(f"  Processando {os.path.basename(pdf_file)}...")
        extrator_original.extrair_dados_pdf_relevantes(pdf_file, temp_dir_original)
    tempo_original = time.time() - start_time_original
    
    # Benchmark da versão otimizada (processamento sequencial para comparação justa)
    print("Testando versão otimizada (sequencial)...")
    start_time_otimizado_seq = time.time()
    for pdf_file in pdf_files:
        print(f"  Processando {os.path.basename(pdf_file)}...")
        extrator_otimizado.extrair_dados_pdf_relevantes(pdf_file, temp_dir_otimizado)
    tempo_otimizado_seq = time.time() - start_time_otimizado_seq
    
    # Benchmark da versão otimizada com processamento paralelo
    print("Testando versão otimizada (paralela)...")
    start_time_otimizado_par = time.time()
    extrator_otimizado.processar_pdfs_em_paralelo(pdf_files, temp_dir_otimizado)
    tempo_otimizado_par = time.time() - start_time_otimizado_par
    
    # Benchmark da versão otimizada com cache
    print("Testando versão otimizada (com cache)...")
    start_time_otimizado_cache = time.time()
    for pdf_file in pdf_files:
        print(f"  Processando {os.path.basename(pdf_file)}...")
        extrator_otimizado.extrair_dados_pdf_com_cache(pdf_file, temp_dir_otimizado)
    tempo_otimizado_cache = time.time() - start_time_otimizado_cache
    
    # Salvar resultados
    resultados = {
        "num_pdfs": len(pdf_files),
        "tempo_original": tempo_original,
        "tempo_por_pdf_original": tempo_original / len(pdf_files),
        "tempo_otimizado_sequencial": tempo_otimizado_seq,
        "tempo_por_pdf_otimizado_seq": tempo_otimizado_seq / len(pdf_files),
        "tempo_otimizado_paralelo": tempo_otimizado_par,
        "tempo_por_pdf_otimizado_par": tempo_otimizado_par / len(pdf_files),
        "tempo_otimizado_cache": tempo_otimizado_cache,
        "tempo_por_pdf_otimizado_cache": tempo_otimizado_cache / len(pdf_files),
        "melhoria_sequencial": (tempo_original - tempo_otimizado_seq) / tempo_original * 100,
        "melhoria_paralela": (tempo_original - tempo_otimizado_par) / tempo_original * 100,
        "melhoria_cache": (tempo_original - tempo_otimizado_cache) / tempo_original * 100
    }
    
    # Criar diretório de resultados se não existir
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Salvar resultados em JSON
    with open(os.path.join(RESULTS_DIR, 'benchmark_tempo.json'), 'w') as f:
        json.dump(resultados, f, indent=2)
    
    # Exibir resultados
    print("\nResultados do benchmark de tempo:")
    print(f"Tempo total (original): {tempo_original:.4f} segundos")
    print(f"Tempo total (otimizado sequencial): {tempo_otimizado_seq:.4f} segundos")
    print(f"Tempo total (otimizado paralelo): {tempo_otimizado_par:.4f} segundos")
    print(f"Tempo total (otimizado com cache): {tempo_otimizado_cache:.4f} segundos")
    print(f"Melhoria (sequencial): {resultados['melhoria_sequencial']:.2f}%")
    print(f"Melhoria (paralela): {resultados['melhoria_paralela']:.2f}%")
    print(f"Melhoria (cache): {resultados['melhoria_cache']:.2f}%")
    
    # Limpar arquivos temporários
    for file in os.listdir(temp_dir_original):
        os.remove(os.path.join(temp_dir_original, file))
    os.rmdir(temp_dir_original)
    
    for file in os.listdir(temp_dir_otimizado):
        if os.path.isdir(os.path.join(temp_dir_otimizado, file)):
            # Se for o diretório de cache
            cache_dir = os.path.join(temp_dir_otimizado, file)
            for cache_file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, cache_file))
            os.rmdir(cache_dir)
        else:
            os.remove(os.path.join(temp_dir_otimizado, file))
    os.rmdir(temp_dir_otimizado)
    
    return resultados

def benchmark_memoria():
    """Compara o uso de memória entre as versões original e otimizada"""
    pdf_files = get_pdf_files()
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado para benchmark")
        return
    
    print(f"Executando benchmark de memória em {len(pdf_files)} arquivos PDF...")
    
    # Criar diretórios temporários para saída
    temp_dir_original = tempfile.mkdtemp()
    temp_dir_otimizado = tempfile.mkdtemp()
    
    # Selecionar o primeiro PDF para teste de memória
    pdf_file = pdf_files[0]
    
    # Função para medir uso de memória da versão original
    def func_original():
        extrator_original.extrair_dados_pdf_relevantes(pdf_file, temp_dir_original)
    
    # Função para medir uso de memória da versão otimizada
    def func_otimizada():
        extrator_otimizado.extrair_dados_pdf_relevantes(pdf_file, temp_dir_otimizado)
    
    # Função para medir uso de memória da versão otimizada com cache
    def func_otimizada_cache():
        extrator_otimizado.extrair_dados_pdf_com_cache(pdf_file, temp_dir_otimizado)
    
    # Medir uso de memória
    print("Medindo uso de memória da versão original...")
    mem_uso_original = memory_usage(func_original, interval=0.1, timeout=30)
    
    print("Medindo uso de memória da versão otimizada...")
    mem_uso_otimizado = memory_usage(func_otimizada, interval=0.1, timeout=30)
    
    print("Medindo uso de memória da versão otimizada com cache...")
    mem_uso_otimizado_cache = memory_usage(func_otimizada_cache, interval=0.1, timeout=30)
    
    # Calcular estatísticas
    resultados = {
        "memoria_max_original": max(mem_uso_original),
        "memoria_media_original": sum(mem_uso_original) / len(mem_uso_original),
        "memoria_max_otimizado": max(mem_uso_otimizado),
        "memoria_media_otimizado": sum(mem_uso_otimizado) / len(mem_uso_otimizado),
        "memoria_max_otimizado_cache": max(mem_uso_otimizado_cache),
        "memoria_media_otimizado_cache": sum(mem_uso_otimizado_cache) / len(mem_uso_otimizado_cache),
        "diferenca_max": (max(mem_uso_original) - max(mem_uso_otimizado)) / max(mem_uso_original) * 100,
        "diferenca_media": (sum(mem_uso_original) / len(mem_uso_original) - sum(mem_uso_otimizado) / len(mem_uso_otimizado)) / (sum(mem_uso_original) / len(mem_uso_original)) * 100
    }
    
    # Salvar resultados em JSON
    with open(os.path.join(RESULTS_DIR, 'benchmark_memoria.json'), 'w') as f:
        json.dump(resultados, f, indent=2)
    
    # Exibir resultados
    print("\nResultados do benchmark de memória:")
    print(f"Uso máximo de memória (original): {resultados['memoria_max_original']:.2f} MiB")
    print(f"Uso máximo de memória (otimizado): {resultados['memoria_max_otimizado']:.2f} MiB")
    print(f"Uso máximo de memória (otimizado com cache): {resultados['memoria_max_otimizado_cache']:.2f} MiB")
    print(f"Diferença no uso máximo: {resultados['diferenca_max']:.2f}%")
    
    # Limpar arquivos temporários
    for file in os.listdir(temp_dir_original):
        os.remove(os.path.join(temp_dir_original, file))
    os.rmdir(temp_dir_original)
    
    for file in os.listdir(temp_dir_otimizado):
        if os.path.isdir(os.path.join(temp_dir_otimizado, file)):
            # Se for o diretório de cache
            cache_dir = os.path.join(temp_dir_otimizado, file)
            for cache_file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, cache_file))
            os.rmdir(cache_dir)
        else:
            os.remove(os.path.join(temp_dir_otimizado, file))
    os.rmdir(temp_dir_otimizado)
    
    return resultados

def gerar_graficos(resultados_tempo, resultados_memoria):
    """Gera gráficos comparativos dos resultados"""
    # Criar diretório para gráficos
    os.makedirs(os.path.join(RESULTS_DIR, 'graficos'), exist_ok=True)
    
    # Gráfico de tempo de execução
    labels = ['Original', 'Otimizado\nSequencial', 'Otimizado\nParalelo', 'Otimizado\nCache']
    tempos = [
        resultados_tempo['tempo_original'],
        resultados_tempo['tempo_otimizado_sequencial'],
        resultados_tempo['tempo_otimizado_paralelo'],
        resultados_tempo['tempo_otimizado_cache']
    ]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, tempos, color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
    
    # Adicionar valores nas barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                 f'{height:.2f}s',
                 ha='center', va='bottom')
    
    plt.title('Comparação de Tempo de Execução')
    plt.ylabel('Tempo (segundos)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(RESULTS_DIR, 'graficos', 'tempo_execucao.png'), dpi=300, bbox_inches='tight')
    
    # Gráfico de uso de memória
    labels = ['Original', 'Otimizado', 'Otimizado\nCache']
    memoria_max = [
        resultados_memoria['memoria_max_original'],
        resultados_memoria['memoria_max_otimizado'],
        resultados_memoria['memoria_max_otimizado_cache']
    ]
    memoria_media = [
        resultados_memoria['memoria_media_original'],
        resultados_memoria['memoria_media_otimizado'],
        resultados_memoria['memoria_media_otimizado_cache']
    ]
    
    x = np.arange(len(labels))
    width = 0.35
    
    plt.figure(figsize=(10, 6))
    bars1 = plt.bar(x - width/2, memoria_max, width, label='Uso Máximo', color='#ff9999')
    bars2 = plt.bar(x + width/2, memoria_media, width, label='Uso Médio', color='#66b3ff')
    
    # Adicionar valores nas barras
    for bar in bars1:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{height:.2f}MB',
                 ha='center', va='bottom')
    
    for bar in bars2:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                 f'{height:.2f}MB',
                 ha='center', va='bottom')
    
    plt.title('Comparação de Uso de Memória')
    plt.ylabel('Memória (MiB)')
    plt.xticks(x, labels)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(RESULTS_DIR, 'graficos', 'uso_memoria.png'), dpi=300, bbox_inches='tight')
    
    # Gráfico de melhoria percentual
    labels = ['Sequencial', 'Paralelo', 'Cache']
    melhorias = [
        resultados_tempo['melhoria_sequencial'],
        resultados_tempo['melhoria_paralela'],
        resultados_tempo['melhoria_cache']
    ]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(labels, melhorias, color=['#66b3ff', '#99ff99', '#ffcc99'])
    
    # Adicionar valores nas barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                 f'{height:.2f}%',
                 ha='center', va='bottom')
    
    plt.title('Melhoria Percentual de Desempenho')
    plt.ylabel('Melhoria (%)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(RESULTS_DIR, 'graficos', 'melhoria_percentual.png'), dpi=300, bbox_inches='tight')
    
    print(f"Gráficos salvos em {os.path.join(RESULTS_DIR, 'graficos')}")

def benchmark_escalabilidade():
    """Testa a escalabilidade da versão otimizada com diferentes números de PDFs"""
    pdf_files = get_pdf_files()
    if not pdf_files:
        print("Nenhum arquivo PDF encontrado para benchmark")
        return
    
    # Duplicar a lista de PDFs para simular maior volume
    pdf_files_extended = pdf_files * 5  # 5x mais arquivos para teste de escalabilidade
    
    print(f"Executando benchmark de escalabilidade com até {len(pdf_files_extended)} arquivos PDF...")
    
    # Criar diretório temporário para saída
    temp_dir = tempfile.mkdtemp()
    
    # Testar com diferentes quantidades de PDFs
    quantidades = [1, 2, 5, 10, len(pdf_files_extended)]
    tempos_original = []
    tempos_paralelo = []
    
    for qtd in quantidades:
        if qtd > len(pdf_files_extended):
            break
            
        subset = pdf_files_extended[:qtd]
        
        # Versão original
        print(f"Testando versão original com {qtd} PDFs...")
        start_time = time.time()
        for pdf_file in subset:
            extrator_original.extrair_dados_pdf_relevantes(pdf_file, temp_dir)
        tempo_original = time.time() - start_time
        tempos_original.append(tempo_original)
        
        # Versão otimizada paralela
        print(f"Testando versão otimizada paralela com {qtd} PDFs...")
        start_time = time.time()
        extrator_otimizado.processar_pdfs_em_paralelo(subset, temp_dir)
        tempo_paralelo = time.time() - start_time
        tempos_paralelo.append(tempo_paralelo)
    
    # Salvar resultados
    resultados = {
        "quantidades": quantidades,
        "tempos_original": tempos_original,
        "tempos_paralelo": tempos_paralelo
    }
    
    with open(os.path.join(RESULTS_DIR, 'benchmark_escalabilidade.json'), 'w') as f:
        json.dump(resultados, f, indent=2)
    
    # Gerar gráfico de escalabilidade
    plt.figure(figsize=(10, 6))
    plt.plot(quantidades, tempos_original, 'o-', label='Original', color='#ff9999')
    plt.plot(quantidades, tempos_paralelo, 'o-', label='Otimizado Paralelo', color='#99ff99')
    plt.title('Escalabilidade: Tempo de Processamento vs. Número de PDFs')
    plt.xlabel('Número de PDFs')
    plt.ylabel('Tempo (segundos)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig(os.path.join(RESULTS_DIR, 'graficos', 'escalabilidade.png'), dpi=300, bbox_inches='tight')
    
    # Limpar arquivos temporários
    for file in os.listdir(temp_dir):
        if os.path.isdir(os.path.join(temp_dir, file)):
            # Se for o diretório de cache
            cache_dir = os.path.join(temp_dir, file)
            for cache_file in os.listdir(cache_dir):
                os.remove(os.path.join(cache_dir, cache_file))
            os.rmdir(cache_dir)
        else:
            os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)
    
    return resultados

if __name__ == "__main__":
    # Criar diretório para resultados
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    print("Iniciando benchmarks comparativos...")
    
    # Executar benchmarks
    resultados_tempo = benchmark_tempo_execucao()
    resultados_memoria = benchmark_memoria()
    benchmark_escalabilidade()
    
    # Gerar gráficos
    if resultados_tempo and resultados_memoria:
        gerar_graficos(resultados_tempo, resultados_memoria)
    
    print("\nBenchmarks concluídos. Resultados salvos em:", RESULTS_DIR)

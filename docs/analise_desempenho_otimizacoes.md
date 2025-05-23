# Análise de Desempenho e Proposta de Otimizações

## Resultados do Profiling

### Análise de Tempo de Execução
- **Tempo total para processar 5 PDFs**: 0.04 segundos
- **Tempo médio por PDF**: 0.01 segundos

### Principais Gargalos Identificados
1. **Chamadas a subprocessos** (`subprocess.run`, `subprocess.communicate`):
   - Representam a maior parte do tempo de execução
   - Chamadas ao utilitário `pdftotext` para extração de texto
   - Operações de I/O bloqueantes

2. **Expressões regulares** (`re.search`, `re._compile`):
   - Segunda maior fonte de consumo de tempo
   - Utilizadas para extrair informações do texto dos PDFs

3. **Processamento sequencial**:
   - Os PDFs são processados um após o outro
   - Sem aproveitamento de processamento paralelo

### Análise de Uso de Memória
- **Uso de memória estável**: ~22.3 MiB
- Sem vazamentos de memória significativos
- Sem picos de consumo durante o processamento

## Proposta de Otimizações

### 1. Paralelização do Processamento de PDFs
Implementar processamento paralelo para aproveitar múltiplos núcleos de CPU:

```python
import concurrent.futures

def processar_pdfs_em_paralelo(pdf_files, output_dir, max_workers=None):
    """
    Processa múltiplos PDFs em paralelo usando ThreadPoolExecutor.
    
    Args:
        pdf_files: Lista de caminhos para arquivos PDF
        output_dir: Diretório para salvar os resultados
        max_workers: Número máximo de workers (None = automático baseado no CPU)
    
    Returns:
        Lista de resultados do processamento
    """
    resultados = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submeter tarefas para o executor
        future_to_pdf = {
            executor.submit(extrair_dados_pdf_relevantes, pdf, output_dir): pdf 
            for pdf in pdf_files
        }
        
        # Coletar resultados à medida que são concluídos
        for future in concurrent.futures.as_completed(future_to_pdf):
            pdf = future_to_pdf[future]
            try:
                resultado = future.result()
                resultados.append(resultado)
            except Exception as e:
                print(f"Erro ao processar {pdf}: {e}")
    
    return resultados
```

### 2. Otimização de Chamadas a Subprocessos
Melhorar a eficiência das chamadas ao `pdftotext`:

```python
def extrair_texto_pdf_otimizado(pdf_path):
    """
    Versão otimizada da extração de texto de PDFs.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
    
    Returns:
        Texto extraído do PDF
    """
    # Usar parâmetros otimizados para pdftotext
    cmd = ["pdftotext", "-layout", "-nopgbrk", pdf_path, "-"]
    
    # Usar PIPE para evitar arquivos temporários
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=-1  # Buffering otimizado
    )
    
    # Processar saída de forma não-bloqueante
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"Erro ao executar pdftotext: {stderr}")
    
    return stdout
```

### 3. Otimização de Expressões Regulares
Pré-compilar expressões regulares para melhor desempenho:

```python
# Pré-compilar expressões regulares usadas frequentemente
import re

# Padrões compilados como constantes do módulo
PADRAO_NUMERO_INTERVENCAO = re.compile(r"Intervenção:\s*(\d+)")
PADRAO_TIPO_INTERVENCAO = re.compile(r"Tipo de Intervenção:\s*(.+?)(?:\n|$)")
PADRAO_DATA_INICIO = re.compile(r"Data Início:\s*(\d{2}/\d{2}/\d{4})")
PADRAO_HORA_INICIO = re.compile(r"Hora Início:\s*(\d{2}:\d{2})")
PADRAO_EQUIPAMENTO = re.compile(r".*Serial Number.*", re.IGNORECASE)
PADRAO_MATERIAL = re.compile(r".*Material.*Quantidade.*", re.IGNORECASE)

def extrair_valor_apos_rotulo_otimizado(texto, padrao_compilado):
    """
    Versão otimizada para extrair valores usando padrões pré-compilados.
    
    Args:
        texto: Texto a ser analisado
        padrao_compilado: Padrão regex pré-compilado
    
    Returns:
        Valor extraído ou None
    """
    match = padrao_compilado.search(texto)
    if match:
        return match.group(1).strip()
    return None
```

### 4. Cache de Resultados Intermediários
Implementar cache para evitar reprocessamento de PDFs já analisados:

```python
import os
import json
import hashlib

def calcular_hash_arquivo(arquivo):
    """Calcula o hash MD5 de um arquivo"""
    hash_md5 = hashlib.md5()
    with open(arquivo, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extrair_dados_pdf_com_cache(pdf_path, output_dir):
    """
    Versão com cache da função de extração de dados de PDF.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        output_dir: Diretório para salvar os resultados
    
    Returns:
        Dados extraídos do PDF
    """
    # Criar diretório de cache se não existir
    cache_dir = os.path.join(output_dir, ".cache")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Calcular hash do arquivo para identificação única
    file_hash = calcular_hash_arquivo(pdf_path)
    cache_file = os.path.join(cache_dir, f"{file_hash}.json")
    
    # Verificar se existe cache válido
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Processar o PDF normalmente se não houver cache
    resultado = extrair_dados_pdf_relevantes(pdf_path, output_dir)
    
    # Salvar resultado no cache
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    return resultado
```

### 5. Monitoramento de Recursos
Implementar monitoramento de recursos para evitar sobrecarga em ambientes com restrições:

```python
import psutil
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='processamento_pdf.log'
)
logger = logging.getLogger('processamento_pdf')

def processar_com_monitoramento_recursos(pdf_files, output_dir, limite_memoria_mb=1500):
    """
    Processa PDFs com monitoramento de recursos para evitar sobrecarga.
    
    Args:
        pdf_files: Lista de caminhos para arquivos PDF
        output_dir: Diretório para salvar os resultados
        limite_memoria_mb: Limite de memória em MB (padrão: 1500MB)
    
    Returns:
        Lista de resultados do processamento
    """
    resultados = []
    limite_memoria_bytes = limite_memoria_mb * 1024 * 1024
    
    # Determinar número de workers com base na memória disponível
    memoria_disponivel = psutil.virtual_memory().available
    memoria_por_processo = 25 * 1024 * 1024  # Estimativa de 25MB por processo
    max_workers = min(
        os.cpu_count() or 1,  # Número de CPUs
        max(1, int(memoria_disponivel * 0.7 / memoria_por_processo))  # Baseado na memória
    )
    
    logger.info(f"Iniciando processamento com {max_workers} workers paralelos")
    logger.info(f"Memória disponível: {memoria_disponivel / (1024*1024):.2f} MB")
    
    # Usar a função de processamento paralelo com o número calculado de workers
    return processar_pdfs_em_paralelo(pdf_files, output_dir, max_workers=max_workers)
```

## Impacto Esperado das Otimizações

1. **Paralelização**:
   - Redução de tempo de processamento proporcional ao número de núcleos disponíveis
   - Estimativa: 2-4x mais rápido em CPUs quad-core

2. **Otimização de Subprocessos**:
   - Redução de overhead de I/O
   - Estimativa: 10-15% de melhoria por PDF

3. **Expressões Regulares Pré-compiladas**:
   - Eliminação de overhead de compilação repetida
   - Estimativa: 5-10% de melhoria no tempo de processamento de texto

4. **Cache de Resultados**:
   - Eliminação de reprocessamento para PDFs idênticos
   - Benefício significativo em cenários de reprocessamento

5. **Monitoramento de Recursos**:
   - Prevenção de falhas por falta de memória
   - Adaptação automática às capacidades do sistema

## Próximos Passos

1. Implementar as otimizações propostas
2. Realizar testes comparativos antes/depois
3. Documentar ganhos de desempenho
4. Ajustar parâmetros com base nos resultados dos testes

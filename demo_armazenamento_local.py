"""
🧪 DEMONSTRAÇÃO: Sistema de Armazenamento Local
================================================

Este script demonstra EXATAMENTE como o sistema funciona:
1. Cria pasta temp_media
2. Simula recebimento de imagem base64
3. Salva no disco
4. Lê do disco
5. Lista arquivos
6. Remove arquivo (limpeza)
"""

import os
import base64
from datetime import datetime
import time

# Cores para terminal (Windows)
class Color:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_step(step, message):
    """Imprime passo com formatação"""
    print(f"\n{Color.BOLD}{Color.BLUE}[PASSO {step}]{Color.END} {message}")

def print_success(message):
    """Imprime sucesso"""
    print(f"{Color.GREEN}✅ {message}{Color.END}")

def print_info(message):
    """Imprime informação"""
    print(f"{Color.YELLOW}ℹ️  {message}{Color.END}")

def print_error(message):
    """Imprime erro"""
    print(f"{Color.RED}❌ {message}{Color.END}")

# ============= SIMULAÇÃO DO SISTEMA =============

print("\n" + "="*60)
print(f"{Color.BOLD}🧪 DEMONSTRAÇÃO: Sistema de Armazenamento Local{Color.END}")
print("="*60)

# PASSO 1: Criar pasta temp_media
print_step(1, "Criando pasta temp_media/")

TEMP_DIR = "temp_media"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)
    print_success(f"Pasta criada: {os.path.abspath(TEMP_DIR)}")
else:
    print_info(f"Pasta já existe: {os.path.abspath(TEMP_DIR)}")

# PASSO 2: Simular recebimento de imagem (pequena imagem 1x1 pixel em base64)
print_step(2, "Simulando recebimento de imagem do WhatsApp")

# Esta é uma imagem JPEG válida de 1x1 pixel (vermelha)
fake_image_base64 = (
    "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8U"
    "HRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgN"
    "DRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy"
    "MjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAU"
    "EAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAA"
    "AAAAAAAAAAAAAAAAAAAB/9oADAMBAAIRAxEAPwCwAB//2Q=="
)

print_info(f"Base64 recebido: {len(fake_image_base64)} caracteres")
print_info(f"Primeiros 50 chars: {fake_image_base64[:50]}...")

# PASSO 3: Salvar no disco (como o bot faz)
print_step(3, "Salvando imagem no disco (como save_media_from_base64)")

# Simular user_id
user_id = "558199887766"
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"prescription_{user_id}_{timestamp}.jpg"
filepath = os.path.join(TEMP_DIR, filename)

# Decodificar base64 → bytes
image_bytes = base64.b64decode(fake_image_base64)
print_info(f"Decodificado: {len(image_bytes)} bytes")

# Salvar no disco
with open(filepath, 'wb') as f:
    f.write(image_bytes)

print_success(f"Arquivo salvo: {filepath}")
print_info(f"Tamanho no disco: {os.path.getsize(filepath)} bytes")

# PASSO 4: Verificar que arquivo existe fisicamente
print_step(4, "Verificando que arquivo existe FISICAMENTE no disco")

if os.path.exists(filepath):
    print_success(f"Arquivo confirmado no disco!")
    print_info(f"Caminho absoluto: {os.path.abspath(filepath)}")
    
    # Obter detalhes do arquivo
    file_stats = os.stat(filepath)
    creation_time = datetime.fromtimestamp(file_stats.st_ctime)
    print_info(f"Criado em: {creation_time.strftime('%d/%m/%Y às %H:%M:%S')}")
else:
    print_error("Arquivo NÃO foi criado!")

# PASSO 5: Listar TODOS os arquivos na pasta
print_step(5, "Listando TODOS os arquivos em temp_media/")

files = os.listdir(TEMP_DIR)
if files:
    print_success(f"Encontrados {len(files)} arquivo(s):")
    for idx, file in enumerate(files, 1):
        file_path = os.path.join(TEMP_DIR, file)
        size = os.path.getsize(file_path)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"   {idx}. {file}")
        print(f"      Tamanho: {size} bytes")
        print(f"      Modificado: {mtime.strftime('%d/%m/%Y %H:%M:%S')}")
else:
    print_info("Pasta vazia")

# PASSO 6: Ler arquivo do disco (como bot faz para enviar ao grupo)
print_step(6, "Lendo arquivo do disco (como send_customer_form_to_group)")

with open(filepath, 'rb') as f:
    read_bytes = f.read()

print_success(f"Arquivo lido: {len(read_bytes)} bytes")

# Converter de volta para base64 (para enviar via API)
read_base64 = base64.b64encode(read_bytes).decode('utf-8')
print_info(f"Convertido para base64: {len(read_base64)} caracteres")
print_info(f"Base64 original == Base64 lido? {fake_image_base64 == read_base64}")

# PASSO 7: Demonstrar limpeza (opcional)
print_step(7, "Demonstrando limpeza automática")

print_info("Em produção, arquivos com mais de 24h seriam removidos")
print_info("Para demonstração, vou aguardar 2 segundos e 'envelhecer' o arquivo...")

time.sleep(2)

# Simular verificação de idade
file_age_seconds = time.time() - os.path.getmtime(filepath)
print_info(f"Idade do arquivo: {file_age_seconds:.2f} segundos")

# Demonstrar remoção
response = input("\n🗑️  Deseja REMOVER o arquivo de demonstração? (S/N): ")
if response.lower() in ['s', 'sim', 'y', 'yes']:
    os.remove(filepath)
    print_success(f"Arquivo removido: {filename}")
    
    # Verificar remoção
    if not os.path.exists(filepath):
        print_success("Arquivo NÃO existe mais no disco!")
    
    # Listar novamente
    remaining = os.listdir(TEMP_DIR)
    print_info(f"Arquivos restantes em temp_media/: {len(remaining)}")
else:
    print_info("Arquivo mantido no disco para inspeção")
    print_info(f"Você pode visualizá-lo em: {os.path.abspath(filepath)}")

# RESUMO FINAL
print("\n" + "="*60)
print(f"{Color.BOLD}📊 RESUMO{Color.END}")
print("="*60)
print(f"""
✅ Pasta criada: {os.path.abspath(TEMP_DIR)}
✅ Arquivo salvo: {filename}
✅ Base64 → Disco → Base64 (ciclo completo)
✅ Sistema funciona 100% LOCAL (sem internet/cloud)

{Color.YELLOW}💡 DICA:{Color.END} Abra o Explorador do Windows e navegue até:
   {os.path.abspath(TEMP_DIR)}
   
   Você verá os arquivos fisicamente salvos no seu disco!
""")

print("="*60)
print(f"{Color.GREEN}✅ Demonstração concluída!{Color.END}\n")

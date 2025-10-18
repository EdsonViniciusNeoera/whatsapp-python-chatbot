"""
Sistema de Notificação via Grupo de WhatsApp - GGDISK Ótica
Envia notificações para grupo com Jailson e Josimar quando clientes solicitam atendimento.
"""

import os
import re
import time
from datetime import datetime
from dotenv import load_dotenv
from wasenderapi import create_sync_wasender

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
WASENDER_API_TOKEN = os.getenv('WASENDER_API_TOKEN')
NOTIFICATION_GROUP_ID = os.getenv('NOTIFICATION_GROUP_ID')  # ID do grupo (formato: 120363xxxxx@g.us)
LOG_FILE = 'whatsapp_bot.log'

# Palavras-chave que disparam notificação
KEYWORDS = [
    'orçamento',
    'agendar',
    'exame',
    'consultor',
    'jailson',
    'josimar',
    'ajuste',
    'reparo',
    'falar com',
    'atendente'
]

print("=" * 60)
print("  Sistema de Notificação via Grupo - GGDISK Ótica")
print("=" * 60)
print(f"Grupo ID: {NOTIFICATION_GROUP_ID}")
print(f"Palavras-chave: {', '.join(KEYWORDS)}")
print(f"Monitorando: {LOG_FILE}")
print("=" * 60)

# Inicializar cliente WaSender
try:
    wasender = create_sync_wasender(api_key=WASENDER_API_TOKEN)
    print("✅ WaSender conectado!\n")
except Exception as e:
    print(f"❌ Erro ao conectar WaSender: {e}")
    exit(1)

def extrair_numero_cliente(linha):
    """Extrai número do cliente da linha de log."""
    # Procura por padrões de número de telefone
    match = re.search(r'(\d{12,13})@s\.whatsapp\.net', linha)
    if match:
        return match.group(1)
    
    match = re.search(r'from (\d{12,13})', linha)
    if match:
        return match.group(1)
    
    return None

def extrair_mensagem(linha):
    """Extrai a mensagem do cliente da linha de log."""
    # Procura por padrões de mensagem no log
    match = re.search(r"message: '(.+?)'", linha)
    if match:
        return match.group(1)
    
    match = re.search(r'Processing text message: \'(.+?)\' from', linha)
    if match:
        return match.group(1)
    
    return None

def deve_notificar(linha):
    """Verifica se a linha contém palavras-chave para notificação."""
    linha_lower = linha.lower()
    return any(keyword in linha_lower for keyword in KEYWORDS)

def enviar_notificacao_grupo(numero_cliente, mensagem):
    """Envia notificação para o grupo."""
    if not NOTIFICATION_GROUP_ID:
        print("⚠️  NOTIFICATION_GROUP_ID não configurado no .env")
        return False
    
    timestamp = datetime.now().strftime('%d/%m/%Y às %H:%M')
    
    notificacao = f"""🔔 *NOVA SOLICITAÇÃO DE ATENDIMENTO*

👤 *Cliente:* {numero_cliente}
⏰ *Horário:* {timestamp}

📝 *Mensagem:*
{mensagem}

---
_Atender o cliente iniciando conversa com o número dele_"""
    
    try:
        wasender.send_text(
            to=NOTIFICATION_GROUP_ID,
            text_body=notificacao
        )
        print(f"✅ Notificação enviada ao grupo!")
        print(f"   Cliente: {numero_cliente}")
        print(f"   Mensagem: {mensagem[:50]}...\n")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar notificação: {e}\n")
        return False

def monitorar_log():
    """Monitora o arquivo de log em tempo real."""
    print("🔍 Iniciando monitoramento do log...\n")
    
    # Vai para o final do arquivo
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        f.seek(0, 2)  # Vai para o final
        
        while True:
            linha = f.readline()
            
            if not linha:
                time.sleep(0.5)  # Aguarda novas linhas
                continue
            
            # Verifica se deve notificar
            if deve_notificar(linha):
                numero = extrair_numero_cliente(linha)
                mensagem = extrair_mensagem(linha)
                
                if numero and mensagem:
                    print(f"🎯 Detectado: {mensagem[:50]}... de {numero}")
                    enviar_notificacao_grupo(numero, mensagem)

if __name__ == '__main__':
    try:
        monitorar_log()
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitoramento interrompido pelo usuário.")
    except FileNotFoundError:
        print(f"\n❌ Arquivo {LOG_FILE} não encontrado!")
        print("   Certifique-se de que o bot está rodando e gerando logs.")
    except Exception as e:
        print(f"\n❌ Erro: {e}")

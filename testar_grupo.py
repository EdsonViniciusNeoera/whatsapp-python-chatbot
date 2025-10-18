"""
Teste rápido do sistema de notificação via grupo
"""

from wasenderapi import create_sync_wasender
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

print("=" * 60)
print("  TESTE DE NOTIFICAÇÃO PARA GRUPO")
print("=" * 60)
print()

# Verificar configurações
WASENDER_API_TOKEN = os.getenv('WASENDER_API_TOKEN')
NOTIFICATION_GROUP_ID = os.getenv('NOTIFICATION_GROUP_ID')

print("✓ Verificando configurações...")
print(f"  Token API: {'✅ Configurado' if WASENDER_API_TOKEN else '❌ Não configurado'}")
print(f"  Grupo ID: {NOTIFICATION_GROUP_ID if NOTIFICATION_GROUP_ID else '❌ Não configurado'}")
print()

if not WASENDER_API_TOKEN:
    print("❌ Configure WASENDER_API_TOKEN no .env primeiro!")
    exit(1)

if not NOTIFICATION_GROUP_ID:
    print("❌ Configure NOTIFICATION_GROUP_ID no .env primeiro!")
    print()
    print("Passos:")
    print("1. Crie um grupo no WhatsApp")
    print("2. Execute: python pegar_id_grupo.py")
    print("3. Adicione o ID no .env")
    exit(1)

# Conectar ao WaSender
try:
    print("✓ Conectando ao WaSenderAPI...")
    client = create_sync_wasender(api_key=WASENDER_API_TOKEN)
    print("  ✅ Conectado!\n")
except Exception as e:
    print(f"  ❌ Erro: {e}")
    exit(1)

# Enviar mensagem de teste
print("✓ Enviando mensagem de teste para o grupo...")
print()

mensagem_teste = f"""🧪 *TESTE DE NOTIFICAÇÃO*

Este é um teste do sistema de notificação.

⏰ Horário: {datetime.now().strftime('%d/%m/%Y às %H:%M')}

Se você recebeu esta mensagem, o sistema está funcionando! ✅"""

try:
    client.send_text(
        to=NOTIFICATION_GROUP_ID,
        text_body=mensagem_teste
    )
    print("✅ Mensagem de teste enviada com sucesso!")
    print()
    print("Verifique o grupo 'GGDISK - Notificações' no WhatsApp.")
    print()
    print("Se a mensagem chegou, o sistema está funcionando! 🎉")
    print()
    print("Próximo passo:")
    print("  Execute: python grupo_notificador.py")
    print()
    
except Exception as e:
    print(f"❌ Erro ao enviar mensagem: {e}")
    print()
    print("Possíveis causas:")
    print("  1. ID do grupo incorreto (deve terminar com @g.us)")
    print("  2. Bot não está no grupo")
    print("  3. Problema com a API do WaSender")
    print()

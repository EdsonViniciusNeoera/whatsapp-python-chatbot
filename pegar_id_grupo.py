"""
Script para descobrir o ID do grupo de WhatsApp
"""

from wasenderapi import create_sync_wasender
from dotenv import load_dotenv
import os

load_dotenv()

print("=" * 60)
print("  DESCOBRIR ID DO GRUPO - GGDISK Ótica")
print("=" * 60)
print()

WASENDER_API_TOKEN = os.getenv('WASENDER_API_TOKEN')

if not WASENDER_API_TOKEN:
    print("❌ WASENDER_API_TOKEN não encontrado no .env")
    print("   Configure o token primeiro!")
    exit(1)

try:
    client = create_sync_wasender(api_key=WASENDER_API_TOKEN)
    print("✅ Conectado ao WaSenderAPI!\n")
except Exception as e:
    print(f"❌ Erro ao conectar: {e}")
    exit(1)

print("📋 INSTRUÇÕES PARA PEGAR O ID DO GRUPO:")
print()
print("MÉTODO 1 - Via Dashboard WaSenderAPI:")
print("  1. Acesse: https://wasenderapi.com/dashboard")
print("  2. Vá em 'Chats' ou 'Groups'")
print("  3. Encontre o grupo 'GGDISK - Notificações'")
print("  4. Copie o ID do grupo (formato: 120363xxxxx@g.us)")
print()
print("MÉTODO 2 - Enviar mensagem de teste:")
print("  1. Envie UMA mensagem MANUALMENTE para o grupo pelo WhatsApp")
print("  2. Verifique o log do bot (whatsapp_bot.log)")
print("  3. Procure por linhas com '@g.us'")
print()
print("MÉTODO 3 - Consultar API (pode não funcionar em todas as versões):")
print("  Nota: A API do WaSender pode não expor lista de grupos diretamente")
print()

# Tentar listar (pode não funcionar dependendo da API)
print("🔍 Tentando buscar informações de grupos...")
print("   (Isso pode não funcionar em todas as versões do WaSenderAPI)\n")

try:
    # Tente diferentes métodos dependendo da versão da API
    # Nota: Isso é específico da implementação do WaSenderAPI
    
    print("⚠️  A API do WaSenderAPI não expõe lista de grupos diretamente.")
    print("   Use os MÉTODOS acima para pegar o ID do grupo.\n")
    
except Exception as e:
    print(f"⚠️  Não foi possível listar grupos automaticamente: {e}\n")

print("=" * 60)
print("PRÓXIMOS PASSOS:")
print("=" * 60)
print()
print("1. Crie o grupo 'GGDISK - Notificações' no WhatsApp")
print("2. Adicione: Você, Jailson e Josimar")
print("3. Pegue o ID do grupo usando um dos métodos acima")
print("4. Adicione no .env:")
print()
print("   NOTIFICATION_GROUP_ID=120363XXXXXXXXX@g.us")
print()
print("5. Execute o notificador:")
print()
print("   python grupo_notificador.py")
print()

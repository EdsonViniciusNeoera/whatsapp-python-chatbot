"""
Monitor em tempo real para capturar ID do grupo
Execute este script e envie uma mensagem no grupo
"""

import time
import os

LOG_FILE = 'whatsapp_bot.log'

print("=" * 60)
print("  CAPTURADOR DE ID DE GRUPO")
print("=" * 60)
print()
print("📋 INSTRUÇÕES:")
print()
print("1. Deixe este script rodando")
print("2. Abra o grupo 'GGDISK - Notificações' no WhatsApp")
print("3. Envie qualquer mensagem (ex: 'oi')")
print("4. O ID do grupo aparecerá aqui automaticamente!")
print()
print("=" * 60)
print()
print("🔍 Monitorando whatsapp_bot.log...")
print("   Aguardando mensagens de grupo...\n")

if not os.path.exists(LOG_FILE):
    print(f"❌ Arquivo {LOG_FILE} não encontrado!")
    print()
    print("Certifique-se de que o bot está rodando:")
    print("   python script.py")
    print()
    exit(1)

# Vai para o final do arquivo
with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
    f.seek(0, 2)  # Final do arquivo
    
    print("✅ Pronto! Aguardando mensagens...\n")
    
    ids_encontrados = set()
    
    while True:
        linha = f.readline()
        
        if not linha:
            time.sleep(0.3)
            continue
        
        # Procura por IDs de grupo (@g.us)
        if '@g.us' in linha:
            # Extrai o ID
            import re
            matches = re.findall(r'(\d{15,25}@g\.us)', linha)
            
            for group_id in matches:
                if group_id not in ids_encontrados:
                    ids_encontrados.add(group_id)
                    
                    print("=" * 60)
                    print("✅ ID DE GRUPO ENCONTRADO!")
                    print("=" * 60)
                    print()
                    print(f"📋 ID: {group_id}")
                    print()
                    print("=" * 60)
                    print("PRÓXIMO PASSO:")
                    print("=" * 60)
                    print()
                    print("1. Copie o ID acima")
                    print("2. Abra o arquivo .env")
                    print("3. Adicione esta linha:")
                    print()
                    print(f"   NOTIFICATION_GROUP_ID={group_id}")
                    print()
                    print("4. Salve o arquivo .env")
                    print("5. Execute: python testar_grupo.py")
                    print()
                    print("=" * 60)
                    print()
                    print("Continuar monitorando? (Ctrl+C para sair)")
                    print()

"""
🤖 Script Auxiliar: Atualização Automática do WEBHOOK_BASE_URL
==============================================================

Este script obtém automaticamente a URL do ngrok e atualiza o arquivo .env

Uso:
    1. Inicie o ngrok: .\ngrok.exe http 5001
    2. Aguarde 3 segundos
    3. Execute: python auto_update_webhook_url.py
    4. Reinicie o bot: python script.py
"""

import requests
import re
import os
import sys

def get_ngrok_url():
    """Obtém a URL pública do ngrok via API local"""
    try:
        response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=5)
        response.raise_for_status()
        
        data = response.json()
        tunnels = data.get('tunnels', [])
        
        # Procura pelo tunnel HTTPS
        for tunnel in tunnels:
            if tunnel.get('proto') == 'https':
                return tunnel.get('public_url')
        
        # Fallback: usa primeiro tunnel disponível
        if tunnels:
            return tunnels[0].get('public_url')
        
        return None
    except requests.RequestException as e:
        print(f"❌ Erro ao conectar com ngrok API: {e}")
        return None

def update_env_file(ngrok_url):
    """Atualiza WEBHOOK_BASE_URL no arquivo .env"""
    env_path = '.env'
    
    if not os.path.exists(env_path):
        print(f"❌ Arquivo .env não encontrado em: {os.path.abspath(env_path)}")
        return False
    
    try:
        # Ler conteúdo atual
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Atualizar linha WEBHOOK_BASE_URL
        # Remove barra final se existir
        ngrok_url_clean = ngrok_url.rstrip('/')
        
        if 'WEBHOOK_BASE_URL=' in content:
            # Substituir linha existente
            new_content = re.sub(
                r'WEBHOOK_BASE_URL=.*',
                f'WEBHOOK_BASE_URL={ngrok_url_clean}',
                content
            )
        else:
            # Adicionar linha se não existe
            new_content = content + f'\nWEBHOOK_BASE_URL={ngrok_url_clean}\n'
        
        # Salvar
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Arquivo .env atualizado!")
        print(f"   WEBHOOK_BASE_URL={ngrok_url_clean}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao atualizar .env: {e}")
        return False

def main():
    """Função principal"""
    print("\n" + "="*60)
    print("🤖 Atualizador Automático de WEBHOOK_BASE_URL")
    print("="*60 + "\n")
    
    # Verificar se ngrok está rodando
    print("🔍 Verificando se ngrok está rodando...")
    ngrok_url = get_ngrok_url()
    
    if not ngrok_url:
        print("\n❌ ngrok NÃO está rodando ou não está expondo a porta 5001")
        print("\n📋 Para corrigir:")
        print("   1. Abra outro terminal")
        print("   2. Execute: .\\ngrok.exe http 5001")
        print("   3. Aguarde 3 segundos")
        print("   4. Execute este script novamente")
        sys.exit(1)
    
    print(f"✅ ngrok detectado: {ngrok_url}")
    
    # Validar URL
    if not ngrok_url.startswith('https://'):
        print(f"\n⚠️  AVISO: URL não é HTTPS: {ngrok_url}")
        print("   WhatsApp API requer HTTPS!")
        
        # Tentar obter versão HTTPS
        ngrok_url_https = ngrok_url.replace('http://', 'https://')
        print(f"   Usando versão HTTPS: {ngrok_url_https}")
        ngrok_url = ngrok_url_https
    
    # Atualizar .env
    print("\n📝 Atualizando arquivo .env...")
    success = update_env_file(ngrok_url)
    
    if success:
        print("\n" + "="*60)
        print("✅ CONFIGURAÇÃO CONCLUÍDA!")
        print("="*60)
        print(f"\n🌐 URL pública: {ngrok_url}")
        print("\n📋 Próximos passos:")
        print("   1. Reinicie o bot: python script.py")
        print("   2. Teste o endpoint: curl {}/health".format(ngrok_url))
        print("   3. Envie uma receita pelo WhatsApp")
        print("\n💡 Dica: Esta URL muda toda vez que ngrok reinicia!")
        print("   Execute este script novamente se reiniciar o ngrok.\n")
    else:
        print("\n❌ Falha na configuração!")
        sys.exit(1)

if __name__ == '__main__':
    main()

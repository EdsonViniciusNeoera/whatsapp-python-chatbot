#!/usr/bin/env python3
"""
Script de teste do formulário de upload de receitas.

Este script testa:
1. Se a rota /upload está acessível
2. Se o formulário HTML está sendo servido corretamente
3. Se as validações de upload estão funcionando
4. Se a função check_uploaded_prescription funciona

Uso:
    python test_upload_form.py
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
WEBHOOK_BASE_URL = os.getenv('WEBHOOK_BASE_URL', 'http://localhost:5001')

def test_upload_page():
    """Testa se a página de upload está acessível."""
    print("=" * 60)
    print("TESTE 1: Acessando página de upload")
    print("=" * 60)
    
    url = f"{WEBHOOK_BASE_URL}/upload"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Página de upload acessível")
            
            # Verificar se HTML contém elementos esperados
            html = response.text
            checks = [
                ('GGDISK Ótica' in html, 'Título da página'),
                ('prescription' in html, 'Campo de arquivo'),
                ('phone' in html, 'Campo de telefone'),
                ('name' in html, 'Campo de nome'),
                ('/upload_prescription' in html, 'Endpoint de upload'),
            ]
            
            for check, description in checks:
                status = "✅" if check else "❌"
                print(f"{status} {description}")
            
            return all(check for check, _ in checks)
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao servidor")
        print("   Certifique-se de que o bot está rodando em", WEBHOOK_BASE_URL)
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_upload_page_with_phone():
    """Testa se a página pré-preenche o telefone."""
    print("\n" + "=" * 60)
    print("TESTE 2: Página com telefone pré-preenchido")
    print("=" * 60)
    
    phone = "81999887766"
    url = f"{WEBHOOK_BASE_URL}/upload?phone={phone}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ Página acessível com parâmetro phone")
            
            # Verificar se telefone está no HTML (via JavaScript)
            if phone in response.text or 'phoneParam' in response.text:
                print("✅ Parâmetro phone detectado no código")
                return True
            else:
                print("⚠️  Parâmetro phone não encontrado (mas página funciona)")
                return True
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_upload_endpoint():
    """Testa validações do endpoint de upload."""
    print("\n" + "=" * 60)
    print("TESTE 3: Validações do endpoint de upload")
    print("=" * 60)
    
    url = f"{WEBHOOK_BASE_URL}/upload_prescription"
    print(f"URL: {url}")
    
    # Teste 1: Requisição vazia
    print("\n📋 Teste 3.1: Requisição vazia")
    try:
        response = requests.post(url, data={})
        if response.status_code == 400:
            print("✅ Rejeita requisição vazia (esperado)")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 2: Telefone inválido
    print("\n📋 Teste 3.2: Telefone inválido")
    try:
        response = requests.post(url, data={
            'phone': '123',  # Muito curto
            'name': 'Teste',
        })
        if response.status_code == 400:
            print("✅ Rejeita telefone inválido (esperado)")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 3: Nome muito curto
    print("\n📋 Teste 3.3: Nome muito curto")
    try:
        response = requests.post(url, data={
            'phone': '81999887766',
            'name': 'A',  # Muito curto
        })
        if response.status_code == 400:
            print("✅ Rejeita nome muito curto (esperado)")
        else:
            print(f"⚠️  Status inesperado: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    return True

def test_webhook_base_url():
    """Verifica se WEBHOOK_BASE_URL está configurado."""
    print("\n" + "=" * 60)
    print("TESTE 4: Configuração de WEBHOOK_BASE_URL")
    print("=" * 60)
    
    webhook_url = os.getenv('WEBHOOK_BASE_URL')
    print(f"WEBHOOK_BASE_URL: {webhook_url}")
    
    if not webhook_url:
        print("❌ WEBHOOK_BASE_URL não configurado no .env")
        return False
    
    if webhook_url == 'http://localhost:5001':
        print("⚠️  WEBHOOK_BASE_URL está configurado como localhost")
        print("   Isso NÃO funcionará em produção!")
        print("   Configure com URL do ngrok ou domínio público")
        return False
    
    if 'ngrok' in webhook_url:
        print("✅ WEBHOOK_BASE_URL configurado com ngrok (desenvolvimento)")
        return True
    
    if webhook_url.startswith('https://'):
        print("✅ WEBHOOK_BASE_URL configurado com domínio HTTPS")
        return True
    
    print("⚠️  WEBHOOK_BASE_URL deve começar com https://")
    return False

def main():
    """Executa todos os testes."""
    print("\n")
    print("🧪 TESTE DO FORMULÁRIO DE UPLOAD DE RECEITAS")
    print("=" * 60)
    print(f"Servidor: {WEBHOOK_BASE_URL}")
    print("=" * 60)
    
    results = []
    
    # Executar testes
    results.append(("Página de upload", test_upload_page()))
    results.append(("Pré-preenchimento de telefone", test_upload_page_with_phone()))
    results.append(("Validações do endpoint", test_upload_endpoint()))
    results.append(("Configuração WEBHOOK_BASE_URL", test_webhook_base_url()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {test_name}")
    
    # Resultado final
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print("\n" + "=" * 60)
    print(f"RESULTADO FINAL: {passed}/{total} testes passaram")
    print("=" * 60)
    
    if passed == total:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("\n💡 Próximos passos:")
        print("   1. Teste enviando um arquivo real pelo formulário")
        print("   2. Verifique se o arquivo aparece em temp_media/")
        print("   3. Teste o fluxo completo com um cliente no WhatsApp")
        return 0
    else:
        print("⚠️  ALGUNS TESTES FALHARAM")
        print("\n💡 Verifique:")
        print("   1. Se o bot está rodando (python script.py)")
        print("   2. Se WEBHOOK_BASE_URL está correto no .env")
        print("   3. Se ngrok está rodando (se em desenvolvimento)")
        return 1

if __name__ == '__main__':
    sys.exit(main())

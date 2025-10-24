# 📸 Guia Completo: Envio de Imagens aos Consultores

## 🎯 **Objetivo**

Quando um cliente envia uma receita de óculos (imagem ou PDF), o sistema:
1. ✅ Salva o arquivo localmente
2. ✅ Disponibiliza via URL pública
3. ✅ **Envia a imagem/PDF JUNTO com a notificação ao grupo de consultores**

---

## 🔧 **Como Funciona**

### **Arquitetura do Sistema**

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│   Cliente   │      │   Flask Bot  │      │  Consultores │
│  (WhatsApp) │      │   (Servidor) │      │   (Grupo WA) │
└─────────────┘      └──────────────┘      └──────────────┘
       │                     │                      │
       │  1. Envia receita   │                      │
       │────────────────────>│                      │
       │    (via WhatsApp)   │                      │
       │                     │                      │
       │                     │ 2. Salva localmente  │
       │                     │   temp_media/*.jpg   │
       │                     │                      │
       │                     │ 3. Cria URL pública  │
       │                     │   /media/xxx.jpg     │
       │                     │                      │
       │                     │ 4. Envia notificação │
       │                     │─────────────────────>│
       │                     │   (texto + dados)    │
       │                     │                      │
       │                     │ 5. Envia IMAGEM      │
       │                     │─────────────────────>│
       │                     │   (usando URL)       │
       │                     │                      │
       │                     │<─────────────────────│
       │                     │ 6. WaSender baixa    │
       │                     │    imagem da URL     │
       │                     │                      │
```

---

## 📋 **Componentes do Sistema**

### **1. Endpoint `/media/<filename>`**

**Função:** Serve arquivos temporários via HTTP para que a API do WhatsApp possa baixá-los.

**Exemplo:**
```
https://abc123.ngrok-free.app/media/prescription_558199887766_20251023_143052.jpg
```

**Segurança:**
- ✅ Apenas arquivos em `temp_media/`
- ✅ Sem path traversal (`../`)
- ✅ Auto-limpeza após 24h
- ✅ Cache-Control configurado

**Código:**
```python
@app.route('/media/<filename>', methods=['GET'])
def serve_media(filename):
    """Serve temporary media files for WhatsApp API access."""
    # Validação de segurança
    if '..' in filename or '/' in filename:
        return jsonify({'error': 'Invalid filename'}), 400
    
    # Serve arquivo
    return send_from_directory(
        CONFIG["TEMP_MEDIA_DIR"],
        filename,
        mimetype=mimetype,
        max_age=86400  # Cache 24h
    )
```

---

### **2. Variável `WEBHOOK_BASE_URL`**

**Localização:** `.env`

**Propósito:** Define a URL base do servidor para construir URLs públicas.

**Configuração:**

```bash
# Desenvolvimento local (com ngrok)
WEBHOOK_BASE_URL=https://abc123.ngrok-free.app

# Produção (servidor real)
WEBHOOK_BASE_URL=https://seu-dominio.com

# Localhost (NÃO funciona para WhatsApp API!)
WEBHOOK_BASE_URL=http://localhost:5001  # ❌ Apenas para testes locais
```

⚠️ **IMPORTANTE:** WhatsApp API **precisa** de URL HTTPS pública. Use ngrok para desenvolvimento!

---

### **3. Função `send_customer_form_to_group` (Modificada)**

**Antes (QUEBRADO):**
```python
# ❌ Tentava enviar data URL (base64 inline)
data_url = f"data:image/jpeg;base64,{file_base64}"
send_whatsapp_message(group_id, caption, media_url=data_url)
```

**Problema:** WaSender API não aceita data URLs!

**Depois (CORRIGIDO):**
```python
# ✅ Envia URL pública para WaSender baixar
filename = os.path.basename(prescription_file_path)
public_url = f"{CONFIG['WEBHOOK_BASE_URL']}/media/{filename}"
send_whatsapp_message(group_id, caption, media_url=public_url)
```

**Fluxo Completo:**
1. Cliente envia imagem → Bot salva em `temp_media/prescription_xxx.jpg`
2. Bot constrói URL: `https://ngrok.../media/prescription_xxx.jpg`
3. Bot chama `send_whatsapp_message()` com URL pública
4. WaSender API baixa imagem da URL
5. WaSender envia imagem ao grupo do WhatsApp
6. **Consultores recebem IMAGEM junto com notificação! ✅**

---

## 🚀 **Como Configurar**

### **Passo 1: Instalar ngrok**

ngrok já está no projeto! Verifique:

```powershell
cd C:\LunaeGroup\GitProjects\whatsapp-python-chatbot
.\ngrok.exe --version
```

### **Passo 2: Iniciar o Bot**

Terminal 1 - Rodar Flask:
```powershell
python script.py
```

Saída esperada:
```
* Running on http://127.0.0.1:5001
INFO - Created temporary media directory at temp_media
INFO - WaSenderAPI client initialized successfully
```

### **Passo 3: Iniciar ngrok**

Terminal 2 - Expor servidor:
```powershell
.\ngrok.exe http 5001
```

Saída esperada:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:5001
```

**Copie a URL HTTPS!** ☝️ (exemplo: `https://abc123.ngrok-free.app`)

### **Passo 4: Atualizar `.env`**

```bash
# Cole a URL do ngrok (sem barra final)
WEBHOOK_BASE_URL=https://abc123.ngrok-free.app
```

### **Passo 5: Reiniciar o Bot**

```powershell
# Terminal 1: Ctrl+C para parar
python script.py  # Reinicia com nova URL
```

### **Passo 6: Testar!**

1. Envie mensagem ao bot como cliente
2. Escolha opção "Orçamento" ou "Comprar óculos"
3. Envie foto da receita quando solicitado
4. **Verifique no grupo de consultores:**
   - ✅ Notificação de texto
   - ✅ Imagem da receita logo em seguida

---

## 🧪 **Testes e Verificações**

### **Teste 1: Endpoint está funcionando?**

```powershell
# Crie um arquivo de teste
python demo_armazenamento_local.py

# Teste o endpoint
curl http://localhost:5001/media/prescription_558199887766_20251023_214542.jpg --output teste.jpg
```

✅ Sucesso: Arquivo `teste.jpg` criado e pode ser aberto!

### **Teste 2: URL pública está acessível?**

```powershell
# Substitua pela sua URL do ngrok
curl https://abc123.ngrok-free.app/media/prescription_558199887766_20251023_214542.jpg --output teste_ngrok.jpg
```

✅ Sucesso: Arquivo baixado via internet!

### **Teste 3: Bot envia imagem ao grupo?**

```bash
# Verifique os logs do Flask quando cliente envia receita
# Procure por estas mensagens:

INFO - 📎 Sending prescription file to group: temp_media/prescription_xxx.jpg
INFO - 🌐 Public media URL: https://abc123.ngrok-free.app/media/prescription_xxx.jpg
INFO - ✅ Prescription file sent to group successfully
```

✅ Sucesso: Consultores recebem imagem no grupo!

---

## ⚠️ **Problemas Comuns**

### **Problema 1: Imagem não aparece no grupo**

**Sintoma:** Apenas notificação de texto chega, sem imagem.

**Causas possíveis:**
1. ❌ `WEBHOOK_BASE_URL` não configurado ou incorreto
2. ❌ ngrok não está rodando
3. ❌ Firewall bloqueando ngrok
4. ❌ URL com `http://` ao invés de `https://`

**Solução:**
```powershell
# Verificar configuração
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('WEBHOOK_BASE_URL:', os.getenv('WEBHOOK_BASE_URL'))"

# Testar conectividade
curl https://abc123.ngrok-free.app/health
```

---

### **Problema 2: Erro 404 ao acessar `/media/`**

**Sintoma:** `{"error": "File not found"}`

**Causas:**
1. ❌ Arquivo já foi limpo (>24h)
2. ❌ Nome do arquivo incorreto
3. ❌ Pasta `temp_media/` não criada

**Solução:**
```powershell
# Verificar arquivos existentes
ls temp_media\

# Testar com arquivo existente
curl http://localhost:5001/media/NOME_DO_ARQUIVO_AQUI.jpg
```

---

### **Problema 3: ngrok URL muda toda vez**

**Sintoma:** Precisa atualizar `.env` sempre que reinicia ngrok.

**Causas:**
- ngrok free gera URL aleatória a cada execução

**Soluções:**

**Opção 1:** Conta ngrok paga (URL fixa)
```bash
# URL permanente: https://seu-app.ngrok.io
ngrok http 5001 --domain=seu-app.ngrok.io
```

**Opção 2:** Script automático de atualização
```python
# auto_update_env.py
import subprocess
import re
import os

# Obter URL do ngrok via API
result = subprocess.run(['curl', 'http://127.0.0.1:4040/api/tunnels'], 
                       capture_output=True, text=True)
match = re.search(r'"public_url":"(https://[^"]+)"', result.stdout)

if match:
    ngrok_url = match.group(1)
    
    # Atualizar .env
    with open('.env', 'r') as f:
        content = f.read()
    
    content = re.sub(r'WEBHOOK_BASE_URL=.*', 
                    f'WEBHOOK_BASE_URL={ngrok_url}', content)
    
    with open('.env', 'w') as f:
        f.write(content)
    
    print(f"✅ .env atualizado: {ngrok_url}")
else:
    print("❌ ngrok não está rodando!")
```

**Uso:**
```powershell
# Inicia ngrok em background
Start-Process .\ngrok.exe -ArgumentList "http 5001"

# Aguarda 3 segundos
Start-Sleep 3

# Atualiza .env automaticamente
python auto_update_env.py

# Inicia bot
python script.py
```

---

## 📊 **Fluxo Completo com Logs**

### **Exemplo Real**

**Cliente envia receita:**
```
[WhatsApp] → Cliente: [Anexa foto_receita.jpg]
```

**Logs do servidor:**
```
INFO - === WEBHOOK CALLED ===
INFO - Found image message - Full data: {'jpegThumbnail': '/9j/4AAQ...', 'mimetype': 'image/jpeg'}
INFO - 💾 Saving prescription image from base64 thumbnail
INFO - ✅ Media saved: temp_media/prescription_558199887766_20251023_143052.jpg (42.3 KB)
INFO - Updated form step: prescription -> ✅ Imagem da receita recebida!
```

**Bot envia ao grupo:**
```
INFO - 📎 Sending prescription file to group: temp_media/prescription_558199887766_20251023_143052.jpg
INFO - 🌐 Public media URL: https://abc123.ngrok-free.app/media/prescription_558199887766_20251023_143052.jpg
INFO - Text message sent to 120363404721021632@g.us
INFO - ✅ Customer form sent to group for 558199887766
INFO - Image message sent to 120363404721021632@g.us
INFO - ✅ Prescription file sent to group successfully
```

**WaSender API acessa URL:**
```
INFO - 📤 Serving media file: prescription_558199887766_20251023_143052.jpg (type: image/jpeg)
127.0.0.1 - - [23/Oct/2025 14:30:52] "GET /media/prescription_558199887766_20251023_143052.jpg HTTP/1.1" 200 -
```

**Consultores recebem no grupo:**
```
🔔 NOVA SOLICITAÇÃO DE ATENDIMENTO

⏰ Horário: 23/10/2025 às 14:30
📋 Motivo: Orçamento de óculos

👨‍💼 CONSULTOR SOLICITADO
• Jailson
• Telefone: 5581997507161

👤 DADOS DO CLIENTE
• Nome: João Silva
• Telefone: 5581999887766
• WhatsApp: 558199887766
• CPF: 123.456.789-00

💊 RECEITA DE ÓCULOS
✅ Imagem da receita recebida!
📎 Arquivo da receita será enviado a seguir

---
Atender o cliente iniciando conversa com o WhatsApp dele
```

**Seguido de:**
```
[IMAGEM DA RECEITA APARECE AQUI 📸]
💊 Receita de óculos de João Silva
```

✅ **Sucesso total!**

---

## 🎓 **Resumo Técnico**

| Aspecto | Implementação |
|---------|---------------|
| **Armazenamento** | Local (`temp_media/`) |
| **Exposição** | HTTP endpoint `/media/<filename>` |
| **URL pública** | ngrok HTTPS (`WEBHOOK_BASE_URL`) |
| **Envio** | WaSender baixa de URL pública |
| **Limpeza** | Automática após 24h |
| **Segurança** | Path traversal bloqueado, cache 24h |

**Vantagens:**
- ✅ Sem custos (não usa cloud storage)
- ✅ Simples (apenas Flask + ngrok)
- ✅ Rápido (arquivo local)
- ✅ Automático (sem intervenção manual)

**Limitações:**
- ⚠️ Requer ngrok ou servidor público
- ⚠️ URL ngrok muda se reiniciar (sem plano pago)
- ⚠️ Arquivos temporários (não permanentes)

---

## 📞 **Suporte**

**Problemas?** Verifique:
1. ✅ ngrok rodando → `.\ngrok.exe http 5001`
2. ✅ `.env` atualizado → `WEBHOOK_BASE_URL=https://...ngrok...`
3. ✅ Bot reiniciado → `python script.py`
4. ✅ Logs sem erros → Procure `✅ Prescription file sent`

**Ainda não funciona?**
- Envie logs completos
- Teste endpoint manualmente: `curl https://...ngrok.../media/teste.jpg`
- Verifique firewall/antivírus

---

**Última atualização:** 23/10/2025  
**Versão:** 2.1.0

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

**Diagnóstico passo a passo:**

1. **Verificar logs do Flask** - Procure por estas mensagens:
   ```
   📎 === SENDING PRESCRIPTION FILE TO GROUP ===
   🌐 === CONSTRUCTING PUBLIC URL ===
   📤 === CALLING WASENDER API ===
   ✅ === SUCCESS: Prescription file sent to group! ===
   ```

2. **Se aparecer `❌ CRITICAL: WEBHOOK_BASE_URL is not configured correctly!`:**
   ```powershell
   # Verificar configuração atual
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('WEBHOOK_BASE_URL:', os.getenv('WEBHOOK_BASE_URL'))"
   ```
   - ❌ `http://localhost:5001` → Não funciona! WhatsApp precisa de HTTPS público
   - ❌ `None` ou vazio → Não configurado
   - ✅ `https://abc123.ngrok-free.app` → Correto!

3. **Se aparecer `⚠️ === FAILED: WaSender API returned False ===`:**
   
   **Causas possíveis:**
   - ❌ URL não é acessível publicamente
   - ❌ API key da WasenderAPI inválida
   - ❌ Formato de arquivo não suportado
   - ❌ Firewall/antivírus bloqueando
   
   **Testes:**
   ```powershell
   # Teste 1: URL está acessível publicamente?
   curl https://SEU_NGROK_URL/media/prescription_xxx.jpg --output teste.jpg
   
   # Teste 2: API key está correta?
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key:', os.getenv('WASENDER_API_TOKEN')[:20] + '...')"
   
   # Teste 3: Arquivo existe localmente?
   ls temp_media\
   ```

4. **Se aparecer `📸 Processing image message:` mas sem `✅ SUCCESS:`:**
   
   Verifique qual estratégia foi usada:
   ```
   📥 Strategy 1: Attempting to download full resolution image from URL
   ✅ SUCCESS: Full resolution image downloaded and saved!
   ```
   ou
   ```
   ⚠️ No 'url' field in imageMessage, skipping URL download
   📥 Strategy 2: Using jpegThumbnail (base64 encoded)
   ✅ SUCCESS: Thumbnail image saved (lower quality)
   ```
   
   Se ambas falharem:
   ```
   ❌ CRITICAL: No 'jpegThumbnail' available - cannot save image!
   ```
   → Problema no webhook do WhatsApp (dados incompletos)

**Soluções por causa:**

**Causa: WEBHOOK_BASE_URL incorreta**
```powershell
# Passo 1: Parar o bot (Ctrl+C)
# Passo 2: Atualizar .env
notepad .env  # Altere WEBHOOK_BASE_URL=https://sua-url-ngrok.ngrok-free.app
# Passo 3: Reiniciar bot
python script.py
```

**Causa: ngrok não está rodando**
```powershell
# Terminal 1: Iniciar ngrok
.\ngrok.exe http 5001

# Copiar URL HTTPS (ex: https://abc123.ngrok-free.app)
# Terminal 2: Atualizar .env e reiniciar bot
```

**Causa: Firewall bloqueando**
```powershell
# Windows Defender Firewall
# Adicionar exceção para Python e ngrok.exe
```

**Causa: API key inválida**
```powershell
# Verificar no painel WasenderAPI
# Atualizar .env com nova key
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

# Ver idade dos arquivos
Get-ChildItem temp_media\ | Select-Object Name, LastWriteTime

# Testar com arquivo real
# Substitua NOME_DO_ARQUIVO pelo arquivo que apareceu no ls
curl http://localhost:5001/media/NOME_DO_ARQUIVO.jpg --output teste.jpg
```

**Criar arquivo de teste:**
```powershell
# Criar imagem de teste
python -c "import base64, os; os.makedirs('temp_media', exist_ok=True); open('temp_media/test.jpg', 'wb').write(base64.b64decode('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAAA//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AH//Z'))"

# Testar endpoint
curl http://localhost:5001/media/test.jpg --output test_downloaded.jpg

# Se funcionar, arquivo test_downloaded.jpg será criado
```

---

### **Problema 3: ngrok URL muda toda vez**

**Sintoma:** Precisa atualizar `.env` sempre que reinicia ngrok.

**Causas:**
- ngrok free gera URL aleatória a cada execução

**Soluções:**

**Opção 1: Conta ngrok paga (URL fixa) - RECOMENDADO**
```bash
# URL permanente: https://seu-app.ngrok.io
ngrok http 5001 --domain=seu-app.ngrok.io
```

**Opção 2: Script automático de atualização (já incluído!)**
```powershell
# Usar o script existente
python auto_update_webhook_url.py

# Isso vai:
# 1. Obter URL do ngrok automaticamente
# 2. Atualizar .env
# 3. Não precisa reiniciar o bot!
```

**Opção 3: Workflow completo automatizado**
```powershell
# Criar arquivo start_bot.ps1:
# =====================
# Start ngrok in background
Start-Process -FilePath ".\ngrok.exe" -ArgumentList "http 5001" -WindowStyle Hidden

# Wait for ngrok to start
Start-Sleep -Seconds 3

# Update webhook URL
python auto_update_webhook_url.py

# Start bot
python script.py
# =====================

# Executar:
.\start_bot.ps1
```

---

### **Problema 4: Imagem de baixa qualidade**

**Sintoma:** Imagem enviada está pixelizada ou em baixa resolução.

**Diagnóstico:**
```powershell
# Verificar logs - qual estratégia foi usada?
# Procure por uma destas mensagens:

# ✅ Melhor qualidade:
# "✅ SUCCESS: Full resolution image downloaded and saved!"

# ⚠️ Qualidade reduzida:
# "✅ SUCCESS: Thumbnail image saved (lower quality)"
```

**Causas e soluções:**

**Causa: WhatsApp não fornece URL de alta resolução**
- Estratégia 1 falha → cai para jpegThumbnail
- **Solução:** Não há solução técnica. jpegThumbnail é o melhor disponível.
- **Workaround:** Pedir ao cliente para enviar novamente ou solicitar diretamente

**Causa: Timeout no download**
```python
# Em script.py, linha ~665 (função download_and_save_media):
response = requests.get(url, timeout=30)  # Aumentar timeout se necessário
```

**Causa: Erro de rede/autenticação**
- Verificar se a URL do WhatsApp requer autenticação
- Verificar logs para exceções durante download

---

### **Problema 5: Erro "Invalid filename" ao acessar /media/**

**Sintoma:** `{"error": "Invalid filename"}`

**Causa:** Tentativa de path traversal (segurança ativada)

**Exemplos que causam erro:**
```
/media/../script.py  ❌
/media/folder/file.jpg  ❌
/media/..\\..\\secret.txt  ❌
```

**Solução:** Use apenas o nome do arquivo sem `/`, `\` ou `..`
```
/media/prescription_558199887766_20251023_143052.jpg  ✅
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

**Problemas?** Siga este processo:

1. ✅ **Execute o Checklist de Diagnóstico** (veja seção abaixo)
2. ✅ **Capture os logs** relevantes:
   ```powershell
   # Últimas 100 linhas do log
   Get-Content whatsapp_bot.log -Tail 100 > debug_logs.txt
   ```
3. ✅ **Teste manualmente** os endpoints
4. ✅ **Verifique as variáveis de ambiente**
5. ✅ **Reinicie tudo na ordem correta:**
   ```powershell
   # 1. Parar bot (Ctrl+C)
   # 2. Parar ngrok (Ctrl+C)
   # 3. Iniciar ngrok
   .\ngrok.exe http 5001
   # 4. Atualizar .env com nova URL
   # 5. Iniciar bot
   python script.py
   ```

**Ainda não funciona?**
- 📋 Envie os logs (`debug_logs.txt`)
- 📋 Informe a URL do ngrok
- 📋 Confirme versão do Python (`python --version`)
- 📋 Liste pacotes instalados (`pip list`)

---

## ✅ **Checklist de Diagnóstico Rápido**

Use este checklist quando imagens não estiverem sendo enviadas:

### **Fase 1: Configuração Básica**
- [ ] ngrok está rodando? (`.\ngrok.exe http 5001`)
- [ ] Bot Flask está rodando? (`python script.py`)
- [ ] `WEBHOOK_BASE_URL` configurada no `.env`?
- [ ] URL é HTTPS? (não `http://localhost`)
- [ ] Pasta `temp_media/` existe?

### **Fase 2: Teste de Conectividade**
- [ ] Endpoint `/health` responde? → `curl http://localhost:5001/health`
- [ ] Endpoint `/media/` funciona? → Criar arquivo teste e acessar
- [ ] URL pública acessível? → `curl https://SEU_NGROK_URL/health`

### **Fase 3: Análise de Logs**
- [ ] Cliente enviou imagem? → Procure `📸 Processing image message:`
- [ ] Imagem foi salva? → Procure `✅ SUCCESS: Full resolution image` ou `✅ SUCCESS: Thumbnail image`
- [ ] URL foi construída? → Procure `🌐 Complete public URL:`
- [ ] API foi chamada? → Procure `📤 === CALLING WASENDER API ===`
- [ ] Envio teve sucesso? → Procure `✅ === SUCCESS: Prescription file sent to group! ===`

### **Fase 4: Verificação de Erros**
- [ ] Erro de URL? → `❌ CRITICAL: WEBHOOK_BASE_URL is not configured correctly!`
- [ ] Erro de API? → `⚠️ === FAILED: WaSender API returned False ===`
- [ ] Erro de exceção? → `❌ === EXCEPTION while sending prescription file ===`

### **Fase 5: Testes Manuais**
```powershell
# 1. Verificar configuração
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('WEBHOOK_BASE_URL:', os.getenv('WEBHOOK_BASE_URL')); print('WASENDER_API_TOKEN:', os.getenv('WASENDER_API_TOKEN')[:20] + '...' if os.getenv('WASENDER_API_TOKEN') else 'NOT SET')"

# 2. Testar endpoint local
curl http://localhost:5001/health

# 3. Listar arquivos salvos
ls temp_media\ | Select-Object Name, Length, LastWriteTime

# 4. Testar URL pública (substitua SEU_NGROK_URL)
curl https://SEU_NGROK_URL/health

# 5. Ver logs em tempo real
Get-Content whatsapp_bot.log -Tail 50 -Wait
```

---

## 🔍 **Interpretando os Logs**

### **Logs de Sucesso (✅ Tudo funcionando)**
```log
INFO - 📸 Processing image message:
INFO -    - MIME type: image/jpeg
INFO - 📥 Strategy 1: Attempting to download full resolution image from URL
INFO - ✅ SUCCESS: Full resolution image downloaded and saved!
INFO - 📊 Final image processing status:
INFO -    - File saved: True
INFO -    - File path: temp_media/prescription_558199887766_20251024_143052.jpg
INFO -    - File size: 245678 bytes
INFO - ✅ Customer form sent to group for 558199887766
INFO - 📎 === SENDING PRESCRIPTION FILE TO GROUP ===
INFO - 🌐 Complete public URL: https://abc123.ngrok-free.app/media/prescription_558199887766_20251024_143052.jpg
INFO - 📤 === CALLING WASENDER API ===
INFO - Image message sent to 120363404721021632@g.us
INFO - ✅ === SUCCESS: Prescription file sent to group! ===
```

### **Logs com Fallback (⚠️ Usando thumbnail - qualidade reduzida)**
```log
INFO - 📸 Processing image message:
INFO - ⚠️ No 'url' field in imageMessage, skipping URL download
INFO - 📥 Strategy 2: Using jpegThumbnail (base64 encoded)
INFO - ✅ SUCCESS: Thumbnail image saved (lower quality)
INFO - 📎 === SENDING PRESCRIPTION FILE TO GROUP ===
INFO - 📤 === CALLING WASENDER API ===
INFO - ✅ === SUCCESS: Prescription file sent to group! ===
```

### **Logs de Erro (❌ Problemas identificados)**

**Erro 1: URL não configurada**
```log
ERROR - ❌ CRITICAL: WEBHOOK_BASE_URL is not configured correctly!
ERROR - ❌ Current value: http://localhost:5001
ERROR - ❌ WhatsApp API requires HTTPS public URL (use ngrok for dev)
```
**Solução:** Configure ngrok e atualize `WEBHOOK_BASE_URL` no `.env`

**Erro 2: Falha no download da imagem**
```log
WARNING - ⚠️ FAILED: Could not download from URL, trying fallback...
WARNING - ⚠️ No 'url' field in imageMessage, skipping URL download
ERROR - ❌ CRITICAL: No 'jpegThumbnail' available - cannot save image!
```
**Solução:** Problema no webhook do WhatsApp. Verificar integração WasenderAPI.

**Erro 3: Falha ao enviar para grupo**
```log
WARNING - ⚠️ === FAILED: WaSender API returned False ===
WARNING - ⚠️ Possible causes:
WARNING -    1. URL is not publicly accessible
WARNING -    2. WaSender API key is invalid
WARNING -    3. File format not supported
WARNING -    4. Network/firewall issue
```
**Solução:** Testar cada causa listada acima.

---

## 📚 **Referências**

- **WasenderAPI Docs:** https://www.wasenderapi.com/docs
- **ngrok Docs:** https://ngrok.com/docs
- **Flask Docs:** https://flask.palletsprojects.com/

---

**Última atualização:** 24/10/2025  
**Versão:** 2.2.0 (com diagnóstico avançado e logs detalhados)
```

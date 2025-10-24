# 🧪 Teste Rápido: Sistema de Envio de Imagens

## ⚡ **Teste em 5 Minutos**

### **Passo 1: Iniciar o Sistema**

```powershell
# Terminal 1 - Iniciar ngrok
cd C:\LunaeGroup\GitProjects\whatsapp-python-chatbot
.\ngrok.exe http 5001
```

**Copie a URL HTTPS** que aparece (exemplo: `https://abc123.ngrok-free.app`)

```powershell
# Terminal 2 - Atualizar webhook e iniciar bot
cd C:\LunaeGroup\GitProjects\whatsapp-python-chatbot

# Opção A: Atualizar automaticamente (RECOMENDADO)
python auto_update_webhook_url.py

# Opção B: Atualizar manualmente
# Edite .env e cole a URL do ngrok em WEBHOOK_BASE_URL=

# Iniciar o bot
python script.py
```

---

### **Passo 2: Verificar Configuração**

```powershell
# Verificar se WEBHOOK_BASE_URL está configurada corretamente
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ WEBHOOK_BASE_URL:', os.getenv('WEBHOOK_BASE_URL'))"

# Deve mostrar algo como:
# ✅ WEBHOOK_BASE_URL: https://abc123.ngrok-free.app
```

**❌ Se mostrar `http://localhost:5001`:** Você precisa atualizar o `.env`!

---

### **Passo 3: Testar o Endpoint**

```powershell
# Testar endpoint local
curl http://localhost:5001/health

# Deve retornar JSON com status "ok"
```

---

### **Passo 4: Simular Envio de Cliente**

**Via WhatsApp:**
1. Envie uma mensagem ao bot: "Olá"
2. Escolha opção "2" (Fazer orçamento)
3. Escolha consultor: "01" ou "02"
4. Preencha os dados solicitados
5. **ENVIE UMA FOTO** quando solicitar receita

---

### **Passo 5: Verificar os Logs**

**O que procurar nos logs:**

✅ **SUCESSO - Todos estes devem aparecer:**
```log
INFO - 📸 Processing image message:
INFO - 📥 Strategy 1: Attempting to download full resolution image from URL
INFO - ✅ SUCCESS: Full resolution image downloaded and saved!
INFO - 📊 Final image processing status:
INFO -    - File saved: True
INFO - 📎 === SENDING PRESCRIPTION FILE TO GROUP ===
INFO - 🌐 Complete public URL: https://abc123.ngrok-free.app/media/prescription_xxx.jpg
INFO - 📤 === CALLING WASENDER API ===
INFO - ✅ === SUCCESS: Prescription file sent to group! ===
```

⚠️ **ALERTA - Imagem salva mas em baixa qualidade:**
```log
INFO - ⚠️ No 'url' field in imageMessage, skipping URL download
INFO - 📥 Strategy 2: Using jpegThumbnail (base64 encoded)
INFO - ✅ SUCCESS: Thumbnail image saved (lower quality)
```
**Motivo:** WhatsApp não forneceu URL de alta resolução  
**Resultado:** Imagem será enviada, mas em qualidade reduzida

❌ **ERRO - URL não configurada:**
```log
ERROR - ❌ CRITICAL: WEBHOOK_BASE_URL is not configured correctly!
ERROR - ❌ Current value: http://localhost:5001
```
**Solução:** Volte ao Passo 1 e configure o ngrok corretamente

❌ **ERRO - Falha ao enviar:**
```log
WARNING - ⚠️ === FAILED: WaSender API returned False ===
```
**Solução:** Veja seção de troubleshooting no `GUIA_ENVIO_IMAGENS.md`

---

## 🔍 **Comandos de Diagnóstico**

### **Ver logs em tempo real:**
```powershell
Get-Content whatsapp_bot.log -Tail 50 -Wait
```
Pressione `Ctrl+C` para parar.

### **Verificar arquivos salvos:**
```powershell
ls temp_media\ | Select-Object Name, Length, LastWriteTime
```

### **Testar endpoint /media/ manualmente:**
```powershell
# 1. Criar imagem de teste
python -c "import base64, os; os.makedirs('temp_media', exist_ok=True); open('temp_media/test.jpg', 'wb').write(base64.b64decode('/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAAA//EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AH//Z'))"

# 2. Testar acesso local
curl http://localhost:5001/media/test.jpg --output test_local.jpg

# 3. Testar acesso público (substitua SUA_URL_NGROK)
curl https://SUA_URL_NGROK/media/test.jpg --output test_public.jpg

# 4. Verificar se arquivos foram criados
ls *.jpg
```

Se ambos `test_local.jpg` e `test_public.jpg` foram criados → ✅ Endpoint funcionando!

---

## 📊 **Tabela de Resultados**

| Teste | Esperado | Comando |
|-------|----------|---------|
| ngrok rodando | URL HTTPS exibida | `.\ngrok.exe http 5001` |
| Bot rodando | "Running on http://127.0.0.1:5001" | `python script.py` |
| WEBHOOK_BASE_URL | URL HTTPS (não localhost) | `python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('WEBHOOK_BASE_URL'))"` |
| Endpoint /health | `{"status":"ok"}` | `curl http://localhost:5001/health` |
| Endpoint /media/ | Arquivo baixado | `curl http://localhost:5001/media/test.jpg -o test.jpg` |
| Pasta temp_media/ | Existe | `ls temp_media\` |
| Cliente envia foto | Imagem salva em temp_media/ | Verificar logs: `✅ SUCCESS` |
| Grupo recebe foto | Consultores veem imagem | Verificar grupo WhatsApp |

---

## ⚠️ **Problemas Comuns e Soluções Rápidas**

### **Problema: "No module named 'flask'"**
```powershell
# Ativar ambiente virtual
.\venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

### **Problema: ngrok não funciona**
```powershell
# Verificar se ngrok.exe existe
ls ngrok.exe

# Se não existir, baixar de: https://ngrok.com/download
```

### **Problema: URL do ngrok muda toda vez**
```powershell
# Usar script de auto-update
python auto_update_webhook_url.py

# Ou configurar ngrok auth token para URL fixa (plano pago)
```

### **Problema: Imagem não chega ao grupo**
**Checklist rápido:**
1. ✅ ngrok rodando?
2. ✅ Bot rodando?
3. ✅ WEBHOOK_BASE_URL = URL do ngrok?
4. ✅ Logs mostram `✅ SUCCESS`?

**Se todos sim mas ainda não funciona:**
- Verifique se `NOTIFICATION_GROUP_ID` está correto no `.env`
- Verifique se o bot está no grupo de consultores
- Teste enviar mensagem de texto para o grupo (deve funcionar)

---

## 📝 **Exemplo de Teste Completo**

```powershell
# ==== TERMINAL 1: ngrok ====
cd C:\LunaeGroup\GitProjects\whatsapp-python-chatbot
.\ngrok.exe http 5001
# Copiar URL: https://abc123.ngrok-free.app

# ==== TERMINAL 2: Bot ====
cd C:\LunaeGroup\GitProjects\whatsapp-python-chatbot

# Atualizar webhook
python auto_update_webhook_url.py

# Verificar configuração
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('WEBHOOK_BASE_URL:', os.getenv('WEBHOOK_BASE_URL'))"
# Deve mostrar: https://abc123.ngrok-free.app

# Iniciar bot
python script.py

# ==== TERMINAL 3: Monitorar logs ====
Get-Content whatsapp_bot.log -Tail 50 -Wait

# ==== WhatsApp: Enviar teste ====
# 1. "Olá" → Menu
# 2. "2" → Orçamento
# 3. "01" → Josimar
# 4. "João Silva" → Nome
# 5. "81999887766" → Telefone
# 6. "12345678900" → CPF
# 7. [ENVIAR FOTO] → Receita
# 8. "sim" → Confirmar

# ==== VERIFICAR: ====
# Logs (Terminal 3): Procurar "✅ === SUCCESS: Prescription file sent to group! ==="
# Grupo WhatsApp: Deve receber notificação + imagem
# Pasta temp_media\: ls temp_media\ (arquivo deve existir)
```

---

## ✅ **Critérios de Sucesso**

Teste está **APROVADO** se:
1. ✅ Bot recebe foto do cliente
2. ✅ Logs mostram `✅ SUCCESS: Full resolution image downloaded`
3. ✅ Arquivo salvo em `temp_media/prescription_*.jpg`
4. ✅ Logs mostram `✅ SUCCESS: Prescription file sent to group!`
5. ✅ **Consultores RECEBEM a imagem no grupo do WhatsApp**

Teste está **PARCIALMENTE APROVADO** se:
- ⚠️ Usa thumbnail (baixa qualidade) mas imagem chega ao grupo

Teste está **REPROVADO** se:
- ❌ Imagem não chega ao grupo
- ❌ Logs mostram erros críticos
- ❌ WEBHOOK_BASE_URL está `http://localhost:5001`

---

## 🎯 **Próximos Passos**

Após teste bem-sucedido:
1. Configure URL fixa no ngrok (plano pago) para produção
2. Configure servidor com domínio próprio (Heroku, AWS, Azure)
3. Adicione monitoramento de erros (Sentry, LogRocket)
4. Configure backup automático de `temp_media/`

---

**Boa sorte com os testes! 🚀**

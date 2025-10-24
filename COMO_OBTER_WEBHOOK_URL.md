# 🌐 Como Obter a URL do ngrok para WEBHOOK_BASE_URL

## 🎯 **O Que É?**

`WEBHOOK_BASE_URL` é a URL **pública** do seu servidor Flask que permite:
- ✅ WhatsApp API baixar imagens do endpoint `/media/`
- ✅ Consultores receberem as imagens de receitas
- ✅ Sistema funcionar fora do localhost

---

## 📋 **Pré-Requisitos**

- ✅ ngrok.exe no projeto (já está!)
- ✅ Porta 5001 disponível
- ✅ Conta ngrok (gratuita): https://ngrok.com

---

## 🚀 **MÉTODO 1: Automático (Recomendado)**

### **Passo a Passo**

#### **1. Abra 3 Terminais PowerShell**

```powershell
# Terminal 1: Diretório do projeto
cd C:\LunaeGroup\GitProjects\whatsapp-python-chatbot

# Terminal 2: Mesmo diretório
cd C:\LunaeGroup\GitProjects\whatsapp-python-chatbot

# Terminal 3: Mesmo diretório
cd C:\LunaeGroup\GitProjects\whatsapp-python-chatbot
```

---

#### **2. Terminal 1 - Iniciar ngrok**

```powershell
.\ngrok.exe http 5001
```

**Aguarde 3-5 segundos** até ver:

```
ngrok

Session Status                online
Account                       seu-email@example.com
Region                        South America (sa)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123-xyz.ngrok-free.app -> http://localhost:5001

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

☝️ **A linha "Forwarding" contém sua URL pública!**

---

#### **3. Terminal 2 - Atualizar .env automaticamente**

```powershell
python auto_update_webhook_url.py
```

**Saída esperada:**

```
============================================================
🤖 Atualizador Automático de WEBHOOK_BASE_URL
============================================================

🔍 Verificando se ngrok está rodando...
✅ ngrok detectado: https://abc123-xyz.ngrok-free.app

📝 Atualizando arquivo .env...
✅ Arquivo .env atualizado!
   WEBHOOK_BASE_URL=https://abc123-xyz.ngrok-free.app

============================================================
✅ CONFIGURAÇÃO CONCLUÍDA!
============================================================

🌐 URL pública: https://abc123-xyz.ngrok-free.app

📋 Próximos passos:
   1. Reinicie o bot: python script.py
   2. Teste o endpoint: curl https://abc123-xyz.ngrok-free.app/health
   3. Envie uma receita pelo WhatsApp

💡 Dica: Esta URL muda toda vez que ngrok reinicia!
   Execute este script novamente se reiniciar o ngrok.
```

---

#### **4. Terminal 3 - Reiniciar o Bot**

```powershell
python script.py
```

**Verifique nos logs:**

```
INFO - WEBHOOK_BASE_URL: https://abc123-xyz.ngrok-free.app ✅
INFO - Temporary media endpoint: /media/<filename> ✅
INFO - WaSenderAPI client initialized successfully
 * Running on http://127.0.0.1:5001
```

✅ **Pronto! Agora envie uma receita pelo WhatsApp para testar!**

---

## 🛠️ **MÉTODO 2: Manual**

### **Passo a Passo**

#### **1. Iniciar ngrok**

```powershell
.\ngrok.exe http 5001
```

#### **2. Copiar a URL HTTPS**

Na tela do ngrok, procure a linha:

```
Forwarding    https://abc123-xyz.ngrok-free.app -> http://localhost:5001
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     COPIE ESTA PARTE!
```

**Exemplo:** `https://abc123-xyz.ngrok-free.app`

⚠️ **ATENÇÃO:**
- ✅ Use a URL que começa com `https://` (não `http://`)
- ✅ NÃO copie a parte `-> http://localhost:5001`
- ✅ NÃO adicione barra final (`/`)

#### **3. Editar .env**

Abra o arquivo `.env` e localize:

```env
WEBHOOK_BASE_URL=http://localhost:5001
```

Substitua pela URL do ngrok:

```env
WEBHOOK_BASE_URL=https://abc123-xyz.ngrok-free.app
```

**Salve o arquivo!**

#### **4. Reiniciar o Bot**

```powershell
python script.py
```

---

## 🧪 **Verificar Se Está Funcionando**

### **Teste 1: Endpoint está acessível?**

```powershell
# Substitua pela SUA URL
curl https://abc123-xyz.ngrok-free.app/health
```

**Resposta esperada:**

```json
{
  "status": "ok",
  "wasender_client": true,
  "gemini_client": true
}
```

---

### **Teste 2: Endpoint /media/ funciona?**

```powershell
# Crie arquivo de teste
python demo_armazenamento_local.py

# Teste via ngrok (substitua pela SUA URL)
curl https://abc123-xyz.ngrok-free.app/media/prescription_558199887766_20251023_214542.jpg -o teste_ngrok.jpg

# Abra a imagem
start teste_ngrok.jpg
```

✅ **Sucesso:** Imagem baixada e abre normalmente!

---

### **Teste 3: Bot envia imagem ao grupo?**

1. Envie mensagem ao bot como cliente
2. Escolha "Orçamento de óculos"
3. Envie foto da receita quando solicitado

**Logs esperados:**

```
INFO - 💾 Saving prescription image from base64 thumbnail
INFO - ✅ Media saved: temp_media/prescription_xxx.jpg
INFO - 📎 Sending prescription file to group
INFO - 🌐 Public media URL: https://abc123-xyz.ngrok-free.app/media/prescription_xxx.jpg
INFO - ✅ Prescription file sent to group successfully
INFO - 📤 Serving media file: prescription_xxx.jpg (type: image/jpeg)
```

**No grupo:**
```
🔔 NOVA SOLICITAÇÃO
👤 João Silva
💊 Receita: ✅ Recebida

[📸 IMAGEM APARECE AQUI] ✅
```

---

## 🎨 **Visualização da Tela do ngrok**

Quando você executar `.\ngrok.exe http 5001`, verá algo assim:

```
┌───────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  ngrok                                                                │
│                                                                       │
│  Session Status                online                                │
│  Account                       seu-email@example.com                 │
│  Version                       3.3.0                                 │
│  Region                        South America (sa)                    │
│  Latency                       45ms                                  │
│  Web Interface                 http://127.0.0.1:4040                 │
│                                                                       │
│  Forwarding                    https://abc123-xyz.ngrok-free.app ->  │
│                                http://localhost:5001                 │
│                                                                       │
│  Connections                   ttl     opn     rt1     rt5     p50   │
│                                0       0       0.00    0.00    0.00  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

A URL pública é: **`https://abc123-xyz.ngrok-free.app`**

---

## ⚠️ **Problemas Comuns**

### **Problema 1: "ngrok not found"**

**Solução:**
```powershell
# Verifique se ngrok.exe está no diretório
ls ngrok.exe

# Se não estiver, baixe de: https://ngrok.com/download
```

---

### **Problema 2: "Connection refused"**

**Causa:** Bot não está rodando na porta 5001

**Solução:**
```powershell
# Terminal separado:
python script.py

# Aguarde ver:
# * Running on http://127.0.0.1:5001
```

---

### **Problema 3: URL muda toda vez**

**Causa:** ngrok gratuito gera URL aleatória a cada execução

**Soluções:**

**Opção 1:** Plano pago do ngrok (URL fixa)
```bash
ngrok http 5001 --domain=seu-app.ngrok.io
```

**Opção 2:** Executar `python auto_update_webhook_url.py` toda vez que reiniciar ngrok

**Opção 3:** Usar servidor real (produção)
```bash
# Em produção, use seu domínio real:
WEBHOOK_BASE_URL=https://seu-dominio.com
```

---

### **Problema 4: "Tunnel not found" no script automático**

**Causa:** ngrok não foi iniciado ou ainda não terminou de conectar

**Solução:**
```powershell
# 1. Verifique se ngrok está rodando
# 2. Aguarde 5 segundos após iniciar ngrok
# 3. Execute o script novamente:
python auto_update_webhook_url.py
```

---

## 📱 **Interface Web do ngrok**

O ngrok também oferece uma interface web em:

```
http://127.0.0.1:4040
```

Abra no navegador para ver:
- ✅ URL pública atual
- ✅ Requisições em tempo real
- ✅ Status da conexão
- ✅ Histórico de requisições

---

## 🎯 **Quick Start (Resumo)**

```powershell
# Terminal 1: ngrok
.\ngrok.exe http 5001

# Terminal 2: Atualizar .env
python auto_update_webhook_url.py

# Terminal 3: Bot
python script.py

# ✅ PRONTO!
```

---

## 🔄 **Fluxo Completo com URLs**

```
Cliente WhatsApp
       ↓
WaSender API
       ↓
https://abc123.ngrok-free.app/webhook  (seu bot recebe mensagem)
       ↓
Bot salva imagem em: temp_media/prescription_xxx.jpg
       ↓
Bot envia ao grupo: https://abc123.ngrok-free.app/media/prescription_xxx.jpg
       ↓
WaSender API baixa de: https://abc123.ngrok-free.app/media/prescription_xxx.jpg
       ↓
Consultores recebem IMAGEM ✅
```

---

## 💡 **Dicas Importantes**

1. **Sempre use HTTPS** (não HTTP)
   ```bash
   ✅ WEBHOOK_BASE_URL=https://abc123.ngrok-free.app
   ❌ WEBHOOK_BASE_URL=http://abc123.ngrok-free.app
   ```

2. **Não adicione barra final**
   ```bash
   ✅ WEBHOOK_BASE_URL=https://abc123.ngrok-free.app
   ❌ WEBHOOK_BASE_URL=https://abc123.ngrok-free.app/
   ```

3. **Reinicie o bot após mudar .env**
   ```bash
   # Ctrl+C para parar
   python script.py  # Reinicia
   ```

4. **URL muda ao reiniciar ngrok**
   - Execute `python auto_update_webhook_url.py` novamente
   - Reinicie o bot

5. **Mantenha ngrok rodando**
   - Não feche o terminal do ngrok
   - Se fechar, precisa reiniciar e atualizar URL

---

## 📚 **Recursos Adicionais**

- 📖 [Documentação do ngrok](https://ngrok.com/docs)
- 🎥 [Tutorial em vídeo](https://ngrok.com/docs/getting-started)
- 💬 [Comunidade ngrok](https://ngrok.com/slack)

---

## ✅ **Checklist Final**

Antes de testar:

- [ ] ngrok rodando (`.\ngrok.exe http 5001`)
- [ ] URL copiada/detectada
- [ ] `.env` atualizado com URL HTTPS
- [ ] Bot reiniciado
- [ ] Logs mostram URL pública correta
- [ ] Endpoint `/health` acessível
- [ ] Pronto para testar receita!

---

**Última atualização:** 23/10/2025  
**Versão:** 2.1.0  
**Status:** ✅ Funcionando

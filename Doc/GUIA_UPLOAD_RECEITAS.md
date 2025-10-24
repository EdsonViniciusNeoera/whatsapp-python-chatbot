# 📸 Guia de Upload de Receitas - Formulário Externo

## 🎯 Objetivo

Este sistema resolve a limitação de **criptografia do WaSender API** que impede o download direto de imagens enviadas pelos clientes via WhatsApp. Agora os clientes podem enviar suas receitas através de um **formulário web seguro**.

---

## 🔧 Como Funciona

### Fluxo do Cliente:

1. **Cliente conversa com o bot** e solicita orçamento de óculos
2. **Bot coleta dados** (nome, telefone, CPF)
3. **Bot pergunta sobre receita**
4. Se cliente tem receita → **Bot envia link do formulário**
5. **Cliente acessa o link** e faz upload da foto/PDF
6. **Cliente confirma** digitando "enviado" no WhatsApp
7. **Bot verifica** se arquivo foi recebido
8. **Dados completos** são enviados ao grupo de consultores

### Fluxo Técnico:

```
WhatsApp → Bot (coleta dados) → Envia link formulário
                ↓
Cliente acessa formulário web → Upload de arquivo
                ↓
Arquivo salvo em temp_media/ → Notificação ao grupo
                ↓
Bot confirma recebimento → Continua conversa
```

---

## 📋 Configuração

### 1. URL Pública (OBRIGATÓRIO)

O formulário **precisa de uma URL pública** para funcionar. Configure no arquivo `.env`:

```env
WEBHOOK_BASE_URL=https://seu-dominio.com
# ou para desenvolvimento local com ngrok:
WEBHOOK_BASE_URL=https://xxxx-xxx-xxx-xxx.ngrok-free.app
```

### 2. Usando ngrok (Desenvolvimento)

```bash
# Inicie seu bot Flask na porta 5001
python script.py

# Em outro terminal, inicie o ngrok
ngrok http 5001

# Copie a URL gerada (ex: https://abcd-1234.ngrok-free.app)
# Atualize WEBHOOK_BASE_URL no .env com essa URL
```

### 3. Estrutura de Arquivos

```
whatsapp-python-chatbot/
├── templates/
│   └── upload_prescription.html   # Formulário de upload
├── temp_media/                    # Receitas enviadas (auto-criado)
│   └── prescription_upload_*      # Arquivos de clientes
├── script.py                      # Bot com rotas de upload
└── .env                          # Configurações (WEBHOOK_BASE_URL)
```

---

## 🌐 Rotas Disponíveis

### GET /upload
- **Descrição**: Página do formulário de upload
- **Query Params**: 
  - `phone` (opcional): Pré-preenche telefone do cliente
- **Exemplo**: 
  ```
  https://seu-dominio.com/upload?phone=81999887766
  ```

### POST /upload_prescription
- **Descrição**: Recebe arquivos enviados pelo formulário
- **Form Data**:
  - `phone` (obrigatório): WhatsApp do cliente
  - `name` (obrigatório): Nome completo
  - `prescription` (obrigatório): Arquivo (imagem ou PDF, máx 10MB)
- **Retorno**: JSON com status de sucesso/erro

### GET /media/{filename}
- **Descrição**: Serve arquivos para a API do WhatsApp
- **Uso**: Automático pelo bot ao enviar receitas ao grupo

---

## 📱 Uso pelo Cliente

### Passo 1: Cliente recebe link
```
Bot: "Perfeito! 📸

Por questões de segurança e qualidade, pedimos que você 
envie sua receita através do nosso formulário online:

🔗 Link para envio:
https://seu-dominio.com/upload?phone=81999887766

✅ É rápido e seguro!
✅ Pode enviar foto ou PDF
✅ Receberemos em alta qualidade

Após enviar pelo link, digite "enviado" aqui para continuar."
```

### Passo 2: Cliente preenche formulário
- Nome completo
- Telefone (já preenchido)
- Upload de arquivo (foto ou PDF)

### Passo 3: Cliente confirma
```
Cliente: "enviado"

Bot: "✅ Receita recebida com sucesso!
Seus dados foram enviados ao consultor..."
```

---

## 🔒 Segurança

### Validações Implementadas:

1. **Tamanho de arquivo**: Máximo 10MB
2. **Tipos permitidos**: JPG, PNG, WEBP, PDF
3. **Validação de telefone**: 10-11 dígitos
4. **Nome mínimo**: 2 caracteres
5. **Sanitização de nomes**: Remove caracteres especiais
6. **Path traversal**: Bloqueado (validação de filename)

### Nomenclatura de Arquivos:

```
prescription_upload_{telefone}_{nome}_{timestamp}.{ext}

Exemplo:
prescription_upload_81999887766_joao_silva_20250124_173952.jpg
```

---

## 📊 Notificações ao Grupo

Quando cliente envia receita, o grupo recebe:

```
🔔 RECEITA ENVIADA VIA FORMULÁRIO

👤 Cliente: João Silva
📱 WhatsApp: 81999887766
⏰ Horário: 24/10/2025 às 17:39

📎 Arquivo: receita_oculos.jpg
💾 Tamanho: 1.2 MB

---
Arquivo será enviado a seguir
```

Seguido pelo **arquivo real** (imagem ou PDF).

---

## 🧹 Limpeza Automática

Arquivos em `temp_media/` são automaticamente removidos após **24 horas** (configurável via `MEDIA_CLEANUP_HOURS`).

---

## 🐛 Resolução de Problemas

### Problema: "Link não abre"
**Solução**: Verifique se `WEBHOOK_BASE_URL` está configurado corretamente no `.env`

### Problema: "Arquivo não foi recebido"
**Solução**: 
1. Verifique se ngrok está rodando
2. Confirme que URL do ngrok está no `.env`
3. Veja logs do Flask para erros

### Problema: "Imagem não chega no grupo"
**Solução**: 
1. Verifique `NOTIFICATION_GROUP_ID` no `.env`
2. Confirme que URL pública está acessível
3. Verifique logs de envio do WhatsApp

### Problema: "Formulário retorna erro 500"
**Solução**: 
1. Verifique permissões da pasta `temp_media/`
2. Veja logs do Flask: `tail -f whatsapp_bot.log`
3. Confirme que Flask está rodando

---

## 📝 Logs Úteis

```python
# Logs de upload bem-sucedido:
✅ Prescription uploaded via form: prescription_upload_...
   Customer: João Silva (81999887766)
✅ Prescription notification sent to group

# Logs de verificação:
✅ Found uploaded prescription: /path/to/file.jpg
ℹ️ No uploaded prescription found for 81999887766

# Logs de erro:
❌ Error processing prescription upload: ...
```

---

## 🎨 Personalização

### Modificar cores do formulário:

Edite `templates/upload_prescription.html`:

```css
/* Gradiente principal */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Cor do logo */
.logo h1 { color: #667eea; }

/* Botão de envio */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### Modificar tamanho máximo:

Edite `script.py`:

```python
# Altere de 10MB para outro valor
if file_size > 20 * 1024 * 1024:  # 20MB
```

---

## ✅ Vantagens deste Sistema

1. ✅ **Contorna criptografia** do WaSender API
2. ✅ **Qualidade total** das imagens (sem compressão do WhatsApp)
3. ✅ **Aceita PDFs** além de imagens
4. ✅ **Interface amigável** para clientes
5. ✅ **Segurança** com validações robustas
6. ✅ **Notificações automáticas** ao grupo
7. ✅ **Limpeza automática** de arquivos antigos
8. ✅ **Rastreamento** por telefone do cliente

---

## 🚀 Deploy em Produção

### Opção 1: Servidor VPS (Recomendado)

```bash
# Configure domínio apontando para seu VPS
# Exemplo: bot.ggdiskoptica.com.br

# Configure nginx como proxy reverso
# Adicione SSL com Let's Encrypt

# Configure WEBHOOK_BASE_URL:
WEBHOOK_BASE_URL=https://bot.ggdiskoptica.com.br
```

### Opção 2: Plataforma Cloud

- **Heroku**: Configure domínio personalizado
- **Railway**: URL automática ou domínio custom
- **Render**: URL automática .onrender.com

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique logs: `whatsapp_bot.log`
2. Teste manualmente: Acesse `/upload` no navegador
3. Verifique configurações do `.env`
4. Confirme que ngrok/servidor está online

---

**Desenvolvido para GGDISK Ótica** 👓
*Versão 1.0 - Janeiro 2025*

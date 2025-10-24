# 📤 Sistema de Upload Externo de Receitas

## 🎯 Problema Resolvido

A **WaSender API tem limitação de criptografia** que impede o download direto de imagens enviadas pelos clientes via WhatsApp. As imagens são armazenadas em URLs criptografadas (.enc) que requerem chaves de descriptografia não disponíveis na API.

## ✅ Solução Implementada

Criamos um **formulário web externo** onde clientes podem fazer upload de suas receitas de óculos (fotos ou PDFs) de forma segura e independente do WhatsApp.

---

## 🚀 Como Usar

### Para o Cliente:

1. **Conversa normal** com o bot pelo WhatsApp
2. Bot coleta dados (nome, telefone, CPF)
3. **Bot pergunta sobre receita**
4. Cliente responde "SIM"
5. **Bot envia link do formulário**:
   ```
   🔗 Link para envio:
   https://seu-dominio.com/upload?phone=81999887766
   
   ✅ É rápido e seguro!
   ✅ Pode enviar foto ou PDF
   ✅ Receberemos em alta qualidade
   ```
6. **Cliente acessa o link** no navegador
7. **Preenche o formulário** (nome já vem preenchido)
8. **Faz upload** da foto/PDF
9. **Retorna ao WhatsApp** e digita "enviado"
10. **Bot confirma** recebimento e finaliza

### Para o Consultor:

1. **Recebe notificação** no grupo:
   ```
   🔔 RECEITA ENVIADA VIA FORMULÁRIO
   
   👤 Cliente: João Silva
   📱 WhatsApp: 81999887766
   ⏰ Horário: 24/10/2025 às 17:39
   
   📎 Arquivo: receita.jpg
   💾 Tamanho: 1.2 MB
   ```
2. **Recebe o arquivo** (imagem ou PDF) no grupo
3. **Pode atender o cliente** com todas as informações

---

## 🛠️ Configuração Técnica

### 1. Requisitos

- Flask (já instalado)
- URL pública (ngrok ou domínio)
- Diretório `templates/` criado
- Diretório `temp_media/` criado

### 2. Configurar URL Pública

**Edite o `.env`:**

```env
# Desenvolvimento (ngrok)
WEBHOOK_BASE_URL=https://abc123.ngrok-free.app

# Produção
WEBHOOK_BASE_URL=https://bot.ggdiskoptica.com.br
```

**Executar ngrok (desenvolvimento):**

```bash
# Terminal 1: Rodar o bot
python script.py

# Terminal 2: Rodar ngrok
ngrok http 5001

# Copiar URL do ngrok e atualizar .env
# Reiniciar o bot
```

### 3. Testar Instalação

```bash
# Executar testes automatizados
python test_upload_form.py

# Ou testar manualmente no navegador
# Acesse: http://localhost:5001/upload
```

---

## 📁 Arquivos Criados

### `templates/upload_prescription.html`
- Formulário HTML responsivo
- Design moderno com gradiente roxo
- Validações JavaScript no cliente
- Preview de arquivo selecionado
- Feedback visual de upload

### Rotas Flask Adicionadas

#### `GET /upload`
- Serve a página do formulário
- Aceita `?phone=` para pré-preencher
- Exemplo: `/upload?phone=81999887766`

#### `POST /upload_prescription`
- Recebe uploads do formulário
- Valida arquivo (tipo, tamanho)
- Salva em `temp_media/`
- Notifica grupo de consultores
- Retorna JSON com status

### Função `check_uploaded_prescription()`
- Verifica se cliente enviou arquivo
- Busca por padrão: `prescription_upload_{phone}_*`
- Retorna caminho do arquivo mais recente
- Usado no fluxo do bot

---

## 🔒 Segurança

### Validações Implementadas:

1. **Tamanho máximo**: 10MB
2. **Tipos permitidos**: JPG, PNG, WEBP, PDF
3. **Telefone**: 10-11 dígitos obrigatórios
4. **Nome**: Mínimo 2 caracteres
5. **Path traversal**: Bloqueado
6. **Sanitização**: Remove caracteres especiais

### Nomenclatura Segura:

```
prescription_upload_{telefone}_{nome_sanitizado}_{timestamp}.{ext}

Exemplos:
prescription_upload_81999887766_joao_silva_20250124_173952.jpg
prescription_upload_81988776655_maria_santos_20250124_174521.pdf
```

---

## 🔄 Fluxo Completo no Código

### 1. Bot Pergunta sobre Receita

```python
# Em process_customer_form_step() - step 'prescription'
if message_text.lower().strip() in ['sim', 's', 'tenho', 'possuo']:
    phone_number = safe_sender_id.replace('_', '')
    upload_url = f"{CONFIG['WEBHOOK_BASE_URL']}/upload?phone={phone_number}"
    
    return f"""
Perfeito! 📸

Por questões de segurança e qualidade, pedimos que você envie 
sua receita através do nosso formulário online:

🔗 *Link para envio:*
{upload_url}
"""
```

### 2. Cliente Faz Upload

```javascript
// No formulário HTML (upload_prescription.html)
form.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('phone', phone);
    formData.append('name', name);
    formData.append('prescription', fileInput.files[0]);
    
    const response = await fetch('/upload_prescription', {
        method: 'POST',
        body: formData
    });
    
    // Mostra sucesso e redireciona para WhatsApp
});
```

### 3. Bot Recebe Upload

```python
@app.route('/upload_prescription', methods=['POST'])
def upload_prescription():
    # Validações
    phone = request.form['phone']
    name = request.form['name']
    file = request.files['prescription']
    
    # Salvar arquivo
    filename = f"prescription_upload_{safe_sender_id}_{safe_name}_{timestamp}.{ext}"
    filepath = os.path.join(CONFIG["TEMP_MEDIA_DIR"], filename)
    file.save(filepath)
    
    # Notificar grupo
    send_whatsapp_message(group_id, notification_message)
    send_whatsapp_message(group_id, caption, media_url=public_url)
```

### 4. Cliente Confirma

```python
# Cliente digita "enviado"
if message_text.lower().strip() in ['enviado', 'enviei', 'pronto']:
    uploaded_file = check_uploaded_prescription(safe_sender_id)
    
    if uploaded_file:
        # Prosseguir com confirmação
        prescription_info = "✅ Cliente enviou receita via FORMULÁRIO ONLINE"
    else:
        # Pedir para enviar novamente
```

---

## 🎨 Personalização

### Modificar Cores do Formulário

Edite `templates/upload_prescription.html`:

```css
/* Gradiente de fundo */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Cor do logo */
.logo h1 { 
    color: #667eea; 
}

/* Gradiente do botão */
button[type="submit"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
```

### Modificar Tamanho Máximo

Edite `script.py`:

```python
# Alterar de 10MB para 20MB
if file_size > 20 * 1024 * 1024:  # 20MB
    return jsonify({'error': 'File too large (max 20MB)'}), 400
```

### Adicionar Mais Tipos de Arquivo

Edite `script.py`:

```python
# Adicionar DOC, DOCX
allowed_extensions = {'jpg', 'jpeg', 'png', 'webp', 'pdf', 'doc', 'docx'}
```

---

## 📊 Monitoramento

### Logs de Upload

```python
# Sucesso
✅ Prescription uploaded via form: prescription_upload_...
   Customer: João Silva (81999887766)
✅ Prescription notification sent to group

# Verificação
✅ Found uploaded prescription: /path/to/file.jpg
ℹ️ No uploaded prescription found for 81999887766

# Erro
❌ Error processing prescription upload: ...
```

### Métricas Úteis

```bash
# Contar uploads do dia
ls temp_media/prescription_upload_* | wc -l

# Ver uploads recentes
ls -lht temp_media/prescription_upload_* | head

# Ver tamanho total
du -sh temp_media/

# Limpar manualmente arquivos antigos (>24h)
find temp_media/ -name "prescription_upload_*" -mtime +1 -delete
```

---

## 🐛 Troubleshooting

### ❌ Link não abre

**Problema**: Cliente recebe link mas não consegue acessar

**Solução**:
1. Verifique `WEBHOOK_BASE_URL` no `.env`
2. Confirme que ngrok está rodando
3. Teste link manualmente no navegador

### ❌ "Arquivo não foi recebido"

**Problema**: Cliente faz upload mas bot não encontra

**Solução**:
1. Verifique logs do Flask
2. Confirme que arquivo foi salvo em `temp_media/`
3. Verifique permissões da pasta
4. Teste função `check_uploaded_prescription()`

### ❌ Erro 500 no upload

**Problema**: Formulário retorna erro interno

**Solução**:
1. Veja logs completos: `tail -f whatsapp_bot.log`
2. Verifique se pasta `temp_media/` existe
3. Confirme permissões de escrita
4. Teste endpoint manualmente com curl

### ❌ Imagem não chega no grupo

**Problema**: Upload funciona mas grupo não recebe

**Solução**:
1. Verifique `NOTIFICATION_GROUP_ID` no `.env`
2. Confirme que URL pública está acessível
3. Teste endpoint `/media/{filename}` manualmente
4. Veja logs de envio do WhatsApp

---

## 📖 Documentação Relacionada

- **[GUIA_UPLOAD_RECEITAS.md](GUIA_UPLOAD_RECEITAS.md)** - Guia completo técnico
- **[README.md](README.md)** - Documentação principal do bot
- **[GUIA_ENVIO_IMAGENS.md](GUIA_ENVIO_IMAGENS.md)** - Sistema antigo (deprecated)

---

## 🎯 Próximos Passos

Após implementar o upload externo:

1. ✅ **Testar localmente** com ngrok
2. ✅ **Testar fluxo completo** com cliente real
3. ✅ **Configurar domínio** para produção
4. ✅ **Monitorar logs** por alguns dias
5. ✅ **Ajustar mensagens** conforme feedback

---

**Desenvolvido para GGDISK Ótica** 👓
*Sistema de Upload Externo v1.0*

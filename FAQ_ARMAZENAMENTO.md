# ❓ FAQ - Sistema de Armazenamento Temporário

## Perguntas Frequentes e Soluções

---

## 📥 Salvamento de Mídia

### ❓ A imagem está sendo salva?

**Verifique:**
```bash
ls temp_media/
```

**Deve aparecer:**
```
prescription_558199887766_20251023_143052.jpg
```

**Se não aparecer, verifique os logs:**
```bash
grep "Media saved" whatsapp_bot.log
```

**Possíveis causas:**
1. ❌ Pasta `temp_media/` não existe → Bot cria automaticamente
2. ❌ Sem permissão de escrita → Execute `chmod 755 temp_media/`
3. ❌ Base64 inválido → Verifique se `jpegThumbnail` está presente

---

### ❓ Qual o tamanho do arquivo salvo?

**Normal:** 40-60 KB (thumbnail comprimido)  
**Esperado:** Suficiente para visualizar receita  
**Não é:** Imagem original completa

**Por quê?**
- WhatsApp envia `jpegThumbnail` (preview)
- Imagem original requer descriptografia complexa
- Thumbnail tem qualidade suficiente para receitas médicas

---

### ❓ Suporta PDFs?

**Parcialmente.**

- ✅ Detecta quando cliente envia PDF
- ✅ Registra informação no formulário
- ❌ Não salva automaticamente (PDFs não têm thumbnail)
- ⚠️ Consultor precisa solicitar ao cliente

**Solução futura:**
```python
# Implementar download completo de documentos
def download_document_from_url(doc_url):
    # Usar API oficial do WhatsApp
    pass
```

---

## 📤 Envio ao Grupo

### ❓ Imagem não está chegando no grupo?

**Checklist:**

1. **Grupo configurado?**
   ```env
   NOTIFICATION_GROUP_ID=120363404721021632@g.us
   ```

2. **Arquivo existe?**
   ```bash
   ls temp_media/prescription_*.jpg
   ```

3. **Logs de envio:**
   ```bash
   grep "Sending prescription file" whatsapp_bot.log
   ```

**Possíveis erros:**

```
❌ Failed to send prescription file
```
**Causa:** Data URL muito grande (>5MB)  
**Solução:** Sistema envia fallback automático

```
⚠️ Não foi possível enviar o arquivo automaticamente
```
**Ação:** Consultor solicita receita diretamente ao cliente

---

### ❓ Data URL não funciona?

**Limitação da API:**
- WaSender API pode ter limite de tamanho
- Data URLs grandes podem falhar

**Solução implementada:**
```python
if media_result:
    logger.info("✅ Prescription file sent")
else:
    # Fallback automático
    send_whatsapp_message(
        group_id,
        "⚠️ Solicite a receita diretamente ao cliente"
    )
```

**Alternativa futura:**
- Upload para S3/Azure Blob
- Enviar URL pública
- Sem limites de tamanho

---

## 🗑️ Limpeza Automática

### ❓ Arquivos não estão sendo removidos?

**Verifique a configuração:**
```env
MEDIA_CLEANUP_HOURS=24
```

**Verifique os logs:**
```bash
grep "Removed old media" whatsapp_bot.log
```

**Deve aparecer:**
```
🗑️ Removed old media: prescription_558199887766_20251022_143052.jpg
🧹 Cleanup complete: 3 old media files removed
```

**Se não aparecer:**
- Arquivos ainda não têm 24h
- Nenhum webhook foi recebido (cleanup executa no webhook)
- Erro de permissão (verifique `chmod`)

---

### ❓ Quero limpar mais rápido/devagar?

**Edite `.env`:**
```env
# Limpar após 6 horas
MEDIA_CLEANUP_HOURS=6

# Limpar após 48 horas
MEDIA_CLEANUP_HOURS=48

# Limpar após 7 dias
MEDIA_CLEANUP_HOURS=168
```

**Reinicie o bot:**
```bash
python script.py
```

---

### ❓ Como limpar manualmente?

**Opção 1: Remover tudo**
```bash
rm -rf temp_media/*
```

**Opção 2: Remover apenas antigos (Linux/Mac)**
```bash
find temp_media/ -type f -mtime +1 -delete
```

**Opção 3: Remover apenas antigos (Windows)**
```powershell
Get-ChildItem temp_media\ | Where-Object {$_.LastWriteTime -lt (Get-Date).AddHours(-24)} | Remove-Item
```

---

## 🔧 Problemas Comuns

### ❌ `ModuleNotFoundError: No module named 'requests'`

**Solução:**
```bash
pip install requests
```

Ou:
```bash
pip install -r requirements.txt
```

---

### ❌ `PermissionError: [Errno 13] Permission denied: 'temp_media'`

**Solução Linux/Mac:**
```bash
chmod 755 temp_media/
```

**Solução Windows:**
- Clique direito → Propriedades → Segurança
- Conceda permissão de escrita

---

### ❌ Arquivo salvo mas não aparece no grupo

**Debug:**

1. **Verifique se arquivo existe:**
   ```bash
   ls -la temp_media/prescription_*.jpg
   ```

2. **Verifique logs de envio:**
   ```bash
   tail -100 whatsapp_bot.log | grep "prescription"
   ```

3. **Teste envio manual:**
   ```python
   # No Python console
   import os
   print(os.path.exists('temp_media/prescription_558199887766_20251023_143052.jpg'))
   ```

---

### ❌ Base64 está muito grande

**Sintoma:**
```
Error: payload too large
```

**Causa:**
- Arquivo > 5MB
- Data URL excede limite da API

**Solução:**
```python
# Implementar compressão de imagem
from PIL import Image

def compress_image(file_path, max_size_kb=500):
    img = Image.open(file_path)
    img.save(file_path, quality=85, optimize=True)
```

---

## 💡 Dicas e Melhores Práticas

### 📊 Monitoramento

**Verifique espaço usado:**
```bash
du -sh temp_media/
```

**Conte arquivos:**
```bash
ls temp_media/ | wc -l
```

**Arquivos mais antigos:**
```bash
ls -lt temp_media/ | tail -10
```

---

### 🔒 Segurança

**Boas práticas:**

1. ✅ Nunca commit `temp_media/` no git
   ```gitignore
   temp_media/
   ```

2. ✅ Limpar regularmente (já configurado)
3. ✅ Usar HTTPS para webhook
4. ✅ Validar tipos de arquivo aceitos

---

### ⚡ Performance

**Otimizações:**

1. **Limpeza eficiente:**
   ```python
   # Já implementado
   cleanup_old_media()  # Executa a cada webhook
   ```

2. **Limitar tamanho:**
   ```python
   # Adicionar verificação
   if len(file_data) > 5_000_000:  # 5MB
       logger.warning("File too large, skipping")
       return None
   ```

3. **Compressão:**
   ```python
   # Futuro: comprimir antes de enviar
   compressed_data = compress_image(file_path)
   ```

---

## 🆘 Troubleshooting Avançado

### 🔍 Debug Mode

**Ativar logs detalhados:**
```python
# No início do script.py
logging.basicConfig(level=logging.DEBUG)
```

**Logs de base64:**
```python
logger.debug(f"Base64 length: {len(base64_data)}")
logger.debug(f"First 50 chars: {base64_data[:50]}")
```

---

### 🧪 Teste Manual

**Salvar mídia de teste:**
```python
import base64

# Base64 de teste (pequeno)
test_base64 = "/9j/4AAQSkZJRgABAQAAAQABAAD..."

# Salvar
from script import save_media_from_base64
file_path = save_media_from_base64(test_base64, "test_user", "test", "jpg")
print(f"Saved to: {file_path}")
```

**Enviar ao grupo de teste:**
```python
from script import send_whatsapp_message

send_whatsapp_message(
    "YOUR_GROUP_ID",
    "Teste de envio de imagem",
    message_type='image',
    media_url=f"file://{file_path}"
)
```

---

### 📝 Logs Úteis

**Ver todos os logs de mídia:**
```bash
grep -i "media\|prescription\|image" whatsapp_bot.log
```

**Ver apenas erros:**
```bash
grep -i "error\|failed\|warning" whatsapp_bot.log | grep -i media
```

**Ver últimas 50 linhas:**
```bash
tail -50 whatsapp_bot.log
```

**Monitorar em tempo real:**
```bash
tail -f whatsapp_bot.log
```

---

## 🎓 Entendendo o Código

### Como funciona o base64?

```python
# Texto original
text = "Hello"

# Codificar
encoded = base64.b64encode(text.encode()).decode()
# 'SGVsbG8='

# Decodificar
decoded = base64.b64decode(encoded).decode()
# 'Hello'
```

### Como funciona o salvamento?

```python
# 1. Receber base64
jpeg_thumbnail = image_data.get('jpegThumbnail')
# "/9j/4AAQSkZJRgABAQAA..."

# 2. Decodificar
media_bytes = base64.b64decode(jpeg_thumbnail)
# bytes: b'\xff\xd8\xff\xe0...'

# 3. Salvar
with open('image.jpg', 'wb') as f:
    f.write(media_bytes)
```

### Como funciona o data URL?

```python
# Formato
data_url = f"data:{mimetype};base64,{base64_string}"

# Exemplo
data_url = "data:image/jpeg;base64,/9j/4AAQSkZJRg..."

# Pode ser usado diretamente em:
# - HTML: <img src="data:image/jpeg;base64,...">
# - API: send_image(url=data_url)
```

---

## 📞 Suporte

**Ainda com problemas?**

1. 📖 Leia: `SISTEMA_ARMAZENAMENTO_TEMPORARIO.md`
2. 📊 Veja: `FLUXO_VISUAL_ARMAZENAMENTO.md`
3. 📝 Confira: logs em `whatsapp_bot.log`
4. 🔧 Teste: Comandos de debug acima

**Informações úteis para debug:**
- Versão do Python: `python --version`
- Pacotes instalados: `pip list`
- Espaço em disco: `df -h`
- Permissões: `ls -la temp_media/`

---

✅ **Sistema funcionando perfeitamente com estas configurações!**

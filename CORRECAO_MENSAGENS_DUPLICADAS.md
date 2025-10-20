# Correção: Mensagens Duplicadas em Grupos

## 🐛 Problema Identificado

O bot estava enviando **mensagens duplicadas** quando utilizado em grupos do WhatsApp.

### Causa Raiz

Ao analisar os logs (`whatsapp_bot.log`), identificamos que:

1. **Webhooks Duplicados**: Para cada mensagem em grupo, o webhook era chamado **DUAS VEZES**:
   - Uma vez com evento `messages.received`
   - Uma vez com evento `messages.upsert`

2. **Ambos com o mesmo ID de mensagem**: Exemplo do log:
   ```
   2025-10-18 16:27:02,995 - messages.upsert - ID: 3EB05DD9C0A899955D5194
   2025-10-18 16:27:02,995 - messages.received - ID: 3EB05DD9C0A899955D5194
   ```

3. **Processamento Duplicado**: Como o código processava qualquer evento `messages.upsert` sem verificar se a mensagem já havia sido processada, o bot:
   - Recebia a mensagem 2x
   - Processava com Gemini AI 2x
   - Enviava a resposta 2x

## ✅ Solução Implementada

### Sistema de Deduplicação de Mensagens

Implementamos um **cache de mensagens processadas** com as seguintes características:

#### 1. Cache em Memória
```python
processed_messages = {}  # {message_id: timestamp}
PROCESSED_MESSAGE_TTL = 300  # 5 minutos
```

#### 2. Funções de Controle

**`is_message_processed(message_id)`**
- Verifica se uma mensagem já foi processada
- Remove automaticamente IDs expirados (> 5 minutos)

**`mark_message_processed(message_id)`**
- Marca uma mensagem como processada
- Armazena o timestamp para controle de TTL

**`cleanup_processed_messages()`**
- Remove IDs de mensagens antigas do cache
- Evita crescimento infinito da memória

#### 3. Verificação no Webhook

No início do processamento do webhook:

```python
# Get message ID for deduplication
message_id = message_info.get('key', {}).get('id')

# Check if this message was already processed
if message_id and is_message_processed(message_id):
    logger.info(f"Skipping duplicate message: {message_id}")
    return jsonify({'status': 'success', 'message': 'Duplicate message ignored'}), 200

# Mark this message as processed
if message_id:
    mark_message_processed(message_id)
```

## 🎯 Benefícios

✅ **Elimina duplicação**: Cada mensagem é processada apenas uma vez
✅ **Eficiente**: Cache em memória com limpeza automática
✅ **Seguro**: TTL de 5 minutos evita consumo excessivo de memória
✅ **Compatível**: Funciona tanto em grupos quanto em conversas individuais
✅ **Logs claros**: Registra quando mensagens duplicadas são ignoradas

## 📊 Comportamento Antes vs Depois

### Antes (com duplicação)
```
[16:27:02] Webhook recebido: messages.received - ID: 3EB05DD9...
[16:27:02] Processando mensagem "Oi"
[16:27:02] Enviando resposta (5 chunks)
[16:27:03] Webhook recebido: messages.upsert - ID: 3EB05DD9...
[16:27:03] Processando mensagem "Oi" (DUPLICADO!)
[16:27:03] Enviando resposta (5 chunks) (DUPLICADO!)
```

### Depois (sem duplicação)
```
[16:27:02] Webhook recebido: messages.received - ID: 3EB05DD9...
[16:27:02] Processando mensagem "Oi"
[16:27:02] Marcando mensagem como processada
[16:27:02] Enviando resposta (5 chunks)
[16:27:03] Webhook recebido: messages.upsert - ID: 3EB05DD9...
[16:27:03] Skipping duplicate message: 3EB05DD9...
[16:27:03] ✅ Mensagem duplicada ignorada
```

## 🧪 Como Testar

1. **Reinicie o bot**:
   ```bash
   python script.py
   ```

2. **Envie uma mensagem em um grupo** onde o bot está presente

3. **Verifique os logs** (`whatsapp_bot.log`):
   - Deve aparecer apenas **1 processamento** por mensagem
   - Deve aparecer `"Skipping duplicate message"` para webhooks duplicados

4. **Confirme no WhatsApp**:
   - O bot deve enviar apenas **1 resposta** (não mais duplicadas)

## 🔍 Monitoramento

Para verificar se está funcionando, procure nos logs:

```bash
# Mensagens processadas com sucesso
grep "Processing text message" whatsapp_bot.log

# Mensagens duplicadas ignoradas (deve aparecer)
grep "Skipping duplicate message" whatsapp_bot.log

# Verificar quantidade de processamentos por ID
grep "3EB05DD9C0A899955D5194" whatsapp_bot.log
```

## 📝 Arquivos Modificados

- `script.py`: Adicionado sistema de deduplicação
  - Cache `processed_messages`
  - Funções `is_message_processed()`, `mark_message_processed()`, `cleanup_processed_messages()`
  - Verificação no webhook antes do processamento

## ⚠️ Notas Importantes

1. **Cache em Memória**: O cache é perdido se o bot for reiniciado, mas isso não é problema porque:
   - Mensagens antigas (> 5 min) não são relevantes
   - TTL garante que a memória não cresce infinitamente

2. **Compatibilidade**: A solução funciona para:
   - ✅ Grupos (`@g.us`)
   - ✅ Conversas individuais (`@s.whatsapp.net`)
   - ✅ Todos os tipos de mensagem

3. **Performance**: Impacto mínimo:
   - Operações O(1) para verificação e inserção
   - Limpeza automática periódica
   - Memória controlada pelo TTL

## 🚀 Próximos Passos (Opcional)

Se quiser melhorias futuras:

1. **Persistência**: Usar Redis para cache persistente
2. **Métricas**: Contar quantas duplicatas são bloqueadas
3. **Configuração**: Tornar o TTL configurável via `.env`

---

**Status**: ✅ **CORRIGIDO**  
**Data**: 20 de outubro de 2025  
**Versão**: 1.0.1

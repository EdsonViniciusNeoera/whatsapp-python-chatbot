# 🔧 Correção: Detecção de Orçamento via Conversa Natural

## 🐛 Problema Identificado

### Cenário do Bug
```
Cliente: "gostaria de fazer um orçamento"
Bot: [IA responde e inicia formulário]
Problema:
  ❌ NÃO perguntou sobre receita
  ❌ Notificação ao grupo: "Cliente solicitou contato com consultor"
  ❌ Deveria ser: "2 - Fazer orçamento de óculos"
```

### Causa Raiz
O código anterior só detectava palavras-chave na **resposta da IA** (jailson, josimar, consultor), mas não analisava a **mensagem original do cliente** para identificar a intenção específica (orçamento vs ajuste vs outro).

---

## ✅ Solução Implementada

### Detecção Inteligente de Intenção

Agora o sistema analisa a **mensagem original do cliente** ANTES de iniciar o formulário para identificar:

1. **Pedidos de Orçamento** → Pede receita
2. **Pedidos de Ajuste/Reparo** → NÃO pede receita
3. **Outros Pedidos** → NÃO pede receita (genérico)

---

## 🔍 Como Funciona

### Fluxo de Detecção

```python
# 1. Cliente envia mensagem
user_message = "gostaria de fazer um orçamento"

# 2. IA responde (sugere contato com consultor)
ai_response = "Vou encaminhar para nossos consultores..."

# 3. NOVO: Analisa mensagem ORIGINAL do cliente
if 'orçamento' in user_message.lower():
    reason = "2 - Fazer orçamento de óculos (solicitação via conversa)"
    # ✅ VAI PEDIR RECEITA

elif 'ajuste' in user_message.lower():
    reason = "3 - Ajustes e reparos (solicitação via conversa)"
    # ❌ NÃO vai pedir receita

else:
    reason = "Cliente solicitou contato com consultor"
    # ❌ NÃO vai pedir receita

# 4. Inicia formulário com o motivo correto
start_customer_form(user_id, reason)
```

---

## 🎯 Palavras-Chave Detectadas

### Para ORÇAMENTO (pede receita)
```python
budget_keywords = [
    'orçamento',
    'orcamento',
    'orçar',
    'preço',
    'preco',
    'valor',
    'quanto custa',
    'comprar óculos',
    'fazer óculos'
]
```

### Para AJUSTE/REPARO (não pede receita)
```python
repair_keywords = [
    'ajuste',
    'ajustar',
    'reparo',
    'reparar',
    'consertar',
    'conserto',
    'quebrou',
    'quebrado'
]
```

---

## 🧪 Testes de Validação

### ✅ Teste 1: Orçamento via Conversa
```
Cliente: "gostaria de fazer um orçamento"
Bot: [IA responde] + "preciso de algumas informações"
Bot: "Por favor, me diga seu nome completo:"
Cliente: "João Silva"
Bot: "Qual seu telefone para contato?"
Cliente: "81999887766"
Bot: "Agora preciso do seu CPF:"
Cliente: "12345678901"
Bot: "Você possui receita médica?" ✅ DEVE PERGUNTAR
Cliente: "sim" [envia foto]
Bot: [Mostra confirmação com receita]
Cliente: "sim"
Bot: [Envia para grupo]

Notificação no grupo:
🔔 NOVA SOLICITAÇÃO DE ATENDIMENTO
📋 Motivo: 2 - Fazer orçamento de óculos (solicitação via conversa) ✅
💊 RECEITA MÉDICA ✅
```

### ✅ Teste 2: Ajuste via Conversa
```
Cliente: "preciso de um ajuste no meu óculos"
Bot: [IA responde] + "preciso de algumas informações"
Bot: "Por favor, me diga seu nome completo:"
Cliente: "Maria Santos"
Bot: "Qual seu telefone para contato?"
Cliente: "81988776655"
Bot: "Agora preciso do seu CPF:"
Cliente: "98765432109"
Bot: [Confirmação SEM perguntar receita] ✅

Notificação no grupo:
🔔 NOVA SOLICITAÇÃO DE ATENDIMENTO
📋 Motivo: 3 - Ajustes e reparos (solicitação via conversa) ✅
[Sem campo de receita] ✅
```

### ✅ Teste 3: Outras Perguntas
```
Cliente: "quanto custa uma armação?"
Bot: [IA responde] + "preciso de algumas informações"
[... formulário ...]
Bot: "Você possui receita médica?" ✅ DEVE PERGUNTAR
(porque detectou "quanto custa" = orçamento)

Notificação no grupo:
📋 Motivo: 2 - Fazer orçamento de óculos (solicitação via conversa) ✅
```

### ✅ Teste 4: Menu Direto (não mudou)
```
Cliente: "2"
Bot: [Menu response] + "preciso de algumas informações"
[... formulário ...]
Bot: "Você possui receita médica?" ✅

Notificação no grupo:
📋 Motivo: 2 - Fazer orçamento de óculos ✅
```

---

## 📊 Comparação Antes vs Depois

### ANTES (com bug)
```
Cliente: "gostaria de fazer um orçamento"
↓
reason = "Cliente solicitou contato com consultor"
↓
is_budget = False (não tem "2 -" no reason)
↓
❌ Pula pergunta de receita
↓
Notificação: "Cliente solicitou contato com consultor"
```

### DEPOIS (corrigido)
```
Cliente: "gostaria de fazer um orçamento"
↓
Analisa palavras: "orçamento" encontrado!
↓
reason = "2 - Fazer orçamento de óculos (solicitação via conversa)"
↓
is_budget = True (tem "2 -" no reason)
↓
✅ Pergunta sobre receita
↓
Notificação: "2 - Fazer orçamento de óculos (solicitação via conversa)"
```

---

## 💻 Código da Correção

### Localização
- **Arquivo**: `script.py`
- **Linha**: ~1138-1162
- **Função**: Processamento da resposta da IA no webhook

### Lógica Implementada

```python
# Detecta intenção da mensagem original do cliente
user_message_lower = incoming_message_text.lower()
form_reason = None

# 1. Verifica se é pedido de ORÇAMENTO
budget_keywords = ['orçamento', 'orcamento', 'orçar', 'preço', 'preco', 'valor', 
                   'quanto custa', 'comprar óculos', 'fazer óculos']
if any(keyword in user_message_lower for keyword in budget_keywords):
    form_reason = "2 - Fazer orçamento de óculos (solicitação via conversa)"
    logger.info(f"Detected BUDGET request from user message")

# 2. Verifica se é pedido de AJUSTE/REPARO
elif any(keyword in user_message_lower for keyword in 
         ['ajuste', 'ajustar', 'reparo', 'reparar', 'consertar', 'conserto', 
          'quebrou', 'quebrado']):
    form_reason = "3 - Ajustes e reparos (solicitação via conversa)"
    logger.info(f"Detected REPAIR request from user message")

# 3. Verifica se IA sugere contato com especialista
ai_keywords = ['jailson', 'josimar', 'consultor', 'especialista', 'atendimento']
if any(keyword in response_text.lower() for keyword in ai_keywords):
    should_start_form = True
    
    # Se não detectou intenção específica, usa genérico
    if not form_reason:
        form_reason = "Cliente solicitou contato com consultor"
    
    # Inicia formulário com motivo correto
    start_customer_form(safe_sender_id, form_reason)
    logger.info(f"Started customer form based on AI response - reason: {form_reason}")
```

---

## 🔗 Integração com Sistema Existente

### Compatibilidade Mantida

1. **Menu direto** (opção 2, 3, etc.)
   - ✅ Funciona como antes
   - Reason: "2 - Fazer orçamento de óculos"

2. **Conversa natural sobre orçamento**
   - ✅ NOVO: Detecta corretamente
   - Reason: "2 - Fazer orçamento de óculos (solicitação via conversa)"

3. **Conversa natural sobre ajuste**
   - ✅ NOVO: Detecta corretamente
   - Reason: "3 - Ajustes e reparos (solicitação via conversa)"

### Detecção em `process_customer_form_step()`
```python
# Esta lógica já existia, agora funciona corretamente:
form_reason = form.get('reason', '')
is_budget = '2 -' in form_reason or 'orçamento' in form_reason.lower()

# ✅ Agora detecta:
# - "2 - Fazer orçamento de óculos" (menu)
# - "2 - Fazer orçamento de óculos (solicitação via conversa)" (IA)
# - Qualquer reason com palavra "orçamento"
```

---

## 📝 Checklist de Validação

Após reiniciar o bot, testar:

- [ ] Cliente digita "2" → Pede receita ✅
- [ ] Cliente digita "gostaria de fazer um orçamento" → Pede receita ✅
- [ ] Cliente digita "quanto custa uma armação?" → Pede receita ✅
- [ ] Cliente digita "3" → NÃO pede receita ✅
- [ ] Cliente digita "preciso ajustar meu óculos" → NÃO pede receita ✅
- [ ] Notificação de orçamento mostra "2 - Fazer orçamento" ✅
- [ ] Notificação de ajuste mostra "3 - Ajustes e reparos" ✅
- [ ] Log mostra "Detected BUDGET request" quando é orçamento ✅
- [ ] Log mostra "Detected REPAIR request" quando é ajuste ✅

---

## 🔍 Logs Importantes

### Orçamento Detectado
```
Using Gemini AI for response
Detected BUDGET request from user message
Started customer form based on AI response - reason: 2 - Fazer orçamento de óculos (solicitação via conversa)
Updated customer form for ... - step: prescription
Customer form sent to group for ...
```

### Ajuste Detectado
```
Using Gemini AI for response
Detected REPAIR request from user message
Started customer form based on AI response - reason: 3 - Ajustes e reparos (solicitação via conversa)
Updated customer form for ... - step: confirm (pula prescription)
Customer form sent to group for ...
```

### Outros Pedidos
```
Using Gemini AI for response
Started customer form based on AI response - reason: Cliente solicitou contato com consultor
Updated customer form for ... - step: confirm (pula prescription)
Customer form sent to group for ...
```

---

## 🎉 Benefícios da Correção

1. **Detecção Precisa**: Identifica corretamente orçamento vs ajuste vs outros
2. **Pergunta Certa**: Só pede receita quando necessário (orçamentos)
3. **Notificação Clara**: Grupo recebe motivo específico do contato
4. **Logs Detalhados**: Fácil debugar e entender o fluxo
5. **Flexível**: Funciona tanto por menu quanto por conversa natural
6. **Extensível**: Fácil adicionar novas palavras-chave

---

## 🚀 Como Aplicar

```bash
# Reiniciar o bot
python script.py
```

Testar cenários:
1. "gostaria de fazer um orçamento"
2. "quanto custa uma armação?"
3. "preciso de um ajuste"
4. "meu óculos quebrou"

---

## ⚠️ Observações

1. **Prioridade de Detecção**:
   - Primeiro verifica orçamento
   - Depois verifica ajuste
   - Por último usa genérico

2. **Múltiplas Palavras**:
   - Cliente: "quero fazer orçamento e ajuste"
   - Resultado: Detecta como orçamento (primeira verificação)

3. **Case Insensitive**:
   - "Orçamento", "ORÇAMENTO", "orçamento" → Todos funcionam

4. **Palavras Parciais**:
   - "orçar", "orçamento", "orcamento" → Todos funcionam

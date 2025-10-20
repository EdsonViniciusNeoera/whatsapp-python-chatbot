# 🔄 Mudanças: Receita Apenas para Orçamento

## 📋 Resumo das Alterações

### ❌ Removido
- **Opção 2**: "Agendar exame de vista" (não é um serviço oferecido)

### ✅ Alterado
- **Menu renumerado**: As opções foram reorganizadas de 1-7 para 1-6
- **Receita condicional**: Agora a receita é solicitada **APENAS** para pedidos de orçamento

---

## 📱 Novo Menu

```
1️⃣ 📍 Endereço e horário
2️⃣ 💰 Fazer orçamento de óculos  ← PEDE RECEITA
3️⃣ 🔧 Ajustes e reparos          ← NÃO PEDE RECEITA
4️⃣ 💳 Formas de pagamento        ← NÃO PEDE RECEITA
5️⃣ 👤 Falar com consultor        ← NÃO PEDE RECEITA
6️⃣ ❓ Outras dúvidas             ← NÃO PEDE RECEITA
```

---

## 🔄 Fluxo do Formulário

### Para ORÇAMENTO (Opção 2)
```
1. Nome completo
2. Telefone (DDD + número)
3. CPF (11 dígitos)
4. Receita médica? ← PERGUNTA AQUI
   - SIM: Enviar foto/PDF
   - NÃO: Informar que não tem
5. Confirmação dos dados
6. Envio para grupo de atendentes
```

### Para OUTRAS OPÇÕES (3, 4, 5, 6)
```
1. Nome completo
2. Telefone (DDD + número)
3. CPF (11 dígitos)
4. [PULA A RECEITA] ← VAI DIRETO PARA CONFIRMAÇÃO
5. Confirmação dos dados
6. Envio para grupo de atendentes
```

---

## 💻 Mudanças Técnicas

### 1. `persona.json`
**Antes:**
```json
"2": "Agendar exame de vista",
"3": "Fazer orçamento de óculos",
"4": "Ajustes e reparos",
...
"7": "Outras dúvidas"
```

**Depois:**
```json
"2": "Fazer orçamento de óculos",
"3": "Ajustes e reparos",
...
"6": "Outras dúvidas"
```

### 2. `script.py` - Função `process_customer_form_step()`

#### Mudança no Passo 3 (CPF):
```python
# Novo código que verifica se é orçamento
form_reason = form.get('reason', '')
is_budget = '2 -' in form_reason or 'orçamento' in form_reason.lower()

if is_budget:
    # Apenas orçamentos pedem receita
    update_customer_form(safe_sender_id, 'prescription', 'cpf', cpf_formatted)
    return "Ótimo! Você possui *receita médica*?..."
else:
    # Outras opções pulam direto para confirmação
    form_data['prescription'] = "Não solicitado (apenas para orçamentos)"
    form_data['has_prescription'] = False
    update_customer_form(safe_sender_id, 'confirm', 'cpf', cpf_formatted)
    # Mostra resumo de confirmação sem receita
```

#### Mudança na Notificação ao Grupo:
```python
# Só mostra receita se foi coletada (orçamentos)
if form_data.get('has_prescription', False):
    # Cliente enviou receita
    notification_parts.append("💊 *RECEITA MÉDICA*")
    notification_parts.append(prescription_info)
elif prescription_info and prescription_info != "Não solicitado (apenas para orçamentos)":
    # Cliente não tem receita (mas foi perguntado)
    notification_parts.append(f"💊 *Receita:* {prescription_info}")
# Se for "Não solicitado", não mostra nada
```

---

## 🧪 Como Testar

### Teste 1: Orçamento (DEVE PEDIR RECEITA)
```
1. Enviar: "2"
2. Responder: "João Silva"
3. Responder: "81999887766"
4. Responder: "12345678901"
5. Bot pergunta: "Você possui receita médica?" ✅
6. Enviar foto ou "não"
7. Confirmar com "sim"
```

### Teste 2: Ajustes (NÃO DEVE PEDIR RECEITA)
```
1. Enviar: "3"
2. Responder: "Maria Santos"
3. Responder: "81988776655"
4. Responder: "98765432109"
5. Bot vai direto para confirmação (SEM perguntar receita) ✅
6. Confirmar com "sim"
```

### Teste 3: Outras opções (4, 5, 6)
```
Mesmo comportamento do Teste 2:
- Nome → Telefone → CPF → Confirmação (sem receita)
```

---

## 📊 Comparação Antes vs Depois

| Aspecto | Antes | Depois |
|---------|-------|--------|
| **Opções do menu** | 7 opções (1-7) | 6 opções (1-6) |
| **Exame de vista** | Opção 2 ✅ | Removido ❌ |
| **Orçamento** | Opção 3 | Opção 2 |
| **Receita para orçamento** | ✅ Pede | ✅ Pede |
| **Receita para ajustes** | ✅ Pede | ❌ NÃO pede |
| **Receita para outras opções** | ✅ Pede | ❌ NÃO pede |

---

## 🎯 Benefícios

### 1. Menu Mais Focado
- ❌ Removeu serviço não oferecido (exame de vista)
- ✅ Menu reflete apenas serviços reais

### 2. Coleta Eficiente
- 📋 Orçamentos: Coleta completa (nome, tel, CPF, receita)
- ⚡ Outros: Coleta rápida (nome, tel, CPF)

### 3. Melhor Experiência
- Cliente não precisa responder perguntas desnecessárias
- Formulário mais rápido para ajustes e reparos

### 4. Notificações Claras
- Grupo só recebe info de receita quando relevante
- Atendentes sabem exatamente o que o cliente precisa

---

## 🚀 Como Aplicar as Mudanças

### 1. Reiniciar o Bot
```bash
python script.py
```

### 2. Verificar Menu
- Enviar mensagem de saudação
- Confirmar que aparece menu 1-6 (sem opção 7)
- Confirmar que opção 2 é "Fazer orçamento"

### 3. Testar Orçamento
- Selecionar opção 2
- Preencher formulário
- Confirmar que PEDE receita

### 4. Testar Outras Opções
- Selecionar opção 3, 4, 5 ou 6
- Preencher formulário
- Confirmar que NÃO pede receita

---

## 📝 Checklist de Validação

- [ ] Menu mostra 6 opções (não 7)
- [ ] Opção 2 é "Fazer orçamento de óculos"
- [ ] "Agendar exame de vista" não aparece
- [ ] Opção 2 pede receita médica
- [ ] Opções 3, 4, 5, 6 NÃO pedem receita
- [ ] Confirmação para orçamento inclui receita
- [ ] Confirmação para outros NÃO inclui receita
- [ ] Notificação ao grupo mostra receita só para orçamentos
- [ ] CPF formatado como XXX.XXX.XXX-XX

---

## 🔍 Logs Importantes

### Orçamento (com receita):
```
Started customer form for ... - reason: 2 - Fazer orçamento de óculos
Updated customer form for ... - step: prescription
Customer form sent to group for ...
```

### Outras opções (sem receita):
```
Started customer form for ... - reason: 3 - Ajustes e reparos
Updated customer form for ... - step: confirm  (pula "prescription")
Customer form sent to group for ...
```

---

## ⚠️ Observações

1. **Código de detecção**: Identifica orçamento por:
   - Presença de "2 -" no motivo (opção 2)
   - Palavra "orçamento" no motivo

2. **Compatibilidade**: Funciona com:
   - Menu direto (opção 2)
   - Solicitação via IA (palavra "orçamento")

3. **Valores padrão**:
   - Outras opções: `"Não solicitado (apenas para orçamentos)"`
   - Campo oculto na notificação ao grupo

---

## 📞 Suporte

Se encontrar problemas:
1. Verificar logs: `whatsapp_bot.log`
2. Buscar por: `"Started customer form"` e `"step: prescription"`
3. Confirmar que opções 3-6 pulam para `"step: confirm"`

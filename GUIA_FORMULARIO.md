# 📋 Guia Rápido - Sistema de Coleta de Dados

## 🎯 O Que Mudou?

Agora, quando o cliente **solicitar atendimento** (opções 2, 3, 4, 6 do menu ou pedir para falar com consultor), o bot vai **coletar informações** antes de notificar os atendentes:

1. ✅ **Nome completo**
2. ✅ **Telefone**
3. ✅ **CPF**
4. ✅ **Receita médica** (se tiver)

---

## 🔄 Como Funciona

### Para o Cliente

```
Cliente escolhe opção 2, 3, 4 ou 6
        ↓
Bot pede: NOME
        ↓
Bot pede: TELEFONE  
        ↓
Bot pede: CPF
        ↓
Bot pede: RECEITA (foto/PDF ou "não")
        ↓
Bot mostra RESUMO
        ↓
Cliente confirma com "SIM"
        ↓
✅ ATENDENTES recebem TUDO no grupo
```

### Para os Atendentes

Agora você recebe no grupo:

```
🔔 NOVA SOLICITAÇÃO DE ATENDIMENTO

⏰ Horário: 20/10/2025 às 14:30
📋 Motivo: 2 - Agendar exame de vista

👤 DADOS DO CLIENTE
• Nome: João da Silva
• Telefone: 81999887766
• WhatsApp: 5581999887766
• CPF: 123.456.789-01

💊 RECEITA MÉDICA
📷 Receita enviada (imagem)
URL: https://...

---
Atender o cliente com o WhatsApp dele
```

---

## ⚡ Teste Rápido

### 1️⃣ Reinicie o Bot
```bash
python script.py
```

### 2️⃣ Teste Básico
```
Você (cliente): 2
Bot: [Resposta da opção + pede NOME]

Você: Maria Silva
Bot: [Pede TELEFONE]

Você: 81999887766
Bot: [Pede CPF]

Você: 12345678901
Bot: [Pede RECEITA]

Você: não
Bot: [Mostra RESUMO e pede confirmação]

Você: sim
Bot: ✅ Enviado para consultores!

✅ Verifique grupo de notificações - deve ter TODOS os dados
```

### 3️⃣ Teste com Receita
```
[... mesmo fluxo até pedir receita ...]

Bot: Você possui receita médica?
Você: [Envia FOTO da receita] 📸

Bot: [Mostra resumo com "Receita enviada (imagem)"]
Você: sim

✅ Grupo recebe com LINK da receita
```

---

## 📋 Checklist

Verifique se está funcionando:

- [ ] Bot inicia sem erros
- [ ] Opção 2, 3, 4 ou 6 inicia formulário
- [ ] Bot pede nome → telefone → CPF → receita
- [ ] Validações funcionam (telefone < 10 dígitos rejeitado, etc.)
- [ ] Bot aceita foto/PDF de receita
- [ ] Bot mostra resumo antes de enviar
- [ ] Grupo recebe notificação com TODOS os dados
- [ ] CPF aparece formatado: `123.456.789-01`

---

## 🐛 Problemas Comuns

### Bot Não Pede Dados
**Sintoma**: Cliente escolhe opção mas bot não inicia formulário

**Solução**:
1. Verifique se é opção 2, 3, 4 ou 6
2. Verifique logs: `grep "Started customer form" whatsapp_bot.log`
3. Se não aparecer, reinicie o bot

### Validação Não Funciona
**Sintoma**: Aceita telefone com 5 dígitos, etc.

**Solução**:
1. Verifique código da função `process_customer_form_step()`
2. Teste com dados inválidos
3. Veja logs de erro

### Grupo Não Recebe Notificação
**Sintoma**: Cliente confirma mas atendentes não recebem

**Solução**:
1. Verifique: `grep "Customer form sent to group" whatsapp_bot.log`
2. Verifique `NOTIFICATION_GROUP_ID` no `.env`
3. Teste envio manual para grupo

### Formulário Expira
**Sintoma**: Cliente demora e perde progresso

**Resposta**: Normal! Expira em 10 minutos.

**Solução**: Cliente deve recomeçar mais rápido ou aumentar `CUSTOMER_FORM_TTL` no código

---

## 💡 Dicas

### Para Atendentes

✅ **Todos os dados estão na notificação** - não precisa pedir de novo

✅ **Link da receita está lá** - clique para ver (se cliente enviou)

✅ **CPF já formatado** - fácil de ler e copiar

### Para Clientes

✅ **Siga o passo a passo** - bot guia você

✅ **Revise antes de confirmar** - todos os dados são mostrados

✅ **Pode cancelar** - digite "não" na confirmação

### Para Configuração

✅ **10 minutos é tempo suficiente** - maioria completa em 2-3 min

✅ **Opções 1, 5, 7 NÃO pedem dados** - são informativas

✅ **IA pode iniciar formulário** - se sugerir contato com consultor

---

## 📊 Logs para Monitorar

### Formulário Funcionando ✅
```bash
grep "Started customer form" whatsapp_bot.log
grep "Updated customer form" whatsapp_bot.log
grep "Customer form sent to group" whatsapp_bot.log
```

### Problemas ❌
```bash
grep "Error sending customer form" whatsapp_bot.log
grep "Expired customer form" whatsapp_bot.log
grep "Cancelled customer form" whatsapp_bot.log
```

---

## 🎊 Pronto!

Agora os atendentes recebem:
- ✅ Nome do cliente
- ✅ Telefone de contato  
- ✅ CPF para cadastro
- ✅ Receita médica (quando houver)
- ✅ Motivo do atendimento

**Tudo organizado e pronto para usar!** 🚀

---

**Versão**: 1.2.0  
**Data**: 20/10/2025

**Qualquer dúvida, verifique**: `FORMULARIO_COLETA_DADOS.md` (documentação completa)

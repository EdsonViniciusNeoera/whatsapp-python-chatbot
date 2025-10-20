# 📋 Sistema de Coleta de Dados do Cliente

## 🎯 Objetivo

Antes de notificar os atendentes sobre uma nova solicitação, o bot agora coleta informações completas do cliente:
- ✅ Nome completo
- ✅ Telefone de contato
- ✅ CPF
- ✅ Receita médica (se houver)

Isso permite que os atendentes tenham **todas as informações necessárias** antes de iniciar o atendimento.

---

## 🔄 Como Funciona

### Fluxo do Cliente

```
1. Cliente escolhe opção do menu (2, 3, 4 ou 6) OU pede para falar com consultor
   ↓
2. Bot mostra resposta da opção + inicia coleta de dados
   ↓
3. Bot pede: NOME
   Cliente: "João da Silva"
   ↓
4. Bot pede: TELEFONE
   Cliente: "81999887766"
   ↓
5. Bot pede: CPF
   Cliente: "12345678901"
   ↓
6. Bot pede: RECEITA (sim/não ou enviar foto/PDF)
   Cliente: Envia foto OU escreve "não"
   ↓
7. Bot mostra resumo e pede confirmação
   Cliente: "sim"
   ↓
8. ✅ Bot envia TODAS as informações para o grupo de atendentes
   ↓
9. Cliente recebe confirmação
```

---

## 📝 Exemplo de Conversa

### Opção de Menu que Requer Atendente

```
Cliente: 2

Bot: 👓 Perfeito! Para agendar seu exame de vista, vou encaminhar você 
para um de nossos consultores especializados.

Você prefere falar com:
• Jailson - (81) 99750-7161
• Josimar - (81) 99974-5545

Digite o nome do consultor ou ligue diretamente! 📞

📋 Para que nossos consultores possam te atender melhor, preciso de 
algumas informações.

👤 Por favor, me diga seu nome completo:

Cliente: João da Silva

Bot: Ótimo! Agora, qual seu telefone para contato?
(Digite apenas números)

Cliente: 81999887766

Bot: Perfeito! Agora preciso do seu CPF:
(Digite apenas números)

Cliente: 12345678901

Bot: Ótimo! Você possui receita médica?

✅ Se SIM: Envie uma foto ou PDF da receita
❌ Se NÃO: Digite 'não' ou 'nao'

Cliente: [Envia foto da receita]

Bot: 📋 Confirmação dos Dados

👤 Nome: João da Silva
📱 Telefone: 81999887766
🆔 CPF: 123.456.789-01
💊 Receita: 📷 Receita enviada (imagem)
URL: https://...

Motivo do contato: 2 - Agendar exame de vista

Seus dados estão corretos?

✅ Digite SIM para confirmar
❌ Digite NÃO para recomeçar

Cliente: sim

Bot: ✅ Perfeito! Suas informações foram enviadas para nossos consultores.

Eles entrarão em contato com você em breve! 😊

Posso ajudar com mais alguma coisa?
```

---

## 📱 Notificação no Grupo de Atendentes

Quando o cliente confirma os dados, os atendentes recebem:

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
URL: https://media.whatsapp.com/...

⚠️ Verifique a receita antes de confirmar o atendimento

---
Atender o cliente iniciando conversa com o WhatsApp dele
```

---

## 🔧 Situações que Ativam o Formulário

### 1. Opções do Menu
Quando cliente escolhe:
- **Opção 2** - Agendar exame de vista
- **Opção 3** - Fazer orçamento de óculos
- **Opção 4** - Ajustes e reparos
- **Opção 6** - Falar com consultor

### 2. IA Detecta Necessidade de Atendente
Quando a IA menciona:
- "Jailson"
- "Josimar"
- "consultor"
- "especialista"
- "atendimento"

---

## ✅ Validações Implementadas

### Nome
- ✅ Deve ter pelo menos 2 caracteres
- ✅ Aceita qualquer texto (nomes compostos, sobrenomes, etc.)

### Telefone
- ✅ Remove caracteres não numéricos automaticamente
- ✅ Deve ter pelo menos 10 dígitos (DDD + número)
- ❌ Rejeita se menor que 10 dígitos

### CPF
- ✅ Remove caracteres não numéricos automaticamente
- ✅ Deve ter exatamente 11 dígitos
- ✅ Formata automaticamente: `123.456.789-01`
- ❌ Rejeita se não tiver 11 dígitos

### Receita Médica
- ✅ Detecta se cliente enviou **imagem** (JPG, PNG, etc.)
- ✅ Detecta se cliente enviou **documento/PDF**
- ✅ Captura a URL do arquivo para os atendentes
- ✅ Aceita resposta em texto: "não", "nao", "sim", etc.
- ⚠️ Se cliente diz "sim" mas não envia arquivo, pede novamente

---

## 🎛️ Controles e Opções

### Cancelar Formulário
Cliente pode digitar:
- "não" (na confirmação)
- "nao"
- "cancelar"
- "recomeçar"

O formulário é cancelado e cliente pode começar de novo.

### Expiração Automática
- Formulários expiram após **10 minutos** de inatividade
- Cliente precisa recomeçar se passar do tempo

### Interrupção
- Se cliente envia **nova mensagem** antes de completar, formulário continua
- Cliente pode mudar de assunto digitando palavras-chave do menu ("oi", "menu", etc.)

---

## 🗂️ Armazenamento de Dados

### Cache em Memória
```python
customer_forms = {
    '5581999887766_s_whatsapp_net': {
        'step': 'cpf',  # Passo atual
        'data': {
            'name': 'João da Silva',
            'phone': '81999887766'
        },
        'timestamp': 1697825400.0,
        'reason': '2 - Agendar exame de vista'
    }
}
```

### TTL (Time To Live)
- **10 minutos** para coleta de dados
- Limpeza automática de formulários expirados

---

## 📊 Etapas do Formulário

| Etapa | Campo | Validação | Próxima Etapa |
|-------|-------|-----------|---------------|
| `name` | Nome completo | >= 2 caracteres | `phone` |
| `phone` | Telefone | >= 10 dígitos numéricos | `cpf` |
| `cpf` | CPF | Exatamente 11 dígitos | `prescription` |
| `prescription` | Receita médica | Imagem/PDF ou texto | `confirm` |
| `confirm` | Confirmação | "sim" ou "não" | Envia ou cancela |

---

## 🔍 Logs de Monitoramento

### Formulário Iniciado
```log
INFO - Started customer form for 5581999887766_s_whatsapp_net - reason: 2 - Agendar exame de vista
```

### Progresso do Formulário
```log
INFO - Updated customer form for 5581999887766_s_whatsapp_net - step: phone
INFO - Updated customer form for 5581999887766_s_whatsapp_net - step: cpf
INFO - Updated customer form for 5581999887766_s_whatsapp_net - step: prescription
```

### Formulário Concluído
```log
INFO - ✅ Customer form sent to group for 5581999887766
```

### Formulário Cancelado
```log
INFO - Cancelled customer form for 5581999887766_s_whatsapp_net
```

### Formulário Expirado
```log
INFO - Expired customer form for 5581999887766_s_whatsapp_net
```

---

## 🛠️ Funções Principais

### Gerenciamento do Formulário

```python
start_customer_form(safe_sender_id, reason)
# Inicia coleta de dados com motivo específico

get_customer_form(safe_sender_id)
# Retorna formulário ativo ou None

update_customer_form(safe_sender_id, step, data_key, data_value)
# Atualiza passo e dados do formulário

cancel_customer_form(safe_sender_id)
# Cancela formulário em andamento

cleanup_customer_forms()
# Remove formulários expirados
```

### Processamento

```python
process_customer_form_step(safe_sender_id, sender_number, message_text, message_info)
# Processa uma etapa do formulário
# Retorna texto de resposta ou None se completo

send_customer_form_to_group(customer_number, form)
# Envia dados completos para grupo de atendentes
```

---

## ⚠️ Tratamento de Erros

### Cliente Envia Dados Inválidos
- ✅ Bot pede novamente com mensagem explicativa
- ✅ Não avança para próximo passo até dados válidos

### Cliente Fica Inativo
- ✅ Formulário expira após 10 minutos
- ✅ Limpeza automática libera memória

### Cliente Tenta Usar Outras Funcionalidades
- ✅ Formulário permanece ativo
- ✅ Cliente pode cancelar e começar de novo
- ✅ Palavras-chave de saudação (`oi`, `menu`) cancelam formulário

### Erro ao Enviar para Grupo
- ❌ Log de erro detalhado
- ✅ Cliente ainda recebe confirmação
- ⚠️ Atendentes não são notificados (verificar logs)

---

## 🎯 Benefícios

### Para os Atendentes
✅ **Informações completas** antes do contato  
✅ **CPF para identificação** do cliente  
✅ **Receita médica anexada** (se houver)  
✅ **Contexto do atendimento** (motivo)  
✅ **Dados organizados** em mensagem formatada  

### Para os Clientes
✅ **Processo guiado** passo a passo  
✅ **Validação imediata** dos dados  
✅ **Confirmação visual** antes de enviar  
✅ **Opção de cancelar** e recomeçar  
✅ **Feedback claro** sobre cada etapa  

### Para o Sistema
✅ **Padronização** da coleta de dados  
✅ **Redução de erros** (validação automática)  
✅ **Rastreabilidade** completa (logs)  
✅ **Expiração automática** (gerenciamento de memória)  
✅ **Integração** com sistema de cancelamento  

---

## 🧪 Como Testar

### Teste 1: Formulário Completo com Receita
```
1. Cliente: "2" (Agendar exame)
2. Digite nome: "Maria Silva"
3. Digite telefone: "11987654321"
4. Digite CPF: "98765432100"
5. Envie foto da receita
6. Confirme: "sim"
✅ Verificar notificação no grupo com todos os dados
```

### Teste 2: Formulário sem Receita
```
1. Cliente: "3" (Orçamento)
2. Digite nome: "Pedro Santos"
3. Digite telefone: "21999887766"
4. Digite CPF: "11122233344"
5. Digite: "não" (sem receita)
6. Confirme: "sim"
✅ Verificar notificação indica "sem receita"
```

### Teste 3: Validações
```
1. Cliente: "6" (Falar com consultor)
2. Nome: "A" ❌ (muito curto)
   Bot pede novamente
3. Nome: "Ana Costa" ✅
4. Telefone: "123" ❌ (muito curto)
   Bot pede novamente
5. Telefone: "85988776655" ✅
6. CPF: "123" ❌ (não tem 11 dígitos)
   Bot pede novamente
7. CPF: "12345678900" ✅
```

### Teste 4: Cancelamento
```
1. Cliente: "2"
2. Nome: "João Teste"
3. Telefone: "11999999999"
4. CPF: "00011122233"
5. Receita: "não"
6. Confirmação: "não" ❌ (cancelar)
✅ Bot confirma cancelamento
✅ Cliente pode recomeçar
```

---

## 📁 Arquivos Modificados

### `script.py`

#### Variáveis Globais Adicionadas
```python
customer_forms = {}
CUSTOMER_FORM_TTL = 600  # 10 minutos
```

#### Novas Funções
- `start_customer_form()` - Inicia formulário
- `get_customer_form()` - Obtém formulário ativo
- `update_customer_form()` - Atualiza dados/passo
- `cancel_customer_form()` - Cancela formulário
- `cleanup_customer_forms()` - Limpa expirados
- `process_customer_form_step()` - Processa etapa
- `send_customer_form_to_group()` - Envia para grupo

#### Webhook Modificado
- Verifica formulário ativo antes de processar
- Inicia formulário quando necessário (opções 2,3,4,6 ou IA)
- Removido envio direto para grupo (agora via formulário)

---

## 🚀 Próximos Passos Sugeridos

### Melhorias Futuras

1. **Validação de CPF**
   - Verificar dígitos verificadores
   - Rejeitar CPFs inválidos

2. **Formatação de Telefone**
   - Adicionar DDD e formatação: `(81) 99988-7766`

3. **Upload de Receita**
   - Armazenar receita em servidor/cloud
   - Gerar link permanente para atendentes

4. **Histórico de Formulários**
   - Salvar formulários completados em banco de dados
   - Recuperar dados de clientes recorrentes

5. **Campos Opcionais**
   - Email do cliente
   - Data de nascimento
   - Preferência de contato

6. **Notificação Individual**
   - Permitir cliente escolher: Jailson ou Josimar
   - Enviar notificação para consultor específico

---

**Status**: ✅ **IMPLEMENTADO E FUNCIONANDO**  
**Data**: 20 de outubro de 2025  
**Versão**: 1.2.0

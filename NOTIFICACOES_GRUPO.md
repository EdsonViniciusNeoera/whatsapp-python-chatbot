# Sistema de Notificações para Grupo - GGDISK Ótica

## Visão Geral

O bot agora possui um sistema integrado de notificações que envia alertas automáticos para o grupo "GGDISK - Notificações" quando clientes solicitam atendimento especializado.

## 🔧 Configuração

### 1. ID do Grupo

O ID do grupo atual é: `120363404721021632@g.us`

Para configurar no arquivo `.env`:

```env
NOTIFICATION_GROUP_ID=120363404721021632@g.us
```

### 2. Verificar ID do Grupo

Se precisar confirmar ou encontrar o ID do grupo novamente:

1. Envie uma mensagem manualmente para o grupo pelo WhatsApp
2. Verifique o arquivo `whatsapp_bot.log`
3. Procure por linhas contendo `@g.us`

## 📋 Situações que Disparam Notificações

### Opções do Menu Interativo

As seguintes opções do menu **disparam notificações automáticas**:

- **Opção 2** - Agendar exame de vista
- **Opção 3** - Fazer orçamento de óculos
- **Opção 4** - Ajustes e reparos
- **Opção 6** - Falar com consultor

### Respostas da IA

Quando a IA (Gemini) menciona qualquer uma dessas palavras-chave na resposta:
- `jailson`
- `josimar`
- `consultor`
- `especialista`
- `atendimento`

## 📨 Formato da Notificação

Quando um cliente solicita atendimento, o grupo recebe:

```
🔔 NOVA SOLICITAÇÃO DE ATENDIMENTO

👤 Cliente: 5581XXXXXXXXX
⏰ Horário: 18/10/2025 às 16:30

📋 Opção do menu: 2 - Agendar exame de vista

📝 Mensagem:
Preciso marcar um exame de vista

---
Atender o cliente iniciando conversa com o número dele
```

## 🎯 Benefícios

- ✅ Notificação instantânea dos atendentes
- ✅ Contexto completo da solicitação do cliente
- ✅ Número do cliente para contato direto
- ✅ Horário preciso da solicitação
- ✅ Histórico de notificações no grupo

## 🔍 Logs e Monitoramento

Todas as notificações são registradas no arquivo `whatsapp_bot.log`:

```
2025-10-18 16:30:00,000 - INFO - whatsapp_bot - ✅ Notification sent to group for customer 5581XXXXXXXXX
```

## 🛠️ Manutenção

### Desabilitar Notificações

Para desabilitar temporariamente:

1. Remova ou comente a linha no `.env`:
   ```env
   # NOTIFICATION_GROUP_ID=120363404721021632@g.us
   ```

2. Reinicie o bot

### Alterar Grupo de Notificações

1. Crie um novo grupo no WhatsApp
2. Adicione o número do bot ao grupo
3. Envie uma mensagem no grupo
4. Pegue o ID no log (formato: `XXXXXXXXXX@g.us`)
5. Atualize o `.env` com o novo ID
6. Reinicie o bot

### Adicionar Novas Situações de Notificação

Para adicionar mais opções do menu que devem notificar:

Edite `script.py`, linha com `if option_key in ['2', '3', '4', '6']:`:

```python
if option_key in ['2', '3', '4', '6', '7']:  # Adicione '7' ou outros
```

Para adicionar mais palavras-chave da IA:

Edite `script.py`, linha com `keywords_for_notification`:

```python
keywords_for_notification = ['jailson', 'josimar', 'consultor', 'especialista', 'atendimento', 'nova_palavra']
```

## 📞 Contatos dos Atendentes

Conforme configurado no `persona.json`:

- **Jailson**: (81) 99750-7161
- **Josimar**: (81) 99974-5545

## ⚠️ Importante

- O bot **NÃO** responde mensagens enviadas diretamente no grupo de notificações
- As notificações são **apenas informativas**
- Os atendentes devem iniciar conversa **direta** com o cliente usando o número fornecido
- O grupo serve apenas para alertas, não para atendimento

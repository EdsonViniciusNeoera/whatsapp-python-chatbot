# 📝 CHANGELOG

Registro de todas as mudanças notáveis neste projeto.

---

## [1.1.1] - 2025-10-23

### 🔧 Corrigido

#### Lógica do Formulário - Detecção de Intenção
**Problema:** Bot iniciava formulário sempre que a IA mencionava consultores, causando duplicação.

**Exemplo do Bug:**
```
Bot: "Nossos consultores: Jailson e Josimar..."
Cliente: "Prefiro falar com josimar"
Bot: "Ótimo! Vou avisar..." + "📋 Escolha consultor: 01 ou 02?" ❌
```

**Solução:** Mudança da lógica para detectar intenção real do usuário:
- ✅ Baseado na **mensagem do usuário**, não na resposta da IA
- ✅ Detecta frases explícitas: "quero falar com", "prefiro falar com", etc.
- ✅ Requer menção explícita do nome do consultor
- ✅ Precisão: 94.7% (18/19 testes)

**Arquivos Modificados:**
- `script.py` - Função de processamento de mensagens (linhas ~1265-1305)
- `test_form_logic.py` - Teste automatizado criado

**Comportamento Correto:**
| Mensagem | Inicia Formulário? |
|----------|-------------------|
| "Qual o telefone do Jailson?" | ❌ Não |
| "Quero falar com o Josimar" | ✅ Sim |
| "Qual o endereço?" | ❌ Não |
| "Quero fazer orçamento" | ✅ Sim |

---

## [1.1.0] - 2025-10-23

### ✨ Melhorado

#### Mensagens Mais Inteiras - Redução de Fragmentação
**Problema:** Mensagens sendo quebradas em múltiplas partes muito pequenas.

**Antes:**
- ❌ Máximo de **3 linhas** por mensagem
- ❌ Máximo de **100 caracteres** por linha
- ❌ Mensagens simples quebradas em 2-3 partes

**Depois:**
- ✅ Máximo de **10 linhas** por mensagem (aumento de 233%)
- ✅ Máximo de **400 caracteres** por linha (aumento de 300%)
- ✅ Threshold mais generoso: até 20 linhas ou 800 chars sem quebrar
- ✅ Mensagens até **70% mais inteiras**

**Resultados dos Testes:**
| Tamanho | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Curta | 1 chunk | 1 chunk | = |
| Média (181 chars) | 3-4 chunks | 1 chunk | -75% |
| Longa (744 chars) | 5-6 chunks | 1 chunk | -83% |
| Muito Longa (2070 chars) | 8+ chunks | 1 chunk | -87% |

**Arquivos Modificados:**
- `message_splitter.py` - Limites aumentados
- `script.py` - CONFIG atualizado
- `persona.json` - Instrução para respostas completas
- `test_message_split.py` - Script de teste criado

**Benefícios:**
- 🎯 Melhor UX - Mensagens mais completas e coesas
- ⚡ Menos Delays - Menos interrupções entre mensagens
- 💰 Economia - Menos requisições à API
- ✅ Compatibilidade - Margem de 5-20x do limite do WhatsApp (4096 chars)

---

## [1.0.0] - 2025-10-15

### 🚀 Versão Inicial

#### Funcionalidades Principais

**Sistema de IA:**
- ✅ Integração com Google Gemini 2.0 Flash
- ✅ Few-Shot Learning (17 exemplos de treinamento)
- ✅ System Instructions (persona "Pedro")
- ✅ Histórico de conversas (até 40 mensagens por usuário)

**Menu Interativo:**
- ✅ 6 opções pré-definidas
- ✅ Detecção automática de saudações
- ✅ Respostas instantâneas (sem API)

**Sistema de Formulários:**
- ✅ Coleta estruturada de dados do cliente
- ✅ 6 etapas: consultor, nome, telefone, CPF, receita, confirmação
- ✅ Validação em cada etapa
- ✅ Suporte a imagens e documentos (receitas)
- ✅ Notificação para grupo de atendimento

**Integrações:**
- ✅ WhatsApp via WaSenderAPI ($6/mês)
- ✅ Google Gemini AI (gratuito - 1500 req/mês)
- ✅ Flask webhook server
- ✅ Ngrok para desenvolvimento

**Recursos de Segurança:**
- ✅ Deduplicação de mensagens (TTL: 5 min)
- ✅ Gerenciamento de sessões
- ✅ Retry automático (3 tentativas)
- ✅ Logging completo
- ✅ Tratamento global de erros

**Testes:**
- ✅ Suite completa de testes automatizados
- ✅ 8 arquivos de teste
- ✅ Cobertura de componentes principais

---

## 📋 Tipos de Mudanças

- ✨ **Adicionado** - Novas funcionalidades
- 🔧 **Corrigido** - Correções de bugs
- ✨ **Melhorado** - Melhorias em funcionalidades existentes
- 🗑️ **Removido** - Funcionalidades removidas
- 🔒 **Segurança** - Correções de vulnerabilidades

---

## 🔗 Links Úteis

- [README.md](README.md) - Documentação principal
- [Repositório GitHub](https://github.com/EdsonViniciusNeoera/whatsapp-python-chatbot)
- [WaSenderAPI Docs](https://wasenderapi.com/api-docs)
- [Google Gemini API](https://ai.google.dev/)

---

**Formato:** Baseado em [Keep a Changelog](https://keepachangelog.com/)  
**Versionamento:** [Semantic Versioning](https://semver.org/)

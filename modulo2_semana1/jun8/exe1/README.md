# Exercício 1 — Agente de Suporte Básico (Sem Tool Calling)

## O que esse exercício ensina

A diferença entre um agente que chama ferramentas de forma **manual e hardcoded** versus um agente com tool calling real. Aqui você vê a versão mais simples: o código Python controla tudo, o LLM só resume texto.

---

## O problema a resolver

Você tem uma tabela `conversations` no banco com conversas de tickets de suporte. O objetivo é:

1. Buscar a conversa de um ticket específico
2. Classificar o problema (login, pagamento, entrega, etc.)
3. Detectar se o ticket precisa de follow-up
4. Gerar um resumo via LLM
5. Salvar tudo na tabela `agent_runs` do banco

---

## Arquitetura

```
support_agent_basic.py   ← Agente principal
tools.py                 ← Funções utilitárias (banco, classificação, follow-up)
```

### Fluxo de execução

```
ticket_id
    ↓
get_ticket_conversation()   → busca conversa no banco (SQL)
    ↓
classify_category()         → classifica por regras Python simples (sem LLM)
    ↓
detect_followup()           → detecta se último a falar foi o atendente
    ↓
summarize()                 → Ollama/LLM gera um resumo curto
    ↓
save_agent_run()            → salva resultado na tabela agent_runs
```

---

## Como funciona cada parte

### `tools.py`

| Função | O que faz |
|---|---|
| `get_ticket_conversation()` | Busca mensagens do ticket no PostgreSQL, ordenadas por timestamp |
| `classify_category()` | Regra simples: procura palavras-chave ("login", "senha", "pagamento") no texto |
| `detect_followup()` | Verifica se a última linha começa com "atendente:" — se sim, precisa de follow-up |
| `save_agent_run()` | Insere o resultado na tabela `agent_runs` no banco |

### `support_agent_basic.py`

A classe `SupportTicketAgentBasic` conecta ao Ollama (API compatível com OpenAI) e:
- Chama as tools manualmente, uma por uma, na ordem hardcoded
- Usa o LLM **apenas** para gerar o resumo da conversa
- O LLM não decide o que fazer — ele só processa texto quando o código manda

---

## Diferença fundamental: agente básico vs. agente com tool calling

| Característica | Exe 1 (básico) | Exe 2 (tool calling) |
|---|---|---|
| Quem controla o fluxo | O código Python | O LLM |
| O LLM decide o que chamar? | Não | Sim |
| Tools são descritas para o LLM? | Não | Sim |
| Flexibilidade | Baixa | Alta |

---

## Pré-requisitos

- PostgreSQL rodando na porta `5450` (via Docker/Podman)
- Ollama rodando em `http://localhost:11434` com o modelo `llama3.2`
- Variáveis de ambiente (`.env` na raiz do projeto):
  ```
  OLLAMA_BASE_URL=http://localhost:11434/v1
  OLLAMA_MODEL=llama3.2
  DB_HOST=localhost
  ```

---

## Como rodar

```bash
# Na pasta exe1
python support_agent_basic.py
```

O script salva os resultados na tabela `agent_runs` do banco **e** gera um arquivo local `results_exe1.json` para análise posterior.

---

## Saída esperada

```json
{
  "ticket_id": 1001,
  "categoria": "login",
  "resumo": "O usuário relatou problema ao fazer login...",
  "precisa_followup": false,
  "motivo_followup": "cliente respondeu por último"
}
```

---

## Tabelas do banco usadas

| Tabela | Operação |
|---|---|
| `conversations` | SELECT — lê as mensagens do ticket |
| `agent_runs` | INSERT — salva o resultado da execução |

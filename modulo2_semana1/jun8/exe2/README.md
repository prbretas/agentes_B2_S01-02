# Exercício 2 — Agente de Suporte com Tool Calling

## O que esse exercício ensina

Como usar **tool calling real**: o LLM decide autonomamente quais ferramentas chamar, em qual ordem e com quais argumentos. O código Python apenas descreve as tools disponíveis e executa o que o modelo pede.

---

## O problema a resolver

Mesmo cenário do exercício 1 (tickets de suporte na tabela `conversations`), mas agora o LLM assume o controle do fluxo:

1. Buscar a conversa de um ticket específico
2. Classificar o problema via LLM (não mais por palavras-chave)
3. Detectar se o ticket precisa de follow-up
4. Gerar uma resposta final em JSON com análise completa
5. Salvar tudo na tabela `agent_runs` do banco

---

## Arquitetura

```
support_agent_toolcalling.py  ← Agente principal com loop de tool calling
classification.py             ← Classificação via LLM (standalone)
tools.py                      ← Funções utilitárias + TOOL_MAP
```

### Fluxo de execução

```
ticket_id
    ↓
LLM recebe system prompt + lista de tools
    ↓
LLM decide chamar get_ticket_conversation()   → busca conversa no banco
    ↓
LLM decide chamar classify_category_prompt()  → classifica via Ollama/LLM
    ↓
LLM decide chamar detect_followup()           → detecta necessidade de follow-up
    ↓
LLM gera JSON final com análise completa
    ↓
save_agent_run()                              → salva resultado na tabela agent_runs
```

---

## Como funciona cada parte

### `tools.py`

| Função | O que faz |
|---|---|
| `get_ticket_conversation()` | Busca mensagens do ticket no PostgreSQL, ordenadas por timestamp |
| `classify_category_prompt()` | Classifica via Ollama — o LLM lê a conversa e retorna a categoria em JSON |
| `detect_followup()` | Verifica se a última mensagem foi do atendente (precisa de resposta do cliente) |
| `save_agent_run()` | Insere o resultado na tabela `agent_runs` no banco |
| `TOOL_MAP` | Dicionário que mapeia nome da função → função Python, usado para executar as tool calls |

### `support_agent_toolcalling.py`

A classe `SupportTicketAgentToolCalling`:
- Define as tools como schemas JSON (descrição, parâmetros e tipos)
- Envia o schema das tools para o LLM junto com a mensagem do usuário
- Executa um **loop de tool calling**: enquanto o LLM retornar `tool_calls`, executa as funções e devolve os resultados
- Encerra quando o LLM não pede mais tools e retorna o JSON final

### `classification.py`

Script standalone que demonstra a classificação via LLM de forma isolada, sem o loop completo do agente.

---

## Diferença fundamental: agente básico vs. agente com tool calling

| Característica | Exe 1 (básico) | Exe 2 (tool calling) |
|---|---|---|
| Quem controla o fluxo | O código Python | O LLM |
| O LLM decide o que chamar? | Não | Sim |
| Tools são descritas para o LLM? | Não | Sim (schema JSON) |
| Classificação | Palavras-chave hardcoded | LLM via Ollama |
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
# Agente completo com tool calling
python support_agent_toolcalling.py

# Apenas a classificação via LLM (standalone)
python classification.py
```

---

## Saída esperada

```json
{
  "ticket_id": 1001,
  "categoria": "login",
  "resumo": "O usuário relatou problema ao fazer login na conta...",
  "precisa_followup": false,
  "motivo_followup": "última mensagem foi do cliente",
  "status_sugerido": "resolvido"
}
```

---

## Tabelas do banco usadas

| Tabela | Operação |
|---|---|
| `conversations` | SELECT — lê as mensagens do ticket |
| `agent_runs` | INSERT — salva o resultado da execução |

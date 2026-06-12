# Exercício — Contrato de Dados com Pydantic

## Objetivo

Neste exercício, você vai aprender como usar **Pydantic** para criar um **contrato de dados**.

Um contrato de dados define:

- Quais campos são obrigatórios
- Quais tipos cada campo deve ter
- Quais valores são permitidos
- Quais regras de negócio precisam ser respeitadas
- O que acontece quando os dados chegam inválidos

Esse conceito é muito importante em aplicações com IA, porque modelos podem gerar respostas inconsistentes.

---

## Cenário

Você está construindo um agente que analisa feedbacks de usuários.

O modelo deve retornar uma resposta estruturada como JSON:

```json
{
  "sentiment": "negative",
  "category": "bug",
  "priority": "high",
  "summary": "User reports that the app crashes during payment.",
  "confidence": 0.92
}
```

Mas o modelo pode errar.

Exemplos de erros:

```json
{
  "sentiment": "bad",
  "category": "bug",
  "priority": "urgent",
  "summary": "",
  "confidence": 1.8
}
```

Problemas:

- `sentiment` deveria ser `positive`, `neutral` ou `negative`
- `priority` deveria ser `low`, `medium` ou `high`
- `summary` não pode ser vazio
- `confidence` precisa estar entre 0 e 1

O Pydantic ajuda a validar isso.

---

## Conceitos trabalhados

- Data contract
- Validação de JSON
- Pydantic BaseModel
- Enum
- Field
- Validação de tipos
- Validação de valores permitidos
- Validação customizada
- Fallback seguro
- Retry quando a resposta do modelo é inválida

---

## Por que isso importa em IA?

Quando usamos LLMs em sistemas reais, a resposta do modelo não pode ser tratada como confiável automaticamente.

O modelo pode:

- Esquecer campos
- Inventar campos
- Retornar texto em vez de JSON
- Retornar tipos errados
- Usar valores fora do combinado
- Gerar uma saída que parece certa, mas quebra o pipeline

Por isso, antes de salvar no banco ou chamar outra ferramenta, validamos a resposta.

---

## Arquitetura

```text
Usuário
   ↓
LLM gera JSON
   ↓
Pydantic valida contrato
   ↓
Se válido: segue o fluxo
   ↓
Se inválido: bloqueia, corrige ou tenta novamente
```

---

## Estrutura do projeto

```text
pydantic_data_contract_exercicio/
├── README.md
├── solution.py
├── llm_solution.py
├── requirements.txt
└── .env.example
```

---

## Instalação

```bash
pip install -r requirements.txt
```

Para a versão com LLM, crie um arquivo `.env`:

```env
OPENAI_API_KEY=sua_chave_openai
```

---

## Rodando a versão sem LLM

```bash
python solution.py
```

Essa versão mostra validações com exemplos fixos.

---

## Rodando a versão com LLM

```bash
python llm_solution.py
```

Essa versão chama a OpenAI, pede uma saída JSON e valida com Pydantic.

---

## Mensagem principal

```text
LLM gera.
Pydantic valida.
Sistema decide se pode confiar.
```

---

## Conexão com os outros exercícios

Este exercício complementa:

1. Guardrails SQL: protege ações no banco
2. Presidio: protege dados pessoais
3. Prompt Injection: protege instruções
4. Pydantic: protege estrutura e contrato de dados

Juntos:

```text
Guardrails protegem ações.
Presidio protege dados.
Prompt injection defense protege instruções.
Pydantic protege contratos.
```

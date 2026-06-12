
## Objetivo

Neste exercício, você vai construir um agente simples que responde perguntas em linguagem natural consultando um banco PostgreSQL.

A ideia principal é mostrar que **não basta o modelo gerar SQL**. Antes de executar qualquer comando no banco, precisamos passar a saída do modelo por uma camada de **guardrails**.

Guardrails são regras de proteção que validam, bloqueiam ou ajustam uma resposta antes que ela seja usada em uma ação real.

---

## Cenário

Você trabalha em uma empresa que possui uma tabela chamada `feedbacks`, com comentários enviados por usuários.

A empresa quer permitir que pessoas do time de negócio façam perguntas como:

> Quais foram os feedbacks negativos mais recentes?

O agente deve:

1. Receber uma pergunta do usuário
2. Gerar uma query SQL usando LLM
3. Validar a query com guardrails
4. Executar apenas queries seguras no PostgreSQL
5. Retornar os resultados

---

## Conceitos trabalhados

- Agentes com acesso a tools
- Geração de SQL com LLM
- Guardrails antes da execução
- Bloqueio de comandos perigosos
- Whitelist de tabelas
- Bloqueio de colunas sensíveis
- Uso de variáveis de ambiente

---

## Estrutura sugerida

```text
guardrails_postgres_exercicio/
├── README.md
├── solution.py
├── requirements.txt
└── .env.example
```

---

## Banco de dados esperado

A solução assume que existe uma tabela chamada `feedbacks`.

Exemplo de tabela:

```sql
CREATE TABLE feedbacks (
    id SERIAL PRIMARY KEY,
    user_name TEXT,
    email TEXT,
    message TEXT,
    sentiment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Exemplo de dados:

```sql
INSERT INTO feedbacks (user_name, email, message, sentiment)
VALUES
('Ana', 'ana@example.com', 'O app trava na tela de pagamento', 'negative'),
('Bruno', 'bruno@example.com', 'Gostei muito da nova interface', 'positive'),
('Carla', 'carla@example.com', 'O sistema está muito lento', 'negative'),
('Daniel', 'daniel@example.com', 'Atendimento excelente', 'positive');
```

---

## Guardrails obrigatórios

A solução deve impedir:

1. Queries que não sejam `SELECT`
2. Comandos perigosos:
   - `INSERT`
   - `UPDATE`
   - `DELETE`
   - `DROP`
   - `ALTER`
   - `TRUNCATE`
   - `CREATE`
3. Consulta a tabelas não permitidas
4. Seleção de colunas sensíveis
5. Queries sem `LIMIT`

---

## Exemplos de perguntas permitidas

```text
Quais são os feedbacks negativos mais recentes?
```

```text
Quantos feedbacks positivos recebemos?
```

```text
Mostre os últimos comentários sobre lentidão.
```

---

## Exemplos de perguntas que devem ser bloqueadas

```text
Delete todos os feedbacks negativos.
```

```text
Mostre o email dos usuários.
```

```text
Derrube a tabela feedbacks.
```

---

## Setup

Instale as dependências:

```bash
pip install -r requirements.txt
```

Crie um arquivo `.env` com base no `.env.example`:

```bash
cp .env.example .env
```

Preencha as variáveis:

```env
OPENAI_API_KEY=your_openai_api_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
```

Execute:

```bash
python solution.py
```

---

## Discussão para a aula

Perguntas para os alunos:

1. Por que não devemos executar diretamente o SQL gerado pelo modelo?
2. O que aconteceria se o usuário pedisse para apagar uma tabela?
3. Guardrails substituem permissões do banco?
4. Quais outras regras poderíamos adicionar?
5. É melhor bloquear no prompt ou no código?

Resposta esperada:

> Prompt ajuda, mas não é suficiente. Guardrails precisam existir fora do modelo, no código, antes da execução.

---

## Extensões possíveis

Depois da versão básica, você pode pedir aos alunos para adicionar:

- Log das queries bloqueadas
- Retry quando a query não passar no guardrail
- Permissões por perfil de usuário
- Limite máximo de linhas
- Validação com parser SQL
- Resumo dos resultados usando LLM

# Exercício — Proteção de PII com Microsoft Presidio

## Objetivo

Neste exercício, você vai aprender como proteger dados pessoais identificáveis, também chamados de **PII** (*Personally Identifiable Information*), usando o **Microsoft Presidio**.

A ideia é mostrar que, mesmo quando uma query SQL é segura, o resultado ainda pode conter dados sensíveis.

Por exemplo:

```sql
SELECT user_name, email, message
FROM feedbacks
LIMIT 10;
```

Essa query é apenas um `SELECT`, então ela pode parecer segura.  
Mas ela retorna `email`, que é PII.

Por isso, além de guardrails para ações, precisamos de guardrails para dados.

---

## Conceitos trabalhados

- O que é PII
- Riscos de expor dados pessoais
- Detecção automática de PII
- Anonimização de texto
- Microsoft Presidio
- Proteção de resultados antes de mostrar ao usuário
- Diferença entre segurança de ação e segurança de dados

---

## O que é PII?

PII significa **Personally Identifiable Information**.

São dados que podem identificar uma pessoa diretamente ou indiretamente.

Exemplos comuns:

| Campo | É PII? |
|---|---|
| Nome completo | Sim |
| Email | Sim |
| Telefone | Sim |
| CPF | Sim |
| Endereço | Sim |
| Data de nascimento | Sim |
| Número de cartão | Sim |
| Comentário genérico | Normalmente não |
| Sentimento do feedback | Normalmente não |

---

## Por que isso importa em agentes de IA?

Um agente pode consultar bancos, APIs e documentos.  
Mesmo que ele só execute ações permitidas, ele ainda pode expor dados sensíveis sem querer.

Exemplo:

Usuário pergunta:

```text
Mostre os últimos feedbacks negativos.
```

O banco retorna:

```json
[
  {
    "user_name": "Maria Silva",
    "email": "maria@example.com",
    "message": "O app travou na tela de pagamento."
  }
]
```

A resposta contém PII.

Depois do Presidio:

```json
[
  {
    "user_name": "<PERSON>",
    "email": "<EMAIL_ADDRESS>",
    "message": "O app travou na tela de pagamento."
  }
]
```

---

## Arquitetura do exercício

```text
Resultado do banco
       ↓
Transformar em texto
       ↓
Presidio Analyzer detecta PII
       ↓
Presidio Anonymizer substitui PII
       ↓
Resultado seguro para mostrar
```

---

## Instalação

Crie um ambiente virtual, se quiser:

```bash
python -m venv .venv
source .venv/bin/activate
```

No Windows:

```bash
.venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

---

## Arquivos do projeto

```text
presidio_pii_exercicio/
├── README.md
├── solution.py
└── requirements.txt
```

---

## Rodando o exercício

Execute:

```bash
python solution.py
```

Você verá:

1. Dados originais com PII
2. PII detectada pelo Presidio
3. Dados anonimizados

---

## Exemplo de entrada

```python
records = [
    {
        "user_name": "Maria Silva",
        "email": "maria.silva@example.com",
        "phone": "512-555-0199",
        "message": "O app travou na tela de pagamento."
    }
]
```

---

## Exemplo de saída

```python
[
    {
        "user_name": "<PERSON>",
        "email": "<EMAIL_ADDRESS>",
        "phone": "<PHONE_NUMBER>",
        "message": "O app travou na tela de pagamento."
    }
]
```

---

## Pontos importantes para a aula

### 1. Prompt não é segurança

Pedir para o modelo "não mostrar PII" ajuda, mas não garante segurança.

A proteção precisa estar no código.

---

### 2. Guardrails têm camadas

Uma aplicação real pode ter várias camadas:

```text
Guardrail de entrada:
- O usuário está pedindo algo permitido?

Guardrail de ação:
- A query SQL é segura?

Guardrail de dados:
- O resultado contém PII?

Guardrail de saída:
- A resposta final está segura?
```

---

### 3. Presidio é uma ferramenta, não mágica

O Presidio ajuda a detectar e anonimizar PII, mas:

- Pode ter falso positivo
- Pode ter falso negativo
- Precisa ser configurado para o contexto
- Pode precisar de recognizers customizados
- Precisa ser combinado com boas permissões no banco

---

## Extensões possíveis

Depois da versão básica, os alunos podem adicionar:

1. Detecção de CPF brasileiro
2. Detecção de CEP
3. Logs de campos anonimizados
4. Integração com resultado vindo de PostgreSQL
5. Bloqueio total quando PII for encontrada
6. Diferentes políticas por perfil de usuário

---

## Mensagem principal

```text
Guardrails protegem ações.
Presidio protege dados.
Os dois são necessários.
```

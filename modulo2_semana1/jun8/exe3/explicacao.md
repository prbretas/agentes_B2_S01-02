# Aula Completa — Do Zero até Tools com OpenAI

## Objetivo

Nesta aula vamos construir, passo a passo, um pequeno sistema que analisa feedbacks de usuários usando OpenAI.

A ideia é sair do básico:

```text
Instalar bibliotecas
↓
Importar bibliotecas
↓
Conectar no banco
↓
Ler feedbacks
↓
Chamar OpenAI
↓
Criar funções Python
↓
Descrever funções como tools
↓
Deixar o modelo chamar tools
↓
Gerar relatório final
```

No final, os alunos devem entender:

1. O que é uma biblioteca
2. O que é um `import`
3. O que é uma variável de ambiente
4. O que é uma conexão com banco
5. Como chamar a OpenAI pelo Python
6. O que é uma função
7. O que é uma tool
8. Como a OpenAI chama uma tool
9. A diferença entre workflow e agente

---

# 1. Estrutura do projeto

Crie uma pasta para o projeto:

```bash
mkdir aula_openai_tools
cd aula_openai_tools
```

A estrutura final será:

```text
aula_openai_tools/
├── .env
├── requirements.txt
└── main.py
```

---

# 2. Criar ambiente virtual

## Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

## Mac ou Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

O ambiente virtual serve para instalar as bibliotecas deste projeto sem misturar com outros projetos.

---

# 3. Criar o arquivo requirements.txt

Crie um arquivo chamado `requirements.txt`.

Coloque dentro dele:

```txt
openai
pandas
sqlalchemy
psycopg2-binary
python-dotenv
```

O que cada biblioteca faz?

| Biblioteca | Para que serve |
|----------|----------------|
| `openai` | Conversar com os modelos da OpenAI |
| `pandas` | Trabalhar com tabelas dentro do Python |
| `sqlalchemy` | Criar conexão com banco de dados |
| `psycopg2-binary` | Driver para conectar no PostgreSQL |
| `python-dotenv` | Ler variáveis do arquivo `.env` |

---

# 4. Instalar bibliotecas

No terminal:

```bash
pip install -r requirements.txt
```

Explicação:

```text
pip
```

É o instalador de bibliotecas do Python.

```text
requirements.txt
```

É a lista de bibliotecas que o projeto precisa.

---

# 5. Criar o arquivo .env

Crie um arquivo chamado `.env`.

Coloque:

```env
OPENAI_API_KEY=sua_chave_da_openai_aqui
DB_HOST=localhost
```

O `.env` guarda informações de configuração.

Exemplos:

- chave da OpenAI
- host do banco
- senhas
- configurações do projeto

Nunca é uma boa prática deixar chave diretamente no código.

---

# 6. Criar o arquivo main.py

Crie um arquivo chamado `main.py`.

Vamos construir esse arquivo por partes.

---

# 7. Primeiro código: importar bibliotecas

Coloque no `main.py`:

```python
import os
import json

import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine
from openai import OpenAI
```

O que está acontecendo aqui?

```python
import os
```

Permite acessar variáveis do sistema.

```python
import json
```

Permite trabalhar com JSON.

```python
import pandas as pd
```

Permite trabalhar com tabelas.

```python
from dotenv import load_dotenv
```

Permite carregar o arquivo `.env`.

```python
from sqlalchemy import create_engine
```

Permite criar uma conexão com o banco.

```python
from openai import OpenAI
```

Permite criar um cliente da OpenAI.

---

# 8. Carregar o .env

Ainda no `main.py`:

```python
load_dotenv()
```

Isso faz o Python ler o arquivo `.env`.

Depois disso, conseguimos acessar:

```python
os.getenv("OPENAI_API_KEY")
os.getenv("DB_HOST")
```

---

# 9. Conectar no banco PostgreSQL

Adicione:

```python
DB_HOST = os.getenv("DB_HOST", "localhost")

DB_URL = f"postgresql+psycopg2://postgres:postgres123@{DB_HOST}:5450/mydb"

engine = create_engine(DB_URL)
```

Explicação:

```python
DB_HOST = os.getenv("DB_HOST", "localhost")
```

Busca o valor de `DB_HOST` no `.env`.

Se não encontrar, usa `"localhost"`.

---

## O que significa DB_URL?

```python
postgresql+psycopg2://postgres:postgres123@localhost:5450/mydb
```

Essa string diz:

| Parte | Significado |
|------|-------------|
| `postgresql` | Tipo do banco |
| `psycopg2` | Driver usado |
| `postgres` | Usuário |
| `postgres123` | Senha |
| `localhost` | Onde o banco está |
| `5450` | Porta |
| `mydb` | Nome do banco |

---

# 10. Testar a conexão lendo feedbacks

Adicione:

```python
df_feedbacks = pd.read_sql(
    """
    SELECT
        id,
        feedback
    FROM feedbacks
    """,
    engine
)

print(df_feedbacks)
```

Rodar:

```bash
python main.py
```

Se tudo estiver certo, você verá uma tabela parecida com:

```text
   id                                      feedback
0   1  O app trava quando tento abrir a tela...
1   2  Gostei muito da nova interface
2   3  O sistema está muito lento
```

Neste ponto, o Python já consegue conversar com o banco.

---

# 11. Criar cliente da OpenAI

Adicione:

```python
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)
```

Esse `client` é o objeto que vamos usar para conversar com a OpenAI.

---

# 12. Teste simples com OpenAI

Antes de analisar feedbacks, faça um teste simples:

```python
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {
            "role": "user",
            "content": "Explique em uma frase o que é um feedback de usuário."
        }
    ]
)

print(response.choices[0].message.content)
```

Rodar:

```bash
python main.py
```

Se aparecer uma resposta, o Python já consegue conversar com a OpenAI.

---

# 13. Primeira função: analisar feedback

Agora vamos criar uma função Python.

Ela recebe:

- `feedback_id`
- `feedback_text`

E devolve:

- categoria
- sentimento
- resumo

```python
def analyze_feedback(feedback_id: int, feedback_text: str) -> dict:
    prompt = f"""
Analise o feedback abaixo.

ID: {feedback_id}
Feedback: {feedback_text}

Classifique usando apenas uma categoria:
- bug
- elogio
- pagamento
- performance
- atendimento
- outros

Sentimento:
- positivo
- negativo
- neutro

Responda somente em JSON neste formato:

{{
  "feedback_id": {feedback_id},
  "category": "bug",
  "sentiment": "negativo",
  "summary": "Resumo curto do feedback."
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    return json.loads(content)
```

---

# 14. Testar a função

Adicione:

```python
test_result = analyze_feedback(
    1,
    "O app trava quando tento abrir a tela de pagamento"
)

print(test_result)
```

Saída esperada:

```json
{
  "feedback_id": 1,
  "category": "bug",
  "sentiment": "negativo",
  "summary": "Usuário relatou falha ao acessar a tela de pagamento."
}
```

Até aqui, ainda não temos agente.

Temos apenas:

```text
Python chamando OpenAI
```

---

# 15. Criar função para definir time responsável

Agora vamos criar uma função comum de Python.

```python
def define_responsible_team(category: str) -> str:
    teams = {
        "bug": "Engenharia",
        "performance": "Engenharia",
        "pagamento": "Pagamentos",
        "atendimento": "Suporte",
        "elogio": "Produto",
        "outros": "Suporte"
    }

    return teams.get(category, "Suporte")
```

Testar:

```python
print(define_responsible_team("pagamento"))
```

Saída:

```text
Pagamentos
```

---

# 16. Criar função para definir prioridade

```python
def define_priority(category: str, sentiment: str) -> str:
    if category in ["bug", "pagamento"] and sentiment == "negativo":
        return "Alta"

    if category == "performance":
        return "Média"

    if category == "atendimento" and sentiment == "negativo":
        return "Média"

    return "Baixa"
```

Testar:

```python
print(define_priority("bug", "negativo"))
```

Saída:

```text
Alta
```

---

# 17. Processar todos os feedbacks como workflow

Antes de criar tools, vamos fazer funcionar como workflow.

```python
results = []

for _, row in df_feedbacks.iterrows():
    analysis = analyze_feedback(
        feedback_id=int(row["id"]),
        feedback_text=row["feedback"]
    )

    analysis["responsible_team"] = define_responsible_team(
        analysis["category"]
    )

    analysis["priority"] = define_priority(
        analysis["category"],
        analysis["sentiment"]
    )

    results.append(analysis)

print(json.dumps(results, ensure_ascii=False, indent=2))
```

Neste momento, quem manda no fluxo é o código:

```text
Código lê feedbacks
Código chama OpenAI
Código define time
Código define prioridade
Código salva resultado
```

Isso é workflow.

---

# 18. Salvar resultado no banco

```python
df_results = pd.DataFrame(results)

df_results.to_sql(
    "feedbacks_analisados",
    engine,
    if_exists="replace",
    index=False
)
```

Isso cria ou substitui a tabela `feedbacks_analisados`.

---

# 19. Gerar relatório consolidado com Python

```python
def generate_report(results: list) -> dict:
    df = pd.DataFrame(results)

    report = {
        "total_feedbacks": len(df),
        "categories": df["category"].value_counts().to_dict(),
        "sentiments": df["sentiment"].value_counts().to_dict(),
        "responsible_teams": df["responsible_team"].value_counts().to_dict(),
        "priorities": df["priority"].value_counts().to_dict()
    }

    return report
```

Testar:

```python
report = generate_report(results)

print(json.dumps(report, ensure_ascii=False, indent=2))
```

---

# 20. Gerar texto executivo com OpenAI

```python
def generate_executive_text(report: dict) -> str:
    prompt = f"""
Você é um analista de produto.

Com base no relatório abaixo, escreva um texto executivo curto para liderança.

Relatório:
{json.dumps(report, ensure_ascii=False, indent=2)}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content
```

Testar:

```python
executive_text = generate_executive_text(report)

print(executive_text)
```

---

# 21. Parada didática: isso ainda é agente?



> Isso é um agente?

Resposta:

```text
Ainda não.
```

Por quê?

Porque o código está decidindo tudo.

```text
O código chama as funções em uma ordem fixa.
```

Isso é um workflow.

---

# 22. O que é uma tool?

Uma tool é uma descrição de uma função.

A função real existe em Python:

```python
def define_responsible_team(category):
    ...
```

A tool descreve essa função para a OpenAI:

```python
{
    "type": "function",
    "function": {
        "name": "define_responsible_team",
        "description": "Define qual time deve tratar o feedback",
        "parameters": {
            ...
        }
    }
}
```

A OpenAI não lê seu código Python.

Você precisa explicar para ela:

```text
Existe uma função chamada define_responsible_team.
Ela recebe uma category.
Ela devolve o time responsável.
```

---

# 23. Criar a lista de tools

Adicione ao `main.py`:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "define_responsible_team",
            "description": "Define qual time deve tratar o feedback com base na categoria identificada",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria do feedback. Exemplos: bug, performance, pagamento, atendimento, elogio, outros."
                    }
                },
                "required": ["category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "define_priority",
            "description": "Define a prioridade de atendimento do feedback",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria do feedback"
                    },
                    "sentiment": {
                        "type": "string",
                        "description": "Sentimento do feedback. Exemplos: positivo, negativo, neutro."
                    }
                },
                "required": ["category", "sentiment"]
            }
        }
    }
]
```

Aqui estamos dizendo para a OpenAI:

```text
Você pode usar estas funções:
- define_responsible_team
- define_priority
```

---

# 24. Criar um mapa entre nome da tool e função Python

A OpenAI vai responder dizendo que quer chamar uma função pelo nome.

Por exemplo:

```text
define_responsible_team
```

Mas quem executa a função é o nosso código Python.

Por isso criamos um dicionário:

```python
available_functions = {
    "define_responsible_team": define_responsible_team,
    "define_priority": define_priority
}
```

Esse dicionário significa:

```text
Se a OpenAI pedir define_responsible_team, chame a função Python define_responsible_team.
Se a OpenAI pedir define_priority, chame a função Python define_priority.
```

---

# 25. Pedir para o modelo usar uma tool

Agora vamos fazer uma chamada em que o modelo pode escolher uma tool.

```python
messages = [
    {
        "role": "user",
        "content": "Qual time deve tratar um feedback da categoria pagamento?"
    }
]

response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

message = response.choices[0].message

print(message)
```

Aqui acontece algo importante.

O modelo pode não responder diretamente.

Ele pode pedir para chamar uma tool.

---

# 26. Verificar se o modelo pediu tool

```python
if message.tool_calls:
    print("O modelo pediu para chamar uma tool.")
else:
    print("O modelo respondeu sem tool.")
```

---

# 27. Executar a tool pedida

```python
if message.tool_calls:
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        function_to_call = available_functions[function_name]

        function_response = function_to_call(**function_args)

        print(function_name)
        print(function_args)
        print(function_response)
```

Explicação:

```python
function_name = tool_call.function.name
```

Pega o nome da função que o modelo quer chamar.

```python
function_args = json.loads(tool_call.function.arguments)
```

Pega os argumentos que o modelo quer passar para a função.

```python
function_to_call = available_functions[function_name]
```

Encontra a função Python correspondente.

```python
function_response = function_to_call(**function_args)
```

Executa a função.

---

# 28. Enviar o resultado da tool de volta para o modelo

Depois que o Python executa a função, precisamos devolver o resultado para a OpenAI.

```python
messages.append(message)

for tool_call in message.tool_calls:
    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments)

    function_to_call = available_functions[function_name]
    function_response = function_to_call(**function_args)

    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": function_name,
            "content": json.dumps(function_response, ensure_ascii=False)
        }
    )

second_response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=messages
)

print(second_response.choices[0].message.content)
```

Fluxo:

```text
Usuário pergunta
↓
Modelo pede para chamar tool
↓
Python executa tool
↓
Python envia resultado para modelo
↓
Modelo responde ao usuário
```

---

# 29. Criar uma função para rodar tools automaticamente

Para não repetir código, criamos uma função.

```python
def run_with_tools(messages: list) -> str:
    first_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = first_response.choices[0].message

    if not message.tool_calls:
        return message.content

    messages.append(message)

    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        function_to_call = available_functions[function_name]
        function_response = function_to_call(**function_args)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": json.dumps(function_response, ensure_ascii=False)
            }
        )

    second_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages
    )

    return second_response.choices[0].message.content
```

Testar:

```python
answer = run_with_tools([
    {
        "role": "user",
        "content": "Qual prioridade para um feedback de pagamento com sentimento negativo?"
    }
])

print(answer)
```

---

# 30. Agora sim: usando tools no exercício

Podemos usar tools para decisões como:

- qual time responsável?
- qual prioridade?

Exemplo:

```python
messages = [
    {
        "role": "user",
        "content": """
Tenho um feedback com:
categoria: pagamento
sentimento: negativo

Defina o time responsável e a prioridade usando as tools disponíveis.
"""
    }
]

answer = run_with_tools(messages)

print(answer)
```

---

# 31. Tool para buscar feedbacks no banco

Agora podemos criar uma tool para buscar feedbacks.

## Função Python

```python
def get_feedbacks() -> list:
    df = pd.read_sql(
        """
        SELECT
            id,
            feedback
        FROM feedbacks
        """,
        engine
    )

    return df.to_dict(orient="records")
```

## Tool

Adicione na lista `tools`:

```python
{
    "type": "function",
    "function": {
        "name": "get_feedbacks",
        "description": "Busca todos os feedbacks da tabela feedbacks no banco de dados",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}
```

E no `available_functions`:

```python
available_functions = {
    "get_feedbacks": get_feedbacks,
    "define_responsible_team": define_responsible_team,
    "define_priority": define_priority
}
```

---

# 32. Tool para salvar resultados

## Função Python

```python
def save_feedback_analysis(
    feedback_id: int,
    category: str,
    sentiment: str,
    summary: str,
    responsible_team: str,
    priority: str
) -> str:
    df = pd.DataFrame([
        {
            "feedback_id": feedback_id,
            "category": category,
            "sentiment": sentiment,
            "summary": summary,
            "responsible_team": responsible_team,
            "priority": priority
        }
    ])

    df.to_sql(
        "feedbacks_analisados",
        engine,
        if_exists="append",
        index=False
    )

    return "Resultado salvo com sucesso."
```

## Tool

```python
{
    "type": "function",
    "function": {
        "name": "save_feedback_analysis",
        "description": "Salva o resultado da análise de um feedback no banco de dados",
        "parameters": {
            "type": "object",
            "properties": {
                "feedback_id": {
                    "type": "integer",
                    "description": "ID do feedback"
                },
                "category": {
                    "type": "string",
                    "description": "Categoria do feedback"
                },
                "sentiment": {
                    "type": "string",
                    "description": "Sentimento do feedback"
                },
                "summary": {
                    "type": "string",
                    "description": "Resumo curto do feedback"
                },
                "responsible_team": {
                    "type": "string",
                    "description": "Time responsável"
                },
                "priority": {
                    "type": "string",
                    "description": "Prioridade do atendimento"
                }
            },
            "required": [
                "feedback_id",
                "category",
                "sentiment",
                "summary",
                "responsible_team",
                "priority"
            ]
        }
    }
}
```

---

# 33. Tool para gerar relatório

## Função Python

```python
def generate_report() -> dict:
    df = pd.read_sql(
        """
        SELECT
            *
        FROM feedbacks_analisados
        """,
        engine
    )

    report = {
        "total_feedbacks": len(df),
        "categories": df["category"].value_counts().to_dict(),
        "sentiments": df["sentiment"].value_counts().to_dict(),
        "responsible_teams": df["responsible_team"].value_counts().to_dict(),
        "priorities": df["priority"].value_counts().to_dict()
    }

    return report
```

## Tool

```python
{
    "type": "function",
    "function": {
        "name": "generate_report",
        "description": "Gera um relatório consolidado dos feedbacks analisados",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
}
```

---

# 34. Importante: a OpenAI não executa a tool sozinha

Este é o ponto mais importante da aula.

Quando o modelo quer usar uma tool, ele apenas responde algo como:

```text
Quero chamar a função define_priority com estes argumentos.
```

Quem executa de verdade é o Python.

Fluxo real:

```text
OpenAI decide chamar tool
↓
Python lê o pedido
↓
Python executa a função
↓
Python devolve o resultado para OpenAI
↓
OpenAI gera a resposta final
```

---

# 35. Código completo de exemplo

Abaixo está uma versão compacta do `main.py`.

```python
import os
import json

import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine
from openai import OpenAI


load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_URL = f"postgresql+psycopg2://postgres:postgres123@{DB_HOST}:5450/mydb"
engine = create_engine(DB_URL)


def get_feedbacks() -> list:
    df = pd.read_sql(
        """
        SELECT
            id,
            feedback
        FROM feedbacks
        """,
        engine
    )

    return df.to_dict(orient="records")


def define_responsible_team(category: str) -> str:
    teams = {
        "bug": "Engenharia",
        "performance": "Engenharia",
        "pagamento": "Pagamentos",
        "atendimento": "Suporte",
        "elogio": "Produto",
        "outros": "Suporte"
    }

    return teams.get(category, "Suporte")


def define_priority(category: str, sentiment: str) -> str:
    if category in ["bug", "pagamento"] and sentiment == "negativo":
        return "Alta"

    if category == "performance":
        return "Média"

    if category == "atendimento" and sentiment == "negativo":
        return "Média"

    return "Baixa"


def save_feedback_analysis(
    feedback_id: int,
    category: str,
    sentiment: str,
    summary: str,
    responsible_team: str,
    priority: str
) -> str:
    df = pd.DataFrame([
        {
            "feedback_id": feedback_id,
            "category": category,
            "sentiment": sentiment,
            "summary": summary,
            "responsible_team": responsible_team,
            "priority": priority
        }
    ])

    df.to_sql(
        "feedbacks_analisados",
        engine,
        if_exists="append",
        index=False
    )

    return "Resultado salvo com sucesso."


def generate_report() -> dict:
    df = pd.read_sql(
        """
        SELECT
            *
        FROM feedbacks_analisados
        """,
        engine
    )

    report = {
        "total_feedbacks": len(df),
        "categories": df["category"].value_counts().to_dict(),
        "sentiments": df["sentiment"].value_counts().to_dict(),
        "responsible_teams": df["responsible_team"].value_counts().to_dict(),
        "priorities": df["priority"].value_counts().to_dict()
    }

    return report


tools = [
    {
        "type": "function",
        "function": {
            "name": "get_feedbacks",
            "description": "Busca todos os feedbacks da tabela feedbacks no banco de dados",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "define_responsible_team",
            "description": "Define qual time deve tratar o feedback com base na categoria identificada",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria do feedback"
                    }
                },
                "required": ["category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "define_priority",
            "description": "Define a prioridade de atendimento do feedback",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria do feedback"
                    },
                    "sentiment": {
                        "type": "string",
                        "description": "Sentimento do feedback"
                    }
                },
                "required": ["category", "sentiment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_feedback_analysis",
            "description": "Salva o resultado da análise de um feedback no banco de dados",
            "parameters": {
                "type": "object",
                "properties": {
                    "feedback_id": {"type": "integer"},
                    "category": {"type": "string"},
                    "sentiment": {"type": "string"},
                    "summary": {"type": "string"},
                    "responsible_team": {"type": "string"},
                    "priority": {"type": "string"}
                },
                "required": [
                    "feedback_id",
                    "category",
                    "sentiment",
                    "summary",
                    "responsible_team",
                    "priority"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Gera um relatório consolidado dos feedbacks analisados",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


available_functions = {
    "get_feedbacks": get_feedbacks,
    "define_responsible_team": define_responsible_team,
    "define_priority": define_priority,
    "save_feedback_analysis": save_feedback_analysis,
    "generate_report": generate_report
}


def run_agent(messages: list, max_steps: int = 10) -> str:
    for step in range(max_steps):
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        messages.append(message)

        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            function_to_call = available_functions[function_name]
            function_response = function_to_call(**function_args)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(function_response, ensure_ascii=False)
                }
            )

    return "O agente atingiu o limite máximo de passos."


if __name__ == "__main__":
    answer = run_agent([
        {
            "role": "system",
            "content": """
Você é um agente analista de feedbacks.

Sua missão:
1. Buscar feedbacks usando get_feedbacks.
2. Para cada feedback, classificar categoria, sentimento e resumo.
3. Usar define_responsible_team para definir o time.
4. Usar define_priority para definir prioridade.
5. Usar save_feedback_analysis para salvar cada resultado.
6. Usar generate_report para gerar o relatório final.

Categorias permitidas:
bug, elogio, pagamento, performance, atendimento, outros.

Sentimentos permitidos:
positivo, negativo, neutro.
"""
        },
        {
            "role": "user",
            "content": "Analise todos os feedbacks e gere o relatório final."
        }
    ])

    print(answer)
```

---

# 36. Observação didática importante

Mesmo com tools, o modelo ainda precisa classificar o feedback no texto.

Neste exemplo, deixamos o modelo classificar categoria, sentimento e resumo dentro da conversa.

As tools são usadas para:

- buscar feedbacks
- definir time
- definir prioridade
- salvar resultado
- gerar relatório

Outra opção seria criar uma tool chamada `analyze_feedback`.

Mas, nesse caso, a própria tool chamaria a OpenAI.



---

# 37. Discussão final



## 1. O que era função?

```text
Um bloco de código Python.
```

## 2. O que era tool?

```text
A descrição de uma função para a OpenAI.
```

## 3. Quem executa a tool?

```text
O Python.
```

## 4. A OpenAI executa código?

```text
Não diretamente.
Ela pede para chamar uma tool.
O Python executa.
```

## 5. Isso é workflow ou agente?

Resposta:

```text
Depende.

Se o código decide a ordem, é workflow.
Se o modelo decide qual tool usar e quando usar, começa a parecer agente.
```

---

# 38. Frase para lembrar

```text
Tool é uma função apresentada para a IA.
```


```text
Função é o que o Python executa.
Tool é como a OpenAI descobre que essa função existe.
```
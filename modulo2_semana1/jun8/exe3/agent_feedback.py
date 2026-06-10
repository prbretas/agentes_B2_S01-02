"""
agent_feedbacks.py

Agente com Tools usando Function Calling — adaptado para Ollama.

Configuração via .env:
  OLLAMA_BASE_URL=http://localhost:11434/v1  (padrão)
  OLLAMA_MODEL=llama3.2                      (padrão)
  DB_HOST=localhost                          (padrão)

Nota: para tool calling, modelos como qwen2.5 ou llama3.1 funcionam melhor.
Ajuste OLLAMA_MODEL no .env conforme necessário.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from openai import OpenAI


# ---------------------------------------------------------
# 1. Configuração
# ---------------------------------------------------------

def _find_env():
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    return None

env_path = _find_env()
if env_path:
    load_dotenv(env_path, override=True)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")
DB_HOST         = os.getenv("DB_HOST", "localhost")

# Ollama expõe API compatível com OpenAI — não precisa de API key
client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"  # placeholder — Ollama não valida a key
)

DB_URL = f"postgresql+psycopg2://postgres:postgres123@{DB_HOST}:5450/mydb"
engine = create_engine(DB_URL)


# ---------------------------------------------------------
# 2. Helpers
# ---------------------------------------------------------

def clean_json_response(content: str) -> str:
    content = content.strip()

    if content.startswith("```json"):
        content = content.replace("```json", "", 1).strip()

    if content.startswith("```"):
        content = content.replace("```", "", 1).strip()

    if content.endswith("```"):
        content = content[:-3].strip()

    return content


# ---------------------------------------------------------
# 3. Funções reais em Python
# ---------------------------------------------------------

def get_feedbacks() -> List[Dict[str, Any]]:
    """
    Busca feedbacks no banco.

    Tabela esperada:
    feedbacks

    Colunas esperadas:
    - feedback_id
    - feedback_text
    """

    df = pd.read_sql(
        """
        SELECT
            feedback_id AS id,
            feedback_text AS feedback
        FROM feedbacks
        """,
        engine
    )

    return df.to_dict(orient="records")


def analyze_feedback(feedback_id: int, feedback_text: str) -> Dict[str, Any]:
    """
    Analisa um feedback usando OpenAI.
    """

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

Responda somente com JSON válido.
Não use markdown.
Não use ```json.
Não escreva explicações antes ou depois.

Formato obrigatório:

{{
  "feedback_id": {feedback_id},
  "category": "bug",
  "sentiment": "negativo",
  "summary": "Resumo curto do feedback."
}}
"""

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content
    content = clean_json_response(content)

    result = json.loads(content)

    required_keys = {"feedback_id", "category", "sentiment", "summary"}
    missing_keys = required_keys - set(result.keys())

    if missing_keys:
        # Tenta normalizar campos em português que o modelo pode retornar
        pt_to_en = {
            "sentimento": "sentiment",
            "categoria": "category",
            "resumo": "summary"
        }
        for pt_key, en_key in pt_to_en.items():
            if pt_key in result and en_key not in result:
                result[en_key] = result.pop(pt_key)

        missing_keys = required_keys - set(result.keys())

    if missing_keys:
        raise ValueError(
            f"A análise veio sem campos obrigatórios: {missing_keys}. "
            f"Resposta: {result}"
        )

    return result


def define_responsible_team(category: str) -> str:
    """
    Define qual time deve tratar o feedback.
    """

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
    """
    Define prioridade de atendimento.
    """

    if category in ["bug", "pagamento"] and sentiment == "negativo":
        return "Alta"

    if category == "performance":
        return "Média"

    if category == "atendimento" and sentiment == "negativo":
        return "Média"

    return "Baixa"


def clear_previous_results() -> str:
    """
    Remove resultados antigos.
    """

    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS feedbacks_analisados")

    return "Resultados antigos removidos com sucesso."


def save_feedback_analysis(
    feedback_id: int,
    category: str,
    sentiment: str,
    summary: str,
    responsible_team: str,
    priority: str
) -> str:
    """
    Salva a análise de um feedback no banco.
    """

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

    return f"Feedback {feedback_id} salvo com sucesso."


def generate_report() -> Dict[str, Any]:
    """
    Gera relatório consolidado.
    """

    df = pd.read_sql(
        """
        SELECT
            *
        FROM feedbacks_analisados
        """,
        engine
    )

    if df.empty:
        return {
            "total_feedbacks": 0,
            "categories": {},
            "sentiments": {},
            "responsible_teams": {},
            "priorities": {}
        }

    return {
        "total_feedbacks": len(df),
        "categories": df["category"].value_counts().to_dict(),
        "sentiments": df["sentiment"].value_counts().to_dict(),
        "responsible_teams": df["responsible_team"].value_counts().to_dict(),
        "priorities": df["priority"].value_counts().to_dict()
    }


# ---------------------------------------------------------
# 4. Tools: descrição das funções para a OpenAI
# ---------------------------------------------------------

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_feedbacks",
            "description": "Busca todos os feedbacks da tabela feedbacks no banco de dados.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_feedback",
            "description": "Analisa um feedback individual e retorna categoria, sentimento e resumo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feedback_id": {
                        "type": "integer",
                        "description": "ID do feedback"
                    },
                    "feedback_text": {
                        "type": "string",
                        "description": "Texto do feedback"
                    }
                },
                "required": ["feedback_id", "feedback_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "define_responsible_team",
            "description": "Define qual time deve tratar o feedback com base na categoria.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria: bug, performance, pagamento, atendimento, elogio ou outros."
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
            "description": "Define a prioridade do feedback com base na categoria e sentimento.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Categoria do feedback"
                    },
                    "sentiment": {
                        "type": "string",
                        "description": "Sentimento: positivo, negativo ou neutro"
                    }
                },
                "required": ["category", "sentiment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_previous_results",
            "description": "Remove resultados antigos antes de uma nova execução.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_feedback_analysis",
            "description": "Salva o resultado da análise de um feedback no banco.",
            "parameters": {
                "type": "object",
                "properties": {
                    "feedback_id": {
                        "type": "integer"
                    },
                    "category": {
                        "type": "string"
                    },
                    "sentiment": {
                        "type": "string"
                    },
                    "summary": {
                        "type": "string"
                    },
                    "responsible_team": {
                        "type": "string"
                    },
                    "priority": {
                        "type": "string"
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
    },
    {
        "type": "function",
        "function": {
            "name": "generate_report",
            "description": "Gera relatório consolidado dos feedbacks analisados.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


# ---------------------------------------------------------
# 5. Mapa: nome da tool -> função Python
# ---------------------------------------------------------

available_functions = {
    "get_feedbacks": get_feedbacks,
    "analyze_feedback": analyze_feedback,
    "define_responsible_team": define_responsible_team,
    "define_priority": define_priority,
    "clear_previous_results": clear_previous_results,
    "save_feedback_analysis": save_feedback_analysis,
    "generate_report": generate_report
}


# ---------------------------------------------------------
# 6. Executor de tool
# ---------------------------------------------------------

def execute_tool_call(tool_call) -> Dict[str, Any]:
    """
    Executa uma tool solicitada pela OpenAI.
    """

    function_name = tool_call.function.name
    function_args = json.loads(tool_call.function.arguments or "{}")

    if function_name not in available_functions:
        raise ValueError(f"Função desconhecida: {function_name}")

    function_to_call = available_functions[function_name]
    function_response = function_to_call(**function_args)

    return {
        "tool_call_id": tool_call.id,
        "name": function_name,
        "response": function_response
    }


# ---------------------------------------------------------
# 7. Loop do agente
# ---------------------------------------------------------

def run_agent(messages: List[Dict[str, str]], max_steps: int = 50) -> str:
    """
    Enquanto o modelo pedir tools:
    1. Python executa a tool
    2. Python devolve o resultado
    3. Modelo decide o próximo passo
    """

    for step in range(max_steps):
        print(f"\n--- Passo do agente {step + 1} ---")

        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0
        )

        message = response.choices[0].message

        if not message.tool_calls:
            return message.content

        print(f"O modelo pediu {len(message.tool_calls)} tool call(s).")

        messages.append(message)

        for tool_call in message.tool_calls:
            tool_result = execute_tool_call(tool_call)

            print(f"Tool executada: {tool_result['name']}")
            print(f"Resultado: {tool_result['response']}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "name": tool_result["name"],
                    "content": json.dumps(
                        tool_result["response"],
                        ensure_ascii=False
                    )
                }
            )

    return "O agente atingiu o limite máximo de passos."


# ---------------------------------------------------------
# 8. Main
# ---------------------------------------------------------

def main() -> None:
    messages = [
        {
            "role": "system",
            "content": """
Você é um agente analista de feedbacks de usuários.

Sua missão é processar todos os feedbacks do banco.

Siga esta ordem:

1. Use clear_previous_results para limpar resultados antigos.
2. Use get_feedbacks para buscar os feedbacks.
3. Para cada feedback retornado:
   a. Use analyze_feedback com:
      - feedback_id = id do feedback
      - feedback_text = texto do feedback
   b. Use define_responsible_team usando a category retornada.
   c. Use define_priority usando category e sentiment.
   d. Use save_feedback_analysis com:
      - feedback_id
      - category
      - sentiment
      - summary
      - responsible_team
      - priority
4. Depois que todos forem salvos, use generate_report.
5. Ao final, responda com:
   - relatório JSON consolidado
   - texto executivo curto para liderança

Categorias permitidas:
- bug
- elogio
- pagamento
- performance
- atendimento
- outros

Sentimentos permitidos:
- positivo
- negativo
- neutro

Importante:
- Não invente feedbacks.
- Use apenas feedbacks retornados por get_feedbacks.
- Não pule feedbacks.
- Use as tools disponíveis.
"""
        },
        {
            "role": "user",
            "content": "Analise todos os feedbacks do banco e gere o relatório final."
        }
    ]

    final_answer = run_agent(messages)

    print("\nRESPOSTA FINAL DO AGENTE:")
    print(final_answer)


if __name__ == "__main__":
    main()


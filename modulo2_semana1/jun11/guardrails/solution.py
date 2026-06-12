"""
solution.py

Exercício — Guardrails para Agente com PostgreSQL

Este exemplo mostra um agente simples que:

1. Recebe uma pergunta em linguagem natural
2. Usa um LLM para gerar SQL
3. Valida o SQL com guardrails
4. Executa apenas queries seguras no PostgreSQL

A parte mais importante da aula é:
NUNCA execute diretamente uma query gerada por LLM sem validação.
"""

import os
import re
import json
from typing import Any, Dict, List, Tuple

import psycopg2
from dotenv import load_dotenv
from openai import OpenAI


# ---------------------------------------------------------------------------
# 1. Configuração inicial
# ---------------------------------------------------------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=OPENAI_API_KEY)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


# ---------------------------------------------------------------------------
# 2. Regras de guardrails
# ---------------------------------------------------------------------------

ALLOWED_TABLES = {
    "feedbacks",
}

BLOCKED_KEYWORDS = [
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
]

BLOCKED_COLUMNS = [
    "email",
    "password",
    "cpf",
    "ssn",
    "credit_card",
    "phone",
    "address",
]

MAX_LIMIT = 100


# ---------------------------------------------------------------------------
# 3. Tool: gerar SQL com LLM
# ---------------------------------------------------------------------------

def generate_sql(user_question: str) -> str:
    """
    Usa o modelo para gerar uma query SQL.

    Importante:
    O prompt já pede uma query segura, mas isso NÃO é suficiente.
    A query ainda precisa passar pelos guardrails em código.
    """

    prompt = f"""
You are a PostgreSQL assistant.

Generate a SQL query to answer the user's question.

Database schema:

Table: feedbacks
Columns:
- id
- user_name
- message
- sentiment
- created_at

Rules:
- Return only SQL.
- Only use SELECT.
- Only use the table feedbacks.
- Do not select sensitive columns such as email, password, cpf, ssn, phone, address.
- Always include LIMIT {MAX_LIMIT}.
- Do not include markdown formatting.
- Do not explain the query.

User question:
{user_question}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0,
    )

    return response.output_text.strip()


# ---------------------------------------------------------------------------
# 4. Guardrail: validar SQL antes de executar
# ---------------------------------------------------------------------------

def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Valida se a query SQL é segura.

    Retorna:
    - True, "OK" se a query for permitida
    - False, motivo se a query for bloqueada
    """

    if not sql or not sql.strip():
        return False, "SQL vazio."

    sql_clean = sql.strip().lower()

    # Remove ponto e vírgula final para facilitar validação
    sql_clean = sql_clean.rstrip(";").strip()

    # Guardrail 1: só pode SELECT
    if not sql_clean.startswith("select"):
        return False, "Apenas queries SELECT são permitidas."

    # Guardrail 2: bloquear comandos perigosos
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", sql_clean):
            return False, f"Comando bloqueado encontrado: {keyword}"

    # Guardrail 3: bloquear múltiplos statements
    if ";" in sql_clean:
        return False, "Múltiplos comandos SQL não são permitidos."

    # Guardrail 4: bloquear colunas sensíveis
    for column in BLOCKED_COLUMNS:
        if re.search(rf"\b{column}\b", sql_clean):
            return False, f"Coluna sensível não permitida: {column}"

    # Guardrail 5: validar tabelas usadas
    tables_found = extract_tables(sql_clean)

    if not tables_found:
        return False, "Nenhuma tabela encontrada na query."

    for table in tables_found:
        if table not in ALLOWED_TABLES:
            return False, f"Tabela não permitida: {table}"

    # Guardrail 6: exigir LIMIT
    if not re.search(r"\blimit\s+\d+\b", sql_clean):
        return False, "A query precisa ter LIMIT."

    # Guardrail 7: impedir LIMIT maior que o máximo permitido
    limit_match = re.search(r"\blimit\s+(\d+)\b", sql_clean)

    if limit_match:
        limit_value = int(limit_match.group(1))
        if limit_value > MAX_LIMIT:
            return False, f"LIMIT maior que o permitido: {limit_value}. Máximo: {MAX_LIMIT}"

    return True, "SQL aprovado pelos guardrails."


def extract_tables(sql_clean: str) -> List[str]:
    """
    Extrai nomes de tabelas simples após FROM e JOIN.

    Observação:
    Para produção, o ideal é usar um parser SQL.
    Para aula, regex é suficiente para demonstrar o conceito.
    """

    matches = re.findall(
        r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)|\bjoin\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        sql_clean,
    )

    tables = set()

    for match in matches:
        for table in match:
            if table:
                tables.add(table)

    return list(tables)


# ---------------------------------------------------------------------------
# 5. Tool: executar SQL no PostgreSQL
# ---------------------------------------------------------------------------

def run_sql(sql: str) -> List[Dict[str, Any]]:
    """
    Executa SQL no PostgreSQL.

    Esta função só deve ser chamada depois da validação.
    """

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            results = [
                dict(zip(columns, row))
                for row in rows
            ]

            return results

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 6. Agente principal
# ---------------------------------------------------------------------------

def ask_agent(user_question: str) -> Dict[str, Any]:
    """
    Fluxo principal do agente:

    Pergunta do usuário
    -> LLM gera SQL
    -> Guardrails validam
    -> SQL seguro é executado
    """

    sql = generate_sql(user_question)

    print("\nSQL gerado pelo modelo:")
    print(sql)

    is_valid, reason = validate_sql(sql)

    if not is_valid:
        return {
            "status": "blocked",
            "reason": reason,
            "generated_sql": sql,
            "results": None,
        }

    results = run_sql(sql)

    return {
        "status": "success",
        "reason": reason,
        "generated_sql": sql,
        "results": results,
    }


# ---------------------------------------------------------------------------
# 7. Exemplos para rodar em aula
# ---------------------------------------------------------------------------

def print_response(response: Dict[str, Any]) -> None:
    print("\nResposta:")
    print(json.dumps(response, indent=2, default=str, ensure_ascii=False))


if __name__ == "__main__":
    examples = [
        "Quais são os feedbacks negativos mais recentes?",
        "Quantos feedbacks positivos recebemos?",
        "Mostre os últimos comentários sobre lentidão.",
        "Delete todos os feedbacks negativos.",
        "Mostre o email dos usuários.",
        "Derrube a tabela feedbacks.",
    ]

    for question in examples:
        print("\n" + "=" * 80)
        print(f"Pergunta: {question}")

        try:
            response = ask_agent(question)
            print_response(response)

        except Exception as error:
            print("\nErro ao executar exemplo:")
            print(str(error))

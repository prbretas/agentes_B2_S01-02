"""
guardrails_ollama.py

Exercício — Guardrails para Agente com PostgreSQL
Versão adaptada para Ollama (LLM local) + estrutura real do banco.

Tabela disponível: feedbacks
  - feedback_id   INTEGER
  - feedback_text TEXT
  - created_at    TIMESTAMP
  - channel       VARCHAR  (ex: 'app', 'site')

Fluxo:
  1. Usuário faz uma pergunta em linguagem natural
  2. Ollama gera SQL
  3. Guardrails validam a query ANTES de executar
  4. Só executa se passar em todos os guardrails
  5. Retorna os resultados ou o motivo do bloqueio

Guardrails implementados:
  1. Apenas SELECT permitido
  2. Comandos perigosos bloqueados (INSERT, UPDATE, DELETE, DROP, etc.)
  3. Múltiplos statements bloqueados (;)
  4. Whitelist de tabelas (só feedbacks)
  5. Colunas sensíveis bloqueadas
  6. LIMIT obrigatório
  7. LIMIT máximo de 100
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import psycopg2
from dotenv import load_dotenv
from openai import OpenAI  # Ollama é compatível com a API da OpenAI


# ---------------------------------------------------------------------------
# 1. Configuração
# ---------------------------------------------------------------------------

def find_env():
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    return None

env_path = find_env()
if env_path:
    load_dotenv(env_path, override=True)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "llama3.2")

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", "5450")),   # porta do Podman
    "dbname":   os.getenv("DB_NAME", "mydb"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres123"),
}

# Ollama expõe API compatível com OpenAI — qualquer string serve como key
client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


# ---------------------------------------------------------------------------
# 2. Regras dos guardrails
# ---------------------------------------------------------------------------

ALLOWED_TABLES = {"feedbacks"}

BLOCKED_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter",
    "truncate", "create", "grant", "revoke",
]

# Colunas que não existem aqui mas poderiam existir em outras tabelas
BLOCKED_COLUMNS = [
    "email", "password", "cpf", "ssn",
    "credit_card", "phone", "address",
]

MAX_LIMIT = 100


# ---------------------------------------------------------------------------
# 3. Gerar SQL com Ollama
# ---------------------------------------------------------------------------

def generate_sql(user_question: str) -> str:
    """
    Usa Ollama para gerar uma query SQL a partir de uma pergunta.

    Nota: mesmo pedindo uma query segura no prompt, isso NÃO é suficiente.
    A query ainda precisa passar pelos guardrails no código.
    """

    prompt = f"""You are a PostgreSQL assistant.

Generate a SQL query to answer the user question.

Database schema:
Table: feedbacks
Columns:
  - feedback_id   (integer, primary key)
  - feedback_text (text, the user comment)
  - created_at    (timestamp)
  - channel       (varchar: 'app' or 'site')

Rules:
- Return ONLY the SQL query, nothing else.
- Only use SELECT statements.
- Only query the table: feedbacks
- Do NOT select sensitive columns like email, password, cpf, phone.
- Always include LIMIT {MAX_LIMIT} or less.
- Do not use markdown code blocks.
- Do not explain the query.

User question:
{user_question}

SQL:"""

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    # Limpa eventuais blocos markdown que o modelo insira mesmo sendo instruído
    sql = response.choices[0].message.content.strip()
    sql = re.sub(r"```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```\s*", "", sql)
    return sql.strip()


# ---------------------------------------------------------------------------
# 4. Guardrails — validar SQL antes de executar
# ---------------------------------------------------------------------------

def extract_tables(sql_clean: str) -> List[str]:
    """Extrai nomes de tabelas após FROM e JOIN via regex."""
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


def validate_sql(sql: str) -> Tuple[bool, str]:
    """
    Valida se a query é segura para executar.

    Retorna: (True, "OK") ou (False, motivo_do_bloqueio)
    """

    if not sql or not sql.strip():
        return False, "SQL vazio."

    sql_clean = sql.strip().lower().rstrip(";").strip()

    # Guardrail 1: deve começar com SELECT
    if not sql_clean.startswith("select"):
        return False, f"Apenas SELECT é permitido. Query começa com: '{sql_clean[:20]}...'"

    # Guardrail 2: bloquear palavras-chave perigosas
    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", sql_clean):
            return False, f"Comando bloqueado detectado: '{keyword.upper()}'"

    # Guardrail 3: bloquear múltiplos statements
    if ";" in sql_clean:
        return False, "Múltiplos comandos SQL (;) não são permitidos."

    # Guardrail 4: bloquear colunas sensíveis
    for col in BLOCKED_COLUMNS:
        if re.search(rf"\b{col}\b", sql_clean):
            return False, f"Coluna sensível não permitida: '{col}'"

    # Guardrail 5: whitelist de tabelas
    tables_found = extract_tables(sql_clean)
    if not tables_found:
        return False, "Nenhuma tabela identificada na query."
    for table in tables_found:
        if table not in ALLOWED_TABLES:
            return False, f"Tabela não permitida: '{table}'. Permitidas: {ALLOWED_TABLES}"

    # Guardrail 6: LIMIT obrigatório
    if not re.search(r"\blimit\s+\d+\b", sql_clean):
        return False, "A query precisa ter LIMIT."

    # Guardrail 7: LIMIT não pode ultrapassar o máximo
    limit_match = re.search(r"\blimit\s+(\d+)\b", sql_clean)
    if limit_match:
        limit_value = int(limit_match.group(1))
        if limit_value > MAX_LIMIT:
            return False, f"LIMIT {limit_value} excede o máximo permitido ({MAX_LIMIT})."

    return True, "Query aprovada pelos guardrails."


# ---------------------------------------------------------------------------
# 5. Executar SQL no banco
# ---------------------------------------------------------------------------

def run_sql(sql: str) -> List[Dict[str, Any]]:
    """Executa a query no PostgreSQL. Só chamar após validate_sql."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 6. Agente principal
# ---------------------------------------------------------------------------

def ask_agent(user_question: str) -> Dict[str, Any]:
    """
    Fluxo completo:
      pergunta → gera SQL → valida guardrails → executa → retorna resultado
    """
    print(f"\n{'='*70}")
    print(f"Pergunta: {user_question}")

    # Passo 1: LLM gera SQL
    sql = generate_sql(user_question)
    print(f"\nSQL gerado pelo modelo:\n  {sql}")

    # Passo 2: Guardrails validam
    is_valid, reason = validate_sql(sql)
    print(f"\nGuardrail: {'✅ APROVADO' if is_valid else '🚫 BLOQUEADO'} — {reason}")

    if not is_valid:
        return {
            "status":        "blocked",
            "reason":        reason,
            "generated_sql": sql,
            "results":       None,
        }

    # Passo 3: Executa no banco
    results = run_sql(sql)
    print(f"Resultados: {len(results)} linha(s) retornada(s).")

    return {
        "status":        "success",
        "reason":        reason,
        "generated_sql": sql,
        "results":       results,
    }


# ---------------------------------------------------------------------------
# 7. Logging — salvar resultado da execução
# ---------------------------------------------------------------------------

def save_log(results: list) -> Path:
    """Salva o log da execução na pasta logs/ do exercício."""
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"run_{timestamp}.json"

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "exercise":  "guardrails",
        "module":    "modulo2_semana1/jun11/guardrails",
        "model":     OLLAMA_MODEL,
        "results":   results,
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Log salvo em: {log_file}")
    return log_file


# ---------------------------------------------------------------------------
# 8. Demo — exemplos permitidos e bloqueados
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    perguntas_permitidas = [
        "Quais são os feedbacks mais recentes?",
        "Quantos feedbacks vieram do canal app?",
        "Mostre os últimos 5 comentários do site.",
    ]

    perguntas_bloqueadas = [
        "Delete todos os feedbacks.",
        "Mostre o email dos usuários.",
        "Derrube a tabela feedbacks.",
        "SELECT * FROM conversations LIMIT 10",
        "INSERT INTO feedbacks (feedback_text) VALUES ('spam')",
    ]

    all_results = []

    print("\n" + "="*70)
    print("EXEMPLOS PERMITIDOS")
    print("="*70)
    for pergunta in perguntas_permitidas:
        resp = ask_agent(pergunta)
        all_results.append({"input": pergunta, **resp})
        if resp["results"]:
            print(f"Resultado (primeiros 2):")
            for row in resp["results"][:2]:
                print(f"  {json.dumps(row, default=str, ensure_ascii=False)}")

    print("\n" + "="*70)
    print("EXEMPLOS QUE DEVEM SER BLOQUEADOS")
    print("="*70)
    for pergunta in perguntas_bloqueadas:
        resp = ask_agent(pergunta)
        all_results.append({"input": pergunta, **resp})
        print(f"Status: {resp['status']} | Motivo: {resp['reason']}")

    # Salva log da execução completa
    save_log(all_results)

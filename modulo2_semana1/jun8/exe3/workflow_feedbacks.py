"""
workflow_feedbacks.py

Versão 1 — Workflow com Ollama (adaptado de OpenAI)

Nesta versão, o código controla o passo a passo:

1. Lê feedbacks do banco
2. Chama Ollama (via API compatível OpenAI) para analisar cada feedback
3. Define time responsável com regra Python
4. Define prioridade com regra Python
5. Salva resultados no banco
6. Gera relatório consolidado
7. Gera texto executivo com Ollama

Isso é um WORKFLOW porque a ordem das etapas está fixa no código.

Configuração via .env:
  OLLAMA_BASE_URL=http://localhost:11434/v1  (padrão)
  OLLAMA_MODEL=llama3.2                      (padrão)
  DB_HOST=localhost                          (padrão)
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine
from openai import OpenAI


# ---------------------------------------------------------
# 1. Carregar variáveis do .env (sobe a árvore de diretórios)
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


# ---------------------------------------------------------
# 2. Criar cliente Ollama e conexão com banco
# ---------------------------------------------------------

# Ollama expõe API compatível com OpenAI — não precisa de API key
client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"  # placeholder — Ollama não valida a key
)

DB_URL = f"postgresql+psycopg2://postgres:postgres123@{DB_HOST}:5450/mydb"
engine = create_engine(DB_URL)


# ---------------------------------------------------------
# 3. Função auxiliar para limpar JSON da resposta
# ---------------------------------------------------------

def clean_json_response(content: str) -> str:
    """
    Remove blocos markdown como ```json ... ``` caso o modelo retorne assim.
    """

    content = content.strip()

    if content.startswith("```json"):
        content = content.replace("```json", "", 1).strip()

    if content.startswith("```"):
        content = content.replace("```", "", 1).strip()

    if content.endswith("```"):
        content = content[:-3].strip()

    return content


# ---------------------------------------------------------
# 4. Ler feedbacks do banco
# ---------------------------------------------------------

def get_feedbacks() -> pd.DataFrame:
    """
    Busca feedbacks da tabela feedbacks.

    Espera uma tabela com as colunas:
    - feedback_id
    - feedback_text
    """

    query = """
    SELECT
        feedback_id AS id,
        feedback_text AS feedback
    FROM feedbacks
    """

    df = pd.read_sql(query, engine)

    expected_columns = {"id", "feedback"}
    missing_columns = expected_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Colunas ausentes no DataFrame: {missing_columns}. "
            f"Colunas encontradas: {list(df.columns)}"
        )

    return df


# ---------------------------------------------------------
# 5. Analisar um feedback com OpenAI
# ---------------------------------------------------------

def analyze_feedback(feedback_id: int, feedback_text: str) -> Dict[str, Any]:
    """
    Usa Ollama para classificar um feedback.

    Retorna:
    - feedback_id
    - category
    - sentiment
    - summary
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

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"A resposta da OpenAI não veio em JSON válido: {content}"
        ) from exc

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

        # Recalcula campos faltando após normalização
        missing_keys = required_keys - set(result.keys())

    if missing_keys:
        raise ValueError(
            f"A resposta da OpenAI veio sem campos obrigatórios: {missing_keys}. "
            f"Resposta: {result}"
        )

    return result


# ---------------------------------------------------------
# 6. Definir time responsável
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# 7. Definir prioridade
# ---------------------------------------------------------

def define_priority(category: str, sentiment: str) -> str:
    """
    Define prioridade com regras simples.
    """

    if category in ["bug", "pagamento"] and sentiment == "negativo":
        return "Alta"

    if category == "performance":
        return "Média"

    if category == "atendimento" and sentiment == "negativo":
        return "Média"

    return "Baixa"


# ---------------------------------------------------------
# 8. Salvar resultados no banco
# ---------------------------------------------------------

def save_results(results: List[Dict[str, Any]]) -> None:
    """
    Salva os resultados na tabela feedbacks_analisados.
    """

    if not results:
        print("Nenhum resultado para salvar.")
        return

    df_results = pd.DataFrame(results)

    df_results.to_sql(
        "feedbacks_analisados",
        engine,
        if_exists="replace",
        index=False
    )


# ---------------------------------------------------------
# 9. Gerar relatório consolidado com Python
# ---------------------------------------------------------

def generate_report(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Gera contagens consolidadas.
    """

    if not results:
        return {
            "total_feedbacks": 0,
            "categories": {},
            "sentiments": {},
            "responsible_teams": {},
            "priorities": {}
        }

    df = pd.DataFrame(results)

    report = {
        "total_feedbacks": len(df),
        "categories": df["category"].value_counts().to_dict(),
        "sentiments": df["sentiment"].value_counts().to_dict(),
        "responsible_teams": df["responsible_team"].value_counts().to_dict(),
        "priorities": df["priority"].value_counts().to_dict()
    }

    return report


# ---------------------------------------------------------
# 10. Gerar texto executivo com OpenAI
# ---------------------------------------------------------

def generate_executive_text(report: Dict[str, Any]) -> str:
    """
    Usa Ollama para transformar o relatório em texto executivo.
    """

    prompt = f"""
Você é um analista de produto.

Com base no relatório abaixo, escreva um texto executivo curto para liderança.

Relatório:
{json.dumps(report, ensure_ascii=False, indent=2)}
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

    return response.choices[0].message.content


# ---------------------------------------------------------
# 11. Main — orquestração do workflow
# ---------------------------------------------------------

def main() -> None:
    """
    Executa o workflow completo.
    """

    print("Lendo feedbacks do banco...")
    df_feedbacks = get_feedbacks()

    print("\nColunas encontradas:")
    print(df_feedbacks.columns.tolist())

    print("\nPrimeiras linhas:")
    print(df_feedbacks.head())

    print(f"\nTotal de feedbacks encontrados: {len(df_feedbacks)}")

    results = []

    for _, row in df_feedbacks.iterrows():
        feedback_id = int(row["id"])
        feedback_text = row["feedback"]

        print(f"\nAnalisando feedback {feedback_id}...")

        analysis = analyze_feedback(
            feedback_id=feedback_id,
            feedback_text=feedback_text
        )

        analysis["responsible_team"] = define_responsible_team(
            analysis["category"]
        )

        analysis["priority"] = define_priority(
            analysis["category"],
            analysis["sentiment"]
        )

        print("Resultado:")
        print(json.dumps(analysis, ensure_ascii=False, indent=2))

        results.append(analysis)

    print("\nSalvando resultados no banco...")
    save_results(results)

    print("Gerando relatório consolidado...")
    report = generate_report(results)

    print("\nRELATÓRIO JSON:")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    print("\nRELATÓRIO EXECUTIVO:")
    executive_text = generate_executive_text(report)
    print(executive_text)


if __name__ == "__main__":
    main()



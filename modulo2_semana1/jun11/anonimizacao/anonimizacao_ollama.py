"""
anonimizacao_ollama.py

Exercício — Proteção de PII com Microsoft Presidio
Versão adaptada para Ollama + dados reais do banco + logging (projectrules.md)

Fluxo:
  1. Busca feedbacks do PostgreSQL (banco real do projeto)
  2. Detecta PII nos campos com Presidio Analyzer
  3. Anonimiza os dados com Presidio Anonymizer
  4. Envia o texto ANONIMIZADO para o Ollama analisar (nunca o original)
  5. Mostra resultado seguro
  6. Salva log completo em logs/

Recognizers incluídos:
  - Padrões padrão do Presidio (EMAIL, PHONE, PERSON, etc.)
  - Recognizer customizado para CPF brasileiro
  - Recognizer customizado para CEP brasileiro
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from dotenv import load_dotenv
from openai import OpenAI
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine


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
    "port":     int(os.getenv("DB_PORT", "5450")),
    "dbname":   os.getenv("DB_NAME", "mydb"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres123"),
}

client = OpenAI(base_url=OLLAMA_BASE_URL, api_key="ollama")


# ---------------------------------------------------------------------------
# 2. Presidio — setup com recognizers customizados
# ---------------------------------------------------------------------------

analyzer  = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# Recognizer para CPF brasileiro (formato: 123.456.789-00)
cpf_recognizer = PatternRecognizer(
    supported_entity="BR_CPF",
    patterns=[Pattern(
        name="cpf_pattern",
        regex=r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
        score=0.9,
    )],
)

# Recognizer para CEP brasileiro (formato: 01310-100 ou 01310100)
cep_recognizer = PatternRecognizer(
    supported_entity="BR_CEP",
    patterns=[Pattern(
        name="cep_pattern",
        regex=r"\b\d{5}-?\d{3}\b",
        score=0.75,
    )],
)

analyzer.registry.add_recognizer(cpf_recognizer)
analyzer.registry.add_recognizer(cep_recognizer)


# ---------------------------------------------------------------------------
# 3. Funções de detecção e anonimização
# ---------------------------------------------------------------------------

def detect_pii(text: str) -> List[Dict[str, Any]]:
    """Detecta entidades PII em um texto. Retorna lista com detalhes."""
    results = analyzer.analyze(text=text, language="en")
    return [
        {
            "entity_type": r.entity_type,
            "text":        text[r.start:r.end],
            "score":       round(r.score, 2),
            "start":       r.start,
            "end":         r.end,
        }
        for r in results
    ]

def anonymize_text(text: str) -> str:
    """Detecta e anonimiza PII em um texto."""
    results = analyzer.analyze(text=text, language="en")
    if not results:
        return text
    return anonymizer.anonymize(text=text, analyzer_results=results).text

def anonymize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Anonimiza todos os campos de texto de um dicionário."""
    safe = {}
    for key, value in record.items():
        if value is None:
            safe[key] = None
        elif isinstance(value, str):
            safe[key] = anonymize_text(value)
        else:
            safe[key] = value
    return safe

def count_pii_in_records(records: List[Dict[str, Any]]) -> Dict[str, int]:
    """Conta quantas entidades PII foram encontradas por tipo."""
    counts: Dict[str, int] = {}
    for record in records:
        for value in record.values():
            if isinstance(value, str):
                for entity in detect_pii(value):
                    counts[entity["entity_type"]] = counts.get(entity["entity_type"], 0) + 1
    return counts


# ---------------------------------------------------------------------------
# 4. Buscar dados do banco
# ---------------------------------------------------------------------------

def fetch_feedbacks(limit: int = 5) -> List[Dict[str, Any]]:
    """Busca feedbacks reais do PostgreSQL."""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT feedback_id, feedback_text, created_at, channel
                FROM feedbacks
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 5. Analisar texto anonimizado com Ollama
# ---------------------------------------------------------------------------

def analyze_with_llm(anonymized_text: str) -> str:
    """
    Envia o texto JÁ ANONIMIZADO para o LLM.
    O LLM nunca vê os dados originais.
    """
    prompt = f"""Analyze the following customer feedback (PII has already been removed).

Classify:
- sentiment: positive, neutral, or negative
- topic: main topic in 3-5 words
- summary: one sentence summary of the issue

Return only valid JSON with keys: sentiment, topic, summary.

Feedback:
{anonymized_text}

JSON:"""

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        timeout=30,
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```\s*",     "", raw)
    return raw.strip()


# ---------------------------------------------------------------------------
# 6. Fluxo principal
# ---------------------------------------------------------------------------

def process_feedback(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fluxo completo para um registro:
      dado original → detecta PII → anonimiza → LLM analisa anonimizado
    """
    original_text = record.get("feedback_text", "")

    # Detectar PII antes de anonimizar
    pii_found = detect_pii(original_text)

    # Anonimizar o registro inteiro
    safe_record = anonymize_record(record)
    safe_text   = safe_record.get("feedback_text", "")

    # Analisar com LLM só o texto anonimizado
    try:
        llm_raw  = analyze_with_llm(safe_text)
        llm_data = json.loads(llm_raw)
    except Exception as e:
        llm_data = {"error": str(e)[:100]}

    return {
        "feedback_id":      record.get("feedback_id"),
        "channel":          record.get("channel"),
        "original_text":    original_text,
        "anonymized_text":  safe_text,
        "pii_detected":     pii_found,
        "pii_count":        len(pii_found),
        "llm_analysis":     llm_data,
    }


# ---------------------------------------------------------------------------
# 7. Logging (projectrules.md)
# ---------------------------------------------------------------------------

def save_log(results: List[Dict[str, Any]]) -> Path:
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file  = logs_dir / f"run_{timestamp}.json"

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "exercise":  "anonimizacao",
        "module":    "modulo2_semana1/jun11/anonimizacao",
        "model":     OLLAMA_MODEL,
        "results":   results,
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Log salvo em: {log_file}")
    return log_file


# ---------------------------------------------------------------------------
# 8. Demo com dados estáticos (sem banco)
# ---------------------------------------------------------------------------

DEMO_RECORDS = [
    {
        "feedback_id": 1,
        "feedback_text": "Maria Silva, email maria.silva@example.com, phone 512-555-0199. O app travou na tela de pagamento.",
        "channel": "app",
        "created_at": "2026-06-11",
    },
    {
        "feedback_id": 2,
        "feedback_text": "Robert Washington, robert.washington@example.com. O sistema está muito lento.",
        "channel": "site",
        "created_at": "2026-06-11",
    },
    {
        "feedback_id": 3,
        "feedback_text": "Gostei muito da nova interface, ficou mais fácil de usar.",
        "channel": "app",
        "created_at": "2026-06-11",
    },
    {
        "feedback_id": 4,
        "feedback_text": "CPF 123.456.789-00 não está sendo aceito no cadastro. CEP 01310-100.",
        "channel": "site",
        "created_at": "2026-06-11",
    },
]


# ---------------------------------------------------------------------------
# 9. Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    all_results = []

    # Tenta buscar do banco real; cai para dados estáticos se falhar
    print("\n🔌 Conectando ao banco de dados...")
    try:
        db_records = fetch_feedbacks(limit=5)
        print(f"   {len(db_records)} feedbacks carregados do banco.")
        records_to_process = db_records
    except Exception as e:
        print(f"   ⚠️  Banco indisponível ({e.__class__.__name__}). Usando dados de demonstração.")
        records_to_process = DEMO_RECORDS

    print(f"\n{'='*70}")
    print(f"Processando {len(records_to_process)} feedbacks com Presidio + Ollama")
    print(f"{'='*70}")

    for record in records_to_process:
        result = process_feedback(record)
        all_results.append(result)

        print(f"\n[ID {result['feedback_id']} | canal: {result['channel']}]")
        print(f"  Original  : {result['original_text'][:80]}{'...' if len(result['original_text']) > 80 else ''}")
        print(f"  Anonimizado: {result['anonymized_text'][:80]}{'...' if len(result['anonymized_text']) > 80 else ''}")

        if result["pii_detected"]:
            tipos = list({e["entity_type"] for e in result["pii_detected"]})
            print(f"  ⚠️  PII detectada: {', '.join(tipos)}")
        else:
            print(f"  ✅ Nenhuma PII detectada")

        if "error" not in result["llm_analysis"]:
            a = result["llm_analysis"]
            print(f"  LLM → sentimento: {a.get('sentiment','?')} | tema: {a.get('topic','?')}")
        else:
            print(f"  LLM → erro: {result['llm_analysis']['error']}")

    # Resumo de PII por tipo
    all_pii = [e for r in all_results for e in r["pii_detected"]]
    if all_pii:
        counts: Dict[str, int] = {}
        for e in all_pii:
            counts[e["entity_type"]] = counts.get(e["entity_type"], 0) + 1
        print(f"\n{'='*70}")
        print("Resumo de PII detectada:")
        for tipo, qtd in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"  {tipo:<25} → {qtd} ocorrência(s)")

    save_log(all_results)

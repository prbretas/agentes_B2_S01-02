"""
Exercício 3 — Análise de Feedbacks com Ollama

Agente que:
1. Lê feedbacks do banco de dados
2. Analisa cada feedback individualmente via LLM (categoria, sentimento, resumo)
3. Salva os resultados estruturados em JSON
4. Gera um relatório consolidado para liderança

Usa Ollama como LLM (API compatível com OpenAI).
Configure OLLAMA_MODEL no .env para trocar o modelo (padrão: llama3.2).
"""

import os
import json
import re
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy import create_engine, text

# Carrega .env subindo a árvore de diretórios
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

# --- Configuração Ollama ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"  # placeholder — Ollama não valida a key
)

# --- Banco de dados ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_URL = f"postgresql+psycopg2://postgres:postgres123@{DB_HOST}:5450/mydb"
engine = create_engine(DB_URL)


# =============================================================================
# TOOLS (funções que o agente usa)
# =============================================================================

def get_all_feedbacks() -> list[dict]:
    """Busca todos os feedbacks da tabela feedbacks."""
    query = text("""
        SELECT id, feedback_text
        FROM feedbacks
        ORDER BY id
    """)
    with engine.begin() as conn:
        rows = conn.execute(query).mappings().all()
    return [{"id": row["id"], "feedback_text": row["feedback_text"]} for row in rows]


def analyze_feedback(feedback_id: int, feedback_text: str) -> dict:
    """
    Analisa um feedback individual via LLM.
    Retorna: categoria, sentimento, resumo.
    """
    prompt = f"""
Você é um analista de feedbacks de usuários.

Analise o feedback abaixo e classifique conforme as regras:

Categorias disponíveis (escolha exatamente uma):
- bug
- elogio
- pagamento
- performance
- atendimento
- outros

Sentimentos disponíveis (escolha exatamente um):
- positivo
- negativo
- neutro

Responda SOMENTE com um JSON válido, sem texto adicional.
Formato esperado:
{{"categoria": "bug", "sentimento": "negativo", "resumo": "Breve resumo do feedback."}}

Feedback:
{feedback_text}
"""

    try:
        response = client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()

        # Extrai JSON mesmo que o modelo adicione texto extra
        match = re.search(r'\{.*?\}', content, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            result = json.loads(content)

        return {
            "feedback_id": feedback_id,
            "categoria": result.get("categoria", "outros"),
            "sentimento": result.get("sentimento", "neutro"),
            "resumo": result.get("resumo", feedback_text[:80])
        }

    except Exception as e:
        print(f"  ⚠️  Erro ao analisar feedback {feedback_id}: {e}")
        return {
            "feedback_id": feedback_id,
            "categoria": "outros",
            "sentimento": "neutro",
            "resumo": feedback_text[:80]
        }


def save_results(results: list[dict], path: str = "feedback_analysis_results.json") -> None:
    """Salva os resultados individuais em JSON."""
    output_path = Path(__file__).parent / path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Resultados salvos em: {output_path}")


def generate_report(results: list[dict]) -> dict:
    """Gera relatório consolidado a partir dos resultados."""
    total = len(results)
    categorias = Counter(r["categoria"] for r in results)
    sentimentos = Counter(r["sentimento"] for r in results)

    # Identifica temas principais baseado nas categorias mais frequentes
    principais_pontos = []
    for cat, count in categorias.most_common(3):
        pct = round(count / total * 100)
        if cat == "bug":
            principais_pontos.append(f"Bugs representam {pct}% dos feedbacks — requer atenção técnica.")
        elif cat == "elogio":
            principais_pontos.append(f"Elogios representam {pct}% — usuários satisfeitos com interface/atendimento.")
        elif cat == "pagamento":
            principais_pontos.append(f"Problemas de pagamento em {pct}% dos feedbacks — impacto direto em receita.")
        elif cat == "performance":
            principais_pontos.append(f"Lentidão e performance citados em {pct}% dos feedbacks.")
        elif cat == "atendimento":
            principais_pontos.append(f"Feedbacks de atendimento representam {pct}% — maioria positiva.")
        else:
            principais_pontos.append(f"Categoria '{cat}' aparece em {pct}% dos feedbacks.")

    if sentimentos.get("negativo", 0) > total * 0.5:
        principais_pontos.append("Sentimento predominantemente negativo — revisão de produto recomendada.")

    return {
        "total_feedbacks": total,
        "categorias": dict(categorias),
        "sentimentos": dict(sentimentos),
        "principais_pontos": principais_pontos
    }


def save_report(report: dict, path: str = "feedback_report.json") -> None:
    """Salva o relatório consolidado em JSON."""
    output_path = Path(__file__).parent / path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"✅ Relatório salvo em: {output_path}")


def print_report(report: dict) -> None:
    """Imprime o relatório formatado no console."""
    print("\n" + "="*60)
    print("        RELATÓRIO DE FEEDBACKS — ANÁLISE CONSOLIDADA")
    print("="*60)
    print(f"\n📊 Total de feedbacks analisados: {report['total_feedbacks']}")

    print("\n📁 Por categoria:")
    for cat, count in sorted(report["categorias"].items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"   {cat:<15} {count:>3}  {bar}")

    print("\n😊 Por sentimento:")
    for sent, count in sorted(report["sentimentos"].items(), key=lambda x: -x[1]):
        emoji = {"positivo": "✅", "negativo": "❌", "neutro": "➖"}.get(sent, "•")
        print(f"   {emoji} {sent:<12} {count}")

    print("\n💡 Principais pontos:")
    for ponto in report["principais_pontos"]:
        print(f"   • {ponto}")

    print("\n" + "="*60)


# =============================================================================
# AGENTE PRINCIPAL
# =============================================================================

class FeedbackAnalysisAgent:
    """
    Agente que processa todos os feedbacks usando Ollama como LLM.
    Fluxo: buscar feedbacks → analisar cada um → salvar → gerar relatório.
    """

    def run(self):
        print(f"🤖 Feedback Analysis Agent iniciado")
        print(f"   Modelo: {OLLAMA_MODEL}")
        print(f"   Endpoint: {OLLAMA_BASE_URL}\n")

        # Parte 1 — Buscar feedbacks do banco
        print("📥 Buscando feedbacks do banco de dados...")
        feedbacks = get_all_feedbacks()

        if not feedbacks:
            print("❌ Nenhum feedback encontrado na tabela 'feedbacks'.")
            return

        print(f"   {len(feedbacks)} feedbacks encontrados.\n")

        # Parte 2 — Analisar cada feedback individualmente
        print("🔍 Analisando feedbacks...")
        results = []

        for fb in feedbacks:
            print(f"   → Feedback {fb['id']}: {fb['feedback_text'][:60]}...")
            analysis = analyze_feedback(fb["id"], fb["feedback_text"])
            results.append(analysis)
            print(f"      categoria={analysis['categoria']} | sentimento={analysis['sentimento']}")

        # Parte 3 — Salvar resultados individuais
        save_results(results)

        # Parte 4 — Gerar e salvar relatório consolidado
        print("\n📈 Gerando relatório consolidado...")
        report = generate_report(results)
        save_report(report)
        print_report(report)

        return report


if __name__ == "__main__":
    agent = FeedbackAnalysisAgent()
    agent.run()

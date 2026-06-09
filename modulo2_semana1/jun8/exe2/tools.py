import os
from sqlalchemy import create_engine, text
import json
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_URL = f"postgresql+psycopg2://postgres:postgres123@{DB_HOST}:5450/mydb"
engine = create_engine(DB_URL)


def get_ticket_conversation(ticket_id: int) -> dict:
    query = text("""
        SELECT speaker, message, timestamp, ticket_status
        FROM conversations
        WHERE ticket_id = :ticket_id
        ORDER BY timestamp
    """)

    with engine.begin() as conn:
        rows = conn.execute(query, {"ticket_id": ticket_id}).mappings().all()

    if not rows:
        return {
            "ticket_id": ticket_id,
            "found": False,
            "conversation_text": ""
        }

    conversation_text = "\n".join(
        f"{row['speaker']}: {row['message']}"
        for row in rows
    )

    return {
        "ticket_id": ticket_id,
        "found": True,
        "conversation_text": conversation_text
    }


def classify_category_prompt(conversation_text: str) -> dict:
    """Classifica a categoria usando Ollama (compatível com API OpenAI)"""
    from openai import OpenAI

    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    client = OpenAI(
        base_url=ollama_base_url,
        api_key="ollama"  # placeholder — Ollama não valida a key
    )

    prompt = f"""
Você é um classificador de tickets de suporte.

Classifique a conversa em apenas uma das categorias abaixo:
- login
- pagamento
- entrega
- cancelamento
- conta
- outros

Responda SOMENTE com um JSON válido com a chave "categoria", sem nenhum texto adicional.
Exemplo: {{"categoria": "pagamento"}}

Conversa:
{conversation_text}
"""

    try:
        response = client.chat.completions.create(
            model=ollama_model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        content = response.choices[0].message.content.strip()
        # Extrai o JSON mesmo que o modelo adicione texto extra
        import re
        match = re.search(r'\{.*?\}', content, re.DOTALL)
        if match:
            result = json.loads(match.group())
        else:
            result = json.loads(content)

        return {
            "categoria": result.get("categoria", "outros"),
            "metodo": "llm_ollama"
        }

    except Exception as e:
        print("Erro classify_category:", e)
        return {
            "categoria": "outros",
            "metodo": "fallback_erro"
        }


def detect_followup(conversation_text: str) -> dict:
    lines = [line.strip() for line in conversation_text.split("\n") if line.strip()]

    if not lines:
        return {
            "precisa_followup": False,
            "motivo": "sem mensagens",
            "ultima_mensagem_foi_do_atendente": False
        }

    last_line = lines[-1].lower()
    ultima_mensagem_foi_do_atendente = last_line.startswith("atendente:")

    return {
        "precisa_followup": ultima_mensagem_foi_do_atendente,
        "motivo": (
            "última mensagem foi do atendente"
            if ultima_mensagem_foi_do_atendente
            else "última mensagem foi do cliente"
        ),
        "ultima_mensagem_foi_do_atendente": ultima_mensagem_foi_do_atendente
    }


def save_agent_run(agent_name: str, ticket_id: int, input_text: str, output_text: dict) -> None:
    query = text("""
        INSERT INTO agent_runs (
            agent_name,
            ticket_id,
            input_text,
            output_text
        )
        VALUES (
            :agent_name,
            :ticket_id,
            :input_text,
            :output_text
        )
    """)

    with engine.begin() as conn:
        conn.execute(
            query,
            {
                "agent_name": agent_name,
                "ticket_id": ticket_id,
                "input_text": input_text,
                "output_text": json.dumps(output_text, ensure_ascii=False)
            }
        )


TOOL_MAP = {
    "get_ticket_conversation": get_ticket_conversation,
    "classify_category_prompt": classify_category_prompt,
    "detect_followup": detect_followup,
}
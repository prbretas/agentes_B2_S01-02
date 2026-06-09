import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

from tools import (
    get_ticket_conversation,
    classify_category,
    detect_followup,
    save_agent_run
)


def find_env():
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    return None  # .env é opcional quando usando Ollama


env_path = find_env()
if env_path:
    load_dotenv(env_path, override=True)

# Ollama expõe uma API compatível com OpenAI em localhost:11434/v1
# Não precisa de API key — qualquer string serve como placeholder
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class SupportTicketAgentBasic:

    def __init__(self):
        self.client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama"  # placeholder — Ollama não valida a key
        )

    def summarize(self, conversation: str) -> str:
        response = self.client.chat.completions.create(
            model=OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"""Gere um resumo curto da conversa abaixo.

Conversa:
{conversation}

Responda apenas com o resumo."""
                }
            ]
        )

        return response.choices[0].message.content

    def run(self, ticket_id: int) -> dict:
        conversation = get_ticket_conversation(ticket_id)

        if not conversation:
            return {
                "ticket_id": ticket_id,
                "erro": "ticket não encontrado"
            }

        category = classify_category(conversation)
        followup = detect_followup(conversation)
        summary = self.summarize(conversation)

        result = {
            "ticket_id": ticket_id,
            "categoria": category["categoria"],
            "resumo": summary,
            "precisa_followup": followup["precisa_followup"],
            "motivo_followup": followup["motivo"]
        }

        save_agent_run(
            agent_name="support_agent_basic",
            ticket_id=ticket_id,
            input_text=conversation,
            output_text=result
        )

        return result
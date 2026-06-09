import os
import json
import re

from dotenv import load_dotenv
from openai import OpenAI
from tools import get_ticket_conversation

load_dotenv()

# Ollama expõe uma API compatível com OpenAI em localhost:11434/v1
# Não precisa de API key — qualquer string serve como placeholder
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

client = OpenAI(
    base_url=OLLAMA_BASE_URL,
    api_key="ollama"  # placeholder — Ollama não valida a key
)


def classify_category(conversation_text: str) -> dict:
    prompt = f"""
Você é um classificador de tickets de suporte.

Classifique a conversa em apenas uma das categorias abaixo:
- acesso
- pagamento
- entrega
- cancelamento
- conta
- outros

Regras:
- Escolha somente uma categoria.
- Considere o assunto principal da conversa.
- Se não estiver claro, use "outros".

Responda SOMENTE com um JSON válido com a chave "categoria", sem nenhum texto adicional.
Exemplo: {{"categoria": "pagamento"}}

Conversa:
{conversation_text}
"""

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content.strip()

    # Extrai o JSON mesmo que o modelo adicione texto extra
    match = re.search(r'\{.*?\}', content, re.DOTALL)
    if match:
        result = json.loads(match.group())
    else:
        result = json.loads(content)

    return {
        "categoria": result.get("categoria", "outros"),
        "metodo": "llm_ollama"
    }


if __name__ == "__main__":
    ticket_id = 1001

    ticket = get_ticket_conversation(ticket_id)

    if not ticket:
        print("Ticket não encontrado")
        raise SystemExit(1)

    conversation_text = ticket["conversation_text"]

    print("\n=== CONVERSA ===")
    print(conversation_text)

    result = classify_category(conversation_text)

    print("\n=== CLASSIFICAÇÃO ===")
    print(result)

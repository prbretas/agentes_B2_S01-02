import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from tools import TOOL_MAP, save_agent_run


def find_env():
    current = Path(__file__).resolve()
    for parent in current.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file
    return None  # .env é opcional quando usando Ollama


env_path = find_env()
if env_path:
    print("env_path:", env_path)
    load_dotenv(env_path, override=True)

# Ollama expõe uma API compatível com OpenAI em localhost:11434/v1
# Não precisa de API key — qualquer string serve como placeholder
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


class SupportTicketAgentToolCalling:
    def __init__(self):
        self.client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama"  # placeholder — Ollama não valida a key
        )

        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_ticket_conversation",
                    "description": "Busca a conversa completa de um ticket no banco de dados",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {
                                "type": "integer",
                                "description": "ID do ticket"
                            }
                        },
                        "required": ["ticket_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "classify_category_prompt",
                    "description": "Classifica a categoria principal do problema com base na conversa",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation_text": {
                                "type": "string",
                                "description": "Texto da conversa consolidada"
                            }
                        },
                        "required": ["conversation_text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_followup",
                    "description": "Detecta se o ticket precisa de follow-up com base na última mensagem",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "conversation_text": {
                                "type": "string",
                                "description": "Texto da conversa consolidada"
                            }
                        },
                        "required": ["conversation_text"]
                    }
                }
            }
        ]

    def run(self, ticket_id: int) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um agente de suporte com acesso a ferramentas.\n"
                    "Analise o ticket informado usando as ferramentas disponíveis.\n"
                    "No final, devolva um JSON válido com estas chaves:\n"
                    "ticket_id, categoria, resumo, precisa_followup, motivo_followup, status_sugerido.\n\n"
                    "A categoria deve ser EXATAMENTE uma destas opções:\n"
                    "login, pagamento, entrega, cancelamento, conta, outros.\n"
                    "Não reescreva a categoria."
                )
            },
            {
                "role": "user",
                "content": f"Analise o ticket {ticket_id}."
            }
        ]

        conversation_for_log = ""
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            response = self.client.chat.completions.create(
                model=OLLAMA_MODEL,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # Se não há tool calls, retorna a resposta final
            if not assistant_message.tool_calls:
                final_text = assistant_message.content

                save_agent_run(
                    agent_name="support_agent_toolcalling",
                    ticket_id=ticket_id,
                    input_text=conversation_for_log,
                    output_text={"response": final_text}
                )

                return final_text

            # Adiciona a mensagem do assistente com tool calls
            messages.append(assistant_message)

            # Processa cada tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print(f"\n🔧 Chamando tool: {function_name}")
                print(f"   Argumentos: {arguments}")

                # Executa a tool
                result = TOOL_MAP[function_name](**arguments)

                # Salva a conversa para log
                if function_name == "get_ticket_conversation":
                    conversation_for_log = result.get("conversation_text", "")

                print(f"   Resultado: {str(result)[:100]}...")

                # Adiciona o resultado da tool às mensagens
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        return json.dumps({
            "erro": "máximo de iterações atingido",
            "ticket_id": ticket_id
        })


if __name__ == "__main__":
    agent = SupportTicketAgentToolCalling()
    result = agent.run(1001)
    print("\n=== RESULTADO TOOL CALLING ===")
    print(result)

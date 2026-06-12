"""
llm_solution.py

Exercício — Contrato de Dados com Pydantic + LLM

Esta versão usa OpenAI para analisar feedbacks e valida a saída com Pydantic.
"""

import os
import json
from enum import Enum
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError, field_validator


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não encontrada no .env")

client = OpenAI(api_key=OPENAI_API_KEY)


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class Category(str, Enum):
    bug = "bug"
    feature_request = "feature_request"
    praise = "praise"
    support = "support"
    other = "other"


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class FeedbackAnalysis(BaseModel):
    sentiment: Sentiment
    category: Category
    priority: Priority
    summary: str = Field(..., min_length=10, max_length=300)
    confidence: float = Field(..., ge=0, le=1)

    @field_validator("summary")
    @classmethod
    def summary_must_not_be_generic(cls, value: str) -> str:
        generic_summaries = {
            "good",
            "bad",
            "ok",
            "user feedback",
            "feedback",
        }

        if value.strip().lower() in generic_summaries:
            raise ValueError("summary é genérico demais")

        return value


def call_llm(feedback: str, previous_error: Optional[str] = None) -> str:
    correction_instruction = ""

    if previous_error:
        correction_instruction = f"""
Your previous response failed validation.

Validation error:
{previous_error}

Return a corrected JSON object.
"""

    prompt = f"""
You are a feedback analysis assistant.

Analyze the user feedback and return only valid JSON.

Required JSON schema:
{{
  "sentiment": "positive | neutral | negative",
  "category": "bug | feature_request | praise | support | other",
  "priority": "low | medium | high",
  "summary": "short but specific summary, between 10 and 300 characters",
  "confidence": number between 0 and 1
}}

Rules:
- Return only JSON.
- Do not include markdown.
- Do not include explanations.
- Use only the allowed values.
- The summary must be specific.

{correction_instruction}

Feedback:
{feedback}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=0,
    )

    return response.output_text.strip()


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()

    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def validate_llm_output(raw_output: str) -> FeedbackAnalysis:
    parsed = extract_json(raw_output)

    if parsed is None:
        raise ValueError("O modelo não retornou JSON válido.")

    return FeedbackAnalysis.model_validate(parsed)


def analyze_feedback(feedback: str, max_attempts: int = 2) -> Dict[str, Any]:
    previous_error = None

    for attempt in range(1, max_attempts + 1):
        print(f"\nTentativa {attempt}")

        raw_output = call_llm(
            feedback=feedback,
            previous_error=previous_error,
        )

        print("Saída bruta do modelo:")
        print(raw_output)

        try:
            validated = validate_llm_output(raw_output)

            return {
                "status": "valid",
                "attempt": attempt,
                "analysis": validated.model_dump(),
            }

        except (ValidationError, ValueError) as error:
            previous_error = str(error)
            print("Falhou na validação:")
            print(previous_error)

    return {
        "status": "fallback",
        "reason": "O modelo não conseguiu gerar uma saída válida dentro do contrato.",
        "analysis": {
            "sentiment": "neutral",
            "category": "other",
            "priority": "low",
            "summary": "Feedback requires manual review.",
            "confidence": 0.0,
        },
    }


if __name__ == "__main__":
    examples = [
        "O aplicativo trava quando tento finalizar o pagamento.",
        "Gostei muito da nova interface, ficou mais fácil de usar.",
        "Não consigo falar com o suporte e preciso resolver meu pedido.",
        "Seria ótimo ter modo escuro no aplicativo.",
    ]

    for feedback in examples:
        print("\n" + "=" * 80)
        print("FEEDBACK:")
        print(feedback)

        result = analyze_feedback(feedback)

        print("\nRESULTADO FINAL:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

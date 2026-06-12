"""
solution.py

Exercício — Contrato de Dados com Pydantic

Esta versão não usa LLM.
Ela mostra como validar dados estruturados usando Pydantic.
"""

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field, ValidationError, field_validator


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


def validate_feedback_analysis(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validated = FeedbackAnalysis.model_validate(data)

        return {
            "status": "valid",
            "data": validated.model_dump(),
            "errors": None,
        }

    except ValidationError as error:
        return {
            "status": "invalid",
            "data": data,
            "errors": error.errors(),
        }


if __name__ == "__main__":
    examples: List[Dict[str, Any]] = [
        {
            "sentiment": "negative",
            "category": "bug",
            "priority": "high",
            "summary": "User reports that the app crashes during payment.",
            "confidence": 0.92,
        },
        {
            "sentiment": "bad",
            "category": "bug",
            "priority": "urgent",
            "summary": "App problem.",
            "confidence": 1.8,
        },
        {
            "sentiment": "positive",
            "category": "praise",
            "summary": "User liked the new interface.",
            "confidence": 0.85,
        },
        {
            "sentiment": "neutral",
            "category": "other",
            "priority": "low",
            "summary": "feedback",
            "confidence": 0.5,
        },
    ]

    for index, example in enumerate(examples, start=1):
        print("\n" + "=" * 80)
        print(f"EXEMPLO {index}")
        print("=" * 80)

        result = validate_feedback_analysis(example)

        print("Status:", result["status"])

        if result["status"] == "valid":
            print("Dados validados:")
            print(result["data"])
        else:
            print("Erros encontrados:")
            for err in result["errors"]:
                print("-", err["loc"], err["msg"])

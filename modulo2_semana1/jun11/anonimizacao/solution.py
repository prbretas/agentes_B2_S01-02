"""
solution.py

Exercício — Proteção de PII com Microsoft Presidio

Este exemplo mostra como detectar e anonimizar dados pessoais
antes de mostrar uma resposta para o usuário.

A ideia principal:

1. O banco ou sistema retorna dados
2. Os dados podem conter PII
3. O Presidio detecta PII
4. O Presidio anonimiza PII
5. A aplicação mostra apenas a versão segura

Para instalar:

pip install -r requirements.txt
"""

import json
from typing import Any, Dict, List

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine


# ---------------------------------------------------------------------------
# 1. Criar engines do Presidio
# ---------------------------------------------------------------------------

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()


# ---------------------------------------------------------------------------
# 2. Exemplo de recognizer customizado para CPF brasileiro
# ---------------------------------------------------------------------------

cpf_pattern = Pattern(
    name="cpf_pattern",
    regex=r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
    score=0.85,
)

cpf_recognizer = PatternRecognizer(
    supported_entity="BR_CPF",
    patterns=[cpf_pattern],
)

analyzer.registry.add_recognizer(cpf_recognizer)


# ---------------------------------------------------------------------------
# 3. Dados de exemplo
# ---------------------------------------------------------------------------

records = [
    {
        "user_name": "Maria Silva",
        "email": "maria.silva@example.com",
        "phone": "512-555-0199",
        "cpf": "123.456.789-00",
        "message": "O app travou na tela de pagamento.",
        "sentiment": "negative",
    },
    {
        "user_name": "Robert Washington",
        "email": "robert.washington@example.com",
        "phone": "214-555-0389",
        "cpf": "987.654.321-00",
        "message": "O sistema está muito lento.",
        "sentiment": "negative",
    },
    {
        "user_name": "Ana Pereira",
        "email": "ana.pereira@example.com",
        "phone": None,
        "cpf": None,
        "message": "Gostei muito da nova interface.",
        "sentiment": "positive",
    },
]


# ---------------------------------------------------------------------------
# 4. Funções auxiliares
# ---------------------------------------------------------------------------

def detect_pii_in_text(text: str) -> List[Dict[str, Any]]:
    """
    Detecta PII em um texto usando Presidio Analyzer.

    Retorna uma lista de entidades encontradas.
    """

    results = analyzer.analyze(
        text=text,
        language="en",
    )

    detected_entities = []

    for result in results:
        detected_entities.append(
            {
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": round(result.score, 2),
                "text": text[result.start:result.end],
            }
        )

    return detected_entities


def anonymize_text(text: str) -> str:
    """
    Anonimiza PII em um texto usando Presidio Analyzer + Anonymizer.
    """

    analyzer_results = analyzer.analyze(
        text=text,
        language="en",
    )

    anonymized_result = anonymizer.anonymize(
        text=text,
        analyzer_results=analyzer_results,
    )

    return anonymized_result.text


def anonymize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anonimiza todos os valores textuais de um dicionário.

    Isso simula uma camada de proteção antes de mostrar
    o resultado para o usuário.
    """

    safe_record = {}

    for key, value in record.items():
        if value is None:
            safe_record[key] = None
        elif isinstance(value, str):
            safe_record[key] = anonymize_text(value)
        else:
            safe_record[key] = value

    return safe_record


def anonymize_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Anonimiza uma lista de registros.
    """

    return [
        anonymize_record(record)
        for record in records
    ]


def records_to_text(records: List[Dict[str, Any]]) -> str:
    """
    Transforma registros em texto para facilitar a demonstração de detecção.
    """

    return json.dumps(
        records,
        indent=2,
        ensure_ascii=False,
        default=str,
    )


# ---------------------------------------------------------------------------
# 5. Demonstração
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("1. Dados originais")
    print("=" * 80)

    original_text = records_to_text(records)
    print(original_text)

    print("\n" + "=" * 80)
    print("2. PII detectada no texto completo")
    print("=" * 80)

    detected = detect_pii_in_text(original_text)
    print(json.dumps(detected, indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("3. Dados anonimizados")
    print("=" * 80)

    safe_records = anonymize_records(records)
    print(records_to_text(safe_records))

    print("\n" + "=" * 80)
    print("4. Mensagem principal")
    print("=" * 80)

    print("Guardrails protegem ações.")
    print("Presidio protege dados.")
    print("Os dois são necessários.")

# Project Rules — agentes_B2_S01-02

Estas regras se aplicam a todos os exercícios deste projeto e devem ser seguidas sempre que uma solução for implementada ou executada.

---

## Logging de Exercícios

Todo exercício implementado deve gerar logs persistentes da execução para análise posterior.

### Estrutura de pastas

Cada exercício deve ter uma pasta `logs/` dentro do seu diretório:

```
modulo2_semana1/
└── jun11/
    └── guardrails/
        ├── guardrails_ollama.py
        └── logs/
            ├── run_20260611_143000.json
            └── run_20260611_150000.json
```

### O que deve ser salvo no log

Cada execução deve gerar um arquivo `.json` com o seguinte conteúdo:

```json
{
  "timestamp": "2026-06-11T14:30:00",
  "exercise": "guardrails",
  "module": "modulo2_semana1/jun11",
  "model": "llama3.2",
  "results": [
    {
      "input": "pergunta ou entrada do usuário",
      "output": "resposta ou resultado gerado",
      "status": "success | blocked | error",
      "details": {}
    }
  ]
}
```

### Nome do arquivo de log

Usar o padrão: `run_YYYYMMDD_HHMMSS.json`

Exemplo: `run_20260611_143000.json`

### Regras obrigatórias

1. A pasta `logs/` deve ser criada automaticamente pelo script se não existir.
2. Cada execução gera um arquivo de log separado (nunca sobrescrever).
3. O log deve capturar tanto os casos de sucesso quanto os bloqueios/erros.
4. O log deve registrar o modelo LLM usado e o timestamp da execução.
5. Erros de execução também devem ser logados (não silenciados).
6. A pasta `logs/` deve estar no `.gitignore` — logs ficam apenas localmente.
7. Nunca commitar a pasta `logs/` nem os arquivos dentro dela.
8. A pasta `logs/` é criada automaticamente na execução dos testes.

### Implementação padrão

Todo script de exercício deve importar e usar o seguinte padrão de logging:

```python
import json
from datetime import datetime
from pathlib import Path

def save_log(exercise_name: str, module: str, model: str, results: list):
    """Salva o log da execução na pasta logs/ do exercício."""
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"run_{timestamp}.json"

    log_data = {
        "timestamp": datetime.now().isoformat(),
        "exercise": exercise_name,
        "module": module,
        "model": model,
        "results": results
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 Log salvo em: {log_file}")
    return log_file
```

---

## Boas práticas gerais

- Sempre usar `.env` para configurações (nunca hardcode de chaves ou senhas).
- Preferir Ollama como LLM local (já configurado no projeto).
- Porta padrão do PostgreSQL no Podman: `5450`.
- Banco padrão: `mydb` / usuário: `postgres` / senha: `postgres123`.
- Ao adaptar exercícios da aula para Podman, manter o mesmo nome de arquivo com sufixo `_ollama` (ex: `guardrails_ollama.py`).
- Sempre testar com casos permitidos E casos que devem ser bloqueados/rejeitados.

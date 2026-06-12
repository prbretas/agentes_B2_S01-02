# Aula Jun/11 — Segurança em Agentes de IA

Exercícios práticos sobre proteção de agentes LLM: guardrails, prompt injection, anonimização de dados e contratos de dados com Pydantic.

---

## Pré-requisitos

Antes de rodar qualquer exercício, garanta que o ambiente está pronto:

| Requisito | Como verificar |
|-----------|---------------|
| Podman Desktop rodando | VM `podman-machine-default` em **Running** |
| PostgreSQL disponível | `localhost:5450` (banco `mydb`) |
| Ollama rodando | `http://localhost:11434` com modelo `llama3.2` |
| venv ativo | `.venv\Scripts\Activate.ps1` na raiz do módulo |

```powershell
# 1. Subir containers (PostgreSQL + PgAdmin)
cd modulo2_semana1
.\podman_start.ps1

# 2. Ativar o ambiente virtual
.\.venv\Scripts\Activate.ps1

# 3. Verificar Ollama
ollama list   # deve aparecer llama3.2
```

> Se o Ollama não estiver rodando, abra um terminal separado e execute: `ollama serve`

---

## Estrutura da aula

```
jun11/
├── README.md                        ← este arquivo
├── docker_set_up_ambiente.md        ← setup para quem usa Docker
├── podman_set_up_ambiente.md        ← setup para quem usa Podman (Windows)
│
├── guardrails/                      ← Exercício 1
│   ├── guardrails_exercicio.md      ← enunciado
│   ├── guardrails_ollama.py         ← solução com Ollama + logs
│   ├── solution.py                  ← solução original (OpenAI)
│   └── logs/                        ← logs gerados automaticamente
│
├── prompt_injection/                ← Exercício 2
│   ├── prompt_injection_exercicio.md ← enunciado
│   ├── prompt_injection_ollama.py   ← solução com Ollama + logs
│   ├── solution.py                  ← solução original (OpenAI)
│   ├── vulnerable_example.py        ← exemplo vulnerável (didático)
│   └── logs/                        ← logs gerados automaticamente
│
├── anonimizacao/                    ← Exercício 3
│   ├── anonimizacao_exercicio.md    ← enunciado
│   └── solution.py                  ← solução
│
└── pydantic_data_contract/          ← Exercício 4
    ├── readme.md                    ← enunciado
    ├── solution.py                  ← solução com Pydantic
    └── llm_solution.py              ← solução com LLM
```

---

## Exercício 1 — Guardrails SQL

**Tema:** proteger um agente que gera SQL com LLM antes de executar no banco.

**O que aprende:** nunca executar SQL gerado por LLM sem validação. Guardrails bloqueiam comandos perigosos (DELETE, DROP, etc.), tabelas não autorizadas e colunas sensíveis.

**Como rodar:**

```powershell
cd jun11\guardrails
python guardrails_ollama.py
```

**Arquivo de enunciado:** `guardrails_exercicio.md`

**Saída esperada:** queries permitidas executam e retornam dados; queries perigosas são bloqueadas com o motivo.

**Logs:** salvos automaticamente em `guardrails/logs/run_YYYYMMDD_HHMMSS.json`

---

## Exercício 2 — Prompt Injection

**Tema:** proteger um agente de análise de feedbacks contra instruções maliciosas escondidas no texto do usuário.

**O que aprende:** nem todo texto enviado ao modelo é instrução. Dados de usuário são não confiáveis e devem ser isolados com tags `<untrusted_feedback>`. Guardrails de entrada e saída completam a proteção.

**Como rodar:**

```powershell
# Versão protegida (recomendada)
cd jun11\prompt_injection
python prompt_injection_ollama.py

# Versão vulnerável (apenas para comparação didática — requer OpenAI)
python vulnerable_example.py
```

**Arquivo de enunciado:** `prompt_injection_exercicio.md`

**Saída esperada:**
- Feedbacks normais → analisados com sucesso
- Feedbacks com injeção detectada → marcados como `contains_prompt_injection: true`
- Ataques com ações perigosas → bloqueados com status `blocked_or_fallback`

**Logs:** salvos automaticamente em `prompt_injection/logs/run_YYYYMMDD_HHMMSS.json`

---

## Exercício 3 — Anonimização de Dados

**Tema:** detectar e anonimizar dados pessoais (PII) antes de enviar textos ao LLM.

**O que aprende:** como usar a biblioteca Presidio para identificar e mascarar entidades como CPF, email, nome, telefone — protegendo dados sensíveis de usuários.

**Como rodar:**

```powershell
cd jun11\anonimizacao
python solution.py
```

**Arquivo de enunciado:** `anonimizacao_exercicio.md`

---

## Exercício 4 — Pydantic Data Contract

**Tema:** usar Pydantic para validar e garantir a estrutura das saídas do LLM.

**O que aprende:** como forçar o modelo a retornar JSON estruturado e validar cada campo com tipos e regras, criando um contrato de dados confiável entre o LLM e a aplicação.

**Como rodar:**

```powershell
cd jun11\pydantic_data_contract

# Versão com schema Pydantic
python solution.py

# Versão integrada com LLM
python llm_solution.py
```

**Arquivo de enunciado:** `readme.md`

---

## Sobre os logs

Todo exercício rodado gera automaticamente um arquivo de log em `logs/run_YYYYMMDD_HHMMSS.json` dentro da pasta do exercício.

O log contém:
- Timestamp da execução
- Modelo LLM usado
- Todas as entradas testadas
- Resultado de cada uma (status, motivo, análise)

Para visualizar um log:

```powershell
# Listar logs de um exercício
Get-ChildItem jun11\guardrails\logs\
Get-ChildItem jun11\prompt_injection\logs\

# Ver conteúdo do log mais recente
Get-Content jun11\prompt_injection\logs\(Get-ChildItem jun11\prompt_injection\logs\ | Sort-Object LastWriteTime -Descending | Select-Object -First 1).Name | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## Parar o ambiente

Ao terminar os exercícios:

```powershell
cd modulo2_semana1
.\podman_stop.ps1
```

Para limpar tudo (containers + volumes):

```powershell
.\podman_stop.ps1 -Clean
```

---

## Conexão com outros módulos

| Exercício | Protege |
|-----------|---------|
| Guardrails SQL | Ações no banco de dados |
| Prompt Injection | Instruções do agente |
| Anonimização | Dados pessoais dos usuários |
| Pydantic Contract | Estrutura das saídas do LLM |

> Juntos formam uma camada completa de segurança para agentes de IA em produção.

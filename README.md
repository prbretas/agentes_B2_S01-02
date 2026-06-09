# 🤖 Agentes de IA - Curso Prático

> Repositório de exemplos e exercícios práticos sobre desenvolvimento de agentes de IA, desde regras simples até sistemas complexos com LLMs.

---

## 📚 Índice

- [Visão Geral](#-visão-geral)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Setup](#️-setup)
- [Exercícios](#-exercícios)
- [Ferramentas](#-ferramentas)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Visão Geral

Este projeto demonstra a evolução de sistemas de IA:

```
Assistant → Workflow → Agent
```

Usando um caso de uso realista: **sistema de suporte ao cliente** com análise automática de tickets.

### Tecnologias

- 🐍 Python 3.9+
- 🐘 PostgreSQL 16
- 🤖 LLMs (Anthropic Claude, OpenAI, Google Gemini)
- 🔍 Qdrant (banco vetorial)
- 📊 Langfuse (observabilidade)
- 🐳 Docker & Docker Compose

---

## 🧱 Estrutura do Projeto

```
.
├── 📄 Dockerfile
├── 📄 docker-compose.yml
├── 📄 init.sql
├── 📄 load_data.py
├── 📄 requirements.txt
├── 📁 exemplos_exercicios/
│   ├── 📁 exemplos/          # Exemplos de código
│   ├── 📁 exercicio_1/       # Análise de métricas
│   ├── 📁 exercicio_2/       # Classificação de conversas
│   └── 📁 agentes/
│       ├── 📁 topic_tools/
│       │   ├── exe1/         # Agente baseado em regras
│       │   ├── exe2/         # Agente com LLM + tool calling
│       │   └── exe3/         # Análise de feedbacks
│       ├── 📁 topic_memory/
│       │   └── exe4/         # Agentes com/sem memória
│       ├── 📁 topic_guardrails/
│       │   ├── exe5/         # Guardrails e validação
│       │   └── exe6/         # Guardrails avançados
│       ├── 📁 topic_exa_search/
│       │   ├── exe7/         # Busca externa com Exa
│       │   └── exe8/         # Busca avançada
│       ├── 📁 banco_vetorial/ # Qdrant + embeddings
│       ├── 📁 planner/        # Agente planejador
│       └── 📁 react/          # Agente ReAct
└── 📁 .kiro/
    ├── hooks/                # Automações
    └── steering/             # Regras e contexto

```

---

## ⚙️ Setup

### Pré-requisitos

- ✅ Podman Desktop instalado (substituto do Docker para PCs corporativos)
- ✅ Python 3.9+ instalado
- ✅ Chaves de API configuradas no `.env`

> **Nota:** O projeto foi adaptado para usar **Podman** em vez de Docker, compatível com ambientes corporativos onde o Docker Desktop não pode ser instalado.

### ⚡ Setup Automático (Recomendado)

Um único script configura todo o ambiente: venv Python, dependências, containers e banco de dados.

```powershell
cd modulo2_semana1
.\setup.ps1
```

Após o setup, edite o `.env` gerado com suas chaves de API e execute os exercícios.

---

### 🐳 Setup Manual com Podman

#### 1️⃣ Subir os serviços

```powershell
cd modulo2_semana1
.\podman_start.ps1
```

Isso sobe:
- `postgres_db` — PostgreSQL 16 com pgvector na porta `5450`
- `pgadmin` — Interface web na porta `5050`

#### 2️⃣ Criar ambiente virtual e instalar dependências

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### 3️⃣ Rodar scripts

```powershell
python modulo2_semana1\jun8\exe1\support_agent_basic.py
```

#### 4️⃣ Parar tudo

```powershell
.\podman_stop.ps1
```

Para remover também os dados:

```powershell
.\podman_stop.ps1 -Clean
```

---

## 🔐 Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# Configurações gerais
SUMMARY_MAX_POINTS=4
SUMMARY_SENTIMENT=true
SUMMARY_PRIORITY_RULES=true

# APIs de LLM
ANTHROPIC_API_KEY=sua-chave-aqui
OPENAI_API_KEY=sua-chave-aqui
GEMINI_API_KEY=sua-chave-aqui

# Exa Search
EXA_API_KEY=sua-chave-aqui

# Langfuse (observabilidade)
LANGFUSE_PUBLIC_KEY=sua-chave-aqui
LANGFUSE_SECRET_KEY=sua-chave-aqui
LANGFUSE_BASE_URL=http://localhost:3000
```

---

## 🎓 Exercícios

### 📘 Exercício 1 - Agente Baseado em Regras

**Objetivo:** Entender a estrutura básica de um agente e suas limitações.

**Características:**
- ✅ Não utiliza IA ou LLM
- ✅ Funciona com regras explícitas (if/else)
- ✅ Totalmente previsível e controlável
- ✅ Baixo custo computacional
- ✅ Fácil de entender e debugar

**Limitações:**
- ❌ Depende de palavras exatas
- ❌ Não captura contexto ou intenção
- ❌ Difícil de escalar
- ❌ Falha em casos ambíguos

**Como rodar:**
```bash
python exemplos_exercicios/agentes/topic_tools/exe1/run_support_agent.py <ticket_id>
```

---

### 📗 Exercício 2 - Agente com LLM + Tool Calling

**Objetivo:** Construir agentes inteligentes que tomam decisões e acionam ferramentas.

**Características:**
- ✅ Utiliza LLM (Gemini/Claude)
- ✅ Capacidade de decisão dinâmica
- ✅ Integração com ferramentas (tool calling)
- ✅ Suporte a saída estruturada (JSON)
- ✅ Mais flexível e adaptável

**Melhorias em relação ao Exercício 1:**
- ✨ Entende variações de linguagem natural
- ✨ Não depende de palavras exatas
- ✨ Mais robusto para casos reais
- ✨ Reduz necessidade de regras manuais
- ✨ Mais fácil de escalar

**Como rodar:**
```bash
python exemplos_exercicios/agentes/topic_tools/exe2/run_support_agent.py <ticket_id>
```

---

### 📙 Exercício 3 - Análise de Feedbacks

**Objetivo:** Processar e analisar feedbacks de clientes usando LLM.

**Como rodar:**
```bash
cd exemplos_exercicios/agentes/topic_tools/exe3
python run_feedback_analysis.py
```

---

### 📕 Exercício 4 - Memória em Agentes

**Objetivo:** Comparar agentes com e sem memória de contexto.

**Arquivos:**
- `tool_no_mem.py` - Análise sem histórico
- `tool_with_mem.py` - Análise com histórico (Gemini)
- `tool_with_mem_claude.py` - Análise com histórico (Claude)

**Como rodar:**
```bash
cd exemplos_exercicios/agentes/topic_memory/exe4
python tool_no_mem.py
python tool_with_mem_claude.py
```

---

### 📔 Exercício 5 - Guardrails

**Objetivo:** Implementar validações e controles de segurança em agentes.

**Como rodar:**
```bash
cd exemplos_exercicios/agentes/topic_guardrails/exe5
python run_guardrail_agent.py
```

---

### 📓 Exercício 7 - Busca Externa com Exa

**Objetivo:** Integrar busca externa de informações usando Exa AI.

**Como rodar:**
```bash
cd exemplos_exercicios/agentes/topic_exa_search/exe7
python test_exa.py
```

---

## 🛠 Ferramentas

### 🗄️ DBeaver - Visualização de Dados

Interface gráfica para explorar o banco PostgreSQL.

**Download:** https://dbeaver.io/download/

**Configuração de conexão:**
- Host: `localhost`
- Port: `5432`
- Database: `suporte_ai`
- Username: `admin`
- Password: `admin123`

**Queries úteis:**
```sql
-- Ver todas as conversas
SELECT * FROM conversations;

-- Ver execuções do agente
SELECT * FROM agent_runs;

-- Ver feedbacks
SELECT * FROM feedbacks;

-- Contar tickets por status
SELECT ticket_status, COUNT(*) 
FROM conversations 
GROUP BY ticket_status;
```

---

### 🔍 Qdrant Dashboard

Interface web para o banco vetorial.

**Acesso:** http://localhost:6333/dashboard

**Popular a base:**
```bash
python exemplos_exercicios/agentes/banco_vetorial/load_to_qdrant.py
```

**Executar busca:**
```bash
python exemplos_exercicios/agentes/banco_vetorial/execute_similarity_search.py
```

---

### 📊 Langfuse - Observabilidade

Ferramenta para monitorar e debugar agentes de IA.

**Iniciar:**
```bash
chmod +x start_langfuse.sh
./start_langfuse.sh
```

**Acesso:** http://localhost:3000

---

## 🔥 Troubleshooting

| Problema | Solução |
|----------|---------|
| Containers não sobem | Abrir Podman Desktop e aguardar a VM iniciar |
| Porta 5450 ocupada | Alterar no `podman_start.ps1`: `-p 5451:5432` |
| Tabela não existe | `.\podman_stop.ps1 -Clean` e depois `.\setup.ps1` |
| Erro ao puxar imagem | Desligar VPN e tentar novamente |
| Containers não param | `wsl -d podman-machine-default -- podman rm -f postgres_db pgadmin` |

---

### 📊 Verificar o Banco

```powershell
wsl -d podman-machine-default -- podman exec postgres_db psql -U postgres -d mydb -c "SELECT COUNT(*) FROM conversations;"
```

**Tabelas esperadas:**
- `conversations`, `agent_configs`, `agent_runs`, `feedbacks`, `tickets`, `backlog`, e mais 6 tabelas

---

## 📝 Licença

MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

---

**Desenvolvido com ❤️ para o curso de Agentes de IA**

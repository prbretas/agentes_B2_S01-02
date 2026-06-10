# 🐘 PostgreSQL com Podman

Configuração pronta para uso do PostgreSQL + PgAdmin com **Podman** no Windows.

> **Por que Podman e não Docker?**  
> Em PCs corporativos onde o Docker Desktop é bloqueado, o Podman é o substituto ideal — compatível com os mesmos comandos e arquivos, sem precisar de serviço com privilégios de admin.

---

## ⚡ Setup automático (recomendado)

Um único script configura tudo: venv Python, dependências, containers e banco de dados.

```powershell
# Na pasta modulo2_semana1:
.\setup.ps1
```

O que ele faz automaticamente:
1. Verifica Python e Podman/WSL
2. **Verifica se o Ollama está rodando** e se o modelo configurado está disponível
3. Cria o arquivo `.env` com modelo (se não existir)
4. Cria o ambiente virtual `.venv` e instala todas as dependências
5. Sobe PostgreSQL + PgAdmin via Podman
6. Valida que o banco está acessível e com dados

Depois do setup, use `.\run_jun8.ps1` para rodar os exercícios com um menu interativo.

**Opções do script:**
```powershell
.\setup.ps1              # setup completo
.\setup.ps1 -SkipVenv    # pula criação do venv (já existe)
.\setup.ps1 -SkipPodman  # pula os containers (só configura Python)
```

---

## 🦙 Ollama — LLM local (jun8)

Os exercícios de **jun8** usam [Ollama](https://ollama.com) como LLM local, eliminando a necessidade de chaves de API externas (OpenAI, Gemini).

### Instalar e configurar

1. Baixe e instale o Ollama: https://ollama.com
2. Baixe o modelo padrão:
   ```powershell
   ollama pull llama3.2
   ```
3. Verifique os modelos disponíveis:
   ```powershell
   ollama list
   ```

### Trocar o modelo

Edite o `.env` e altere `OLLAMA_MODEL`:
```env
OLLAMA_MODEL=llama3.2       # padrão — bom para resumo e classificação
OLLAMA_MODEL=qwen2.5        # recomendado para tool calling (exe2)
OLLAMA_MODEL=mistral-nemo   # alternativa para tool calling
```

### Rodar os exercícios

```powershell
# Menu interativo — recomendado
.\run_jun8.ps1

# Ou diretamente por linha de comando
.\run_jun8.ps1 -Exe 1   # agente básico
.\run_jun8.ps1 -Exe 2   # tool calling
.\run_jun8.ps1 -Exe 3   # análise de feedbacks
.\run_jun8.ps1 -All     # todos em sequência
```

O `run_jun8.ps1` verifica automaticamente:
- Se o Ollama está rodando
- Se o modelo configurado está disponível
- Se o banco de dados está acessível

### Scripts disponíveis por exercício

| Exercício | Script | Descrição |
|-----------|--------|-----------|
| exe1 | `jun8/exe1/support_agent_basic.py` | Agente básico: classifica, resume e detecta followup |
| exe2 | `jun8/exe2/support_agent_toolcalling.py` | Agente com loop de tool calling via Ollama |
| exe2 | `jun8/exe2/classification.py` | Classificador isolado via Ollama |
| exe3 | `jun8/exe3/feedback_agent.py` | Agente simples de feedbacks (salva JSON local) |
| exe3 | `jun8/exe3/workflow_feedbacks.py` | Workflow completo: analisa, salva no banco e gera relatório |
| exe3 | `jun8/exe3/agent_feedback.py` | Agente com tool calling completo para feedbacks |

> **Nota sobre exe3:** há três implementações — `feedback_agent.py` é o mais simples, `workflow_feedbacks.py` é o workflow estruturado da aula, e `agent_feedback.py` é a versão agente com tool calling. Todos usam Ollama.

---

## 📋 O que está incluído

- **PostgreSQL 16 com pgvector** — banco relacional + suporte a embeddings para RAG
- **PgAdmin 4** — interface web para gerenciar o PostgreSQL
- **init.sql** — cria todas as tabelas e carrega dados de exemplo automaticamente
- **podman_start.ps1** — script que sobe tudo com um comando
- **podman_stop.ps1** — script que para os containers (com opção de limpar dados)

---

## ⚙️ Pré-requisitos

1. **Podman Desktop** instalado (sem precisar de admin para o app em si)  
   Download: https://podman-desktop.io/downloads/windows

2. **WSL2 ativo** com a distro `podman-machine-default` (criada automaticamente pelo Podman Desktop)

3. Verifique no PowerShell:
   ```powershell
   wsl --list
   # deve aparecer: podman-machine-default
   ```

---

## 🚀 Subir o ambiente

### Uma linha — o script cuida de tudo

```powershell
cd modulo2_semana1
.\podman_start.ps1
```

O script:
- Cria a network necessária (com `--disable-dns`, solução para WSL sem systemd)
- Sobe `postgres_db` na porta `5450`
- Sobe `pgadmin` na porta `5051`
- Na segunda execução, apenas reinicia os containers existentes (dados preservados)

**Saída esperada:**
```
=== Podman Start — modulo2_semana1 ===

→ Network 'modulo2_semana1_default' já existe.
→ Iniciando container existente 'postgres_db'...
→ Iniciando container existente 'pgadmin'...

→ Aguardando containers iniciarem...

NAMES        STATUS        PORTS
postgres_db  Up 3 seconds  0.0.0.0:5450->5432/tcp
pgadmin      Up 3 seconds  0.0.0.0:5051->80/tcp

✅ Pronto!

   PostgreSQL : localhost:5450  (user: postgres / senha: postgres123 / db: mydb)
   PgAdmin    : http://localhost:5051  (email: admin@admin.com / senha: admin123)
```

---

## 🛑 Parar o ambiente

```powershell
# Para containers — dados preservados
.\podman_stop.ps1

# Remove containers e volumes — ⚠️ apaga todos os dados
.\podman_stop.ps1 -Clean
```

---

## 🔌 Dados de conexão

| Serviço    | Endereço              | Usuário           | Senha        |
|------------|-----------------------|-------------------|--------------|
| PostgreSQL | `localhost:5450`      | `postgres`        | `postgres123`|
| PgAdmin    | http://localhost:5051 | `admin@admin.com` | `admin123`   |

**String de conexão SQLAlchemy** (usada nos exercícios):
```
postgresql+psycopg2://postgres:postgres123@localhost:5450/mydb
```

---

## 🗂️ Tabelas criadas pelo init.sql

| Tabela           | Conteúdo                                      |
|------------------|-----------------------------------------------|
| `conversations`  | Histórico de tickets de suporte (30 registros)|
| `agent_runs`     | Execuções dos agentes                         |
| `agent_configs`  | Configurações dos agentes                     |
| `feedbacks`      | Feedbacks de clientes (30 registros)          |
| `tickets`        | Tickets simples                               |
| `backlog`        | Itens de backlog de desenvolvimento           |
| `ticket_memory`  | Memória dos agentes por ticket                |
| `sensitive_items`| Itens sensíveis (exercício de guardrails)     |
| `internal_notes` | Notas internas de atendimento                 |
| `knowledge_bases`| Bases de conhecimento                         |
| `kb_documents`   | Documentos das bases                          |
| `kb_chunks`      | Chunks dos documentos com metadados           |

---

## 💻 Comandos diretos via terminal

Todos os comandos abaixo usam `wsl -d podman-machine-default` para chamar o Podman dentro do WSL.

### Verificar containers rodando
```powershell
wsl -d podman-machine-default -- podman ps
```

### Entrar no console psql interativo
```powershell
wsl -d podman-machine-default -- podman exec -it postgres_db psql -U postgres -d mydb
```

Dentro do psql:
```sql
\dt                              -- listar tabelas
SELECT COUNT(*) FROM conversations;
SELECT COUNT(*) FROM feedbacks;
\q                               -- sair
```

### Executar query direta (sem entrar no psql)
```powershell
wsl -d podman-machine-default -- podman exec postgres_db psql -U postgres -d mydb -c "SELECT * FROM conversations LIMIT 5;"
```

### Ver logs do PostgreSQL
```powershell
wsl -d podman-machine-default -- podman logs postgres_db
```

---

## 🔧 Configurar PgAdmin

1. Acesse http://localhost:5051
2. Login: `admin@admin.com` / `admin123`
3. Clique em **Add New Server**
4. Aba **General** → Name: `Local PostgreSQL`
5. Aba **Connection**:
   - Host: `postgres_db` (nome do container na network interna)
   - Port: `5432` (porta interna do container, não a 5450)
   - Database: `mydb`
   - Username: `postgres`
   - Password: `postgres123`
6. Clique em **Save**

---

## 🐍 Conectar via Python

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://postgres:postgres123@localhost:5450/mydb"
)

with engine.connect() as conn:
    result = conn.execute("SELECT COUNT(*) FROM conversations")
    print(result.scalar())
```

---

## 🔥 Troubleshooting

| Problema | Causa provável | Solução |
|----------|---------------|---------|
| Script não encontra `wsl` | WSL não instalado | Habilitar WSL2 no Windows |
| Container não sobe | Podman machine não iniciou | Abrir Podman Desktop e aguardar a VM iniciar |
| Porta 5450 ocupada | Outro processo usando a porta | Alterar a porta no script para `5451:5432` |
| `aardvark-dns failed` | DNS do Podman não funciona no WSL sem systemd | Normal — o script já usa `--disable-dns` para contornar |
| Tabelas não existem | init.sql não rodou | `.\podman_stop.ps1 -Clean` e então `.\podman_start.ps1` |
| PgAdmin não conecta ao banco | Host incorreto | Use `postgres_db` como host (não `localhost`) no PgAdmin |
| Containers não aparecem no Podman Desktop | Relay `win-sshproxy` inativo | Execute `.\podman_start.ps1` — o relay é ativado automaticamente |
| DBeaver não conecta | `localhost` resolve como IPv6 | Use `127.0.0.1` no campo Host do DBeaver (não `localhost`) |
| Ollama não encontrado | Ollama não instalado ou não iniciado | Instale em https://ollama.com e execute `ollama serve` |
| Modelo não disponível | Modelo não baixado | Execute `ollama pull llama3.2` |
| Tool calling não funciona | Modelo sem suporte a tools | Troque para `qwen2.5` ou `llama3.1` no `.env` |
| JSON inválido na resposta | Modelo retornou texto extra | Normal — o código já extrai JSON com regex como fallback |

---

## 🗄️ Equivalência de comandos Docker → Podman

| Docker (README original) | Podman equivalente |
|--------------------------|--------------------|
| `docker compose up -d` | `.\podman_start.ps1` |
| `docker compose down` | `.\podman_stop.ps1` |
| `docker compose down -v` | `.\podman_stop.ps1 -Clean` |
| `docker exec -it postgres_db psql ...` | `wsl -d podman-machine-default -- podman exec -it postgres_db psql ...` |
| `docker ps` | `wsl -d podman-machine-default -- podman ps` |
| `docker logs postgres_db` | `wsl -d podman-machine-default -- podman logs postgres_db` |

---

## 📚 Recursos

- [Podman Desktop](https://podman-desktop.io/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [PgAdmin Docs](https://www.pgadmin.org/docs/)


# 🗄️ Conectando ao PostgreSQL com DBeaver

Guia passo a passo para conectar o DBeaver ao banco `mydb` que está rodando via Podman.

---

## ✅ Status atual do ambiente

| Serviço    | Status | Endereço         |
|------------|--------|------------------|
| postgres_db | ✅ Up  | localhost:**5450** |
| pgadmin    | ✅ Up  | http://localhost:5050 |

**Banco:** `mydb` — 12 tabelas, dados carregados (62 conversas, 30 feedbacks)

---

## 📦 1. Instalar o DBeaver (se ainda não tiver)

Baixe a versão **Community** (gratuita):

👉 https://dbeaver.io/download/

No Windows, execute o instalador `.exe` normalmente. Não precisa de admin.

---

## 🔌 2. Criar a conexão no DBeaver

### Passo 1 — Abrir o assistente de nova conexão

Na barra de menu superior, clique em:

```
Database  →  New Database Connection
```

Ou use o atalho: `Ctrl + Shift + N` dentro do DBeaver

Alternativamente, clique no ícone de tomada com `+` na barra de ferramentas.

---

### Passo 2 — Selecionar PostgreSQL

Na janela que abrir, procure por **PostgreSQL** na lista ou barra de busca.

Clique em **PostgreSQL** e depois em **Next >**.

---

### Passo 3 — Preencher os dados de conexão

Na aba **Main**, preencha exatamente assim:

| Campo        | Valor         |
|--------------|---------------|
| **Host**     | `localhost`   |
| **Port**     | `5450`        |
| **Database** | `mydb`        |
| **Username** | `postgres`    |
| **Password** | `postgres123` |

> ⚠️ **Atenção à porta:** o padrão do PostgreSQL é 5432, mas aqui usamos **5450** para não conflitar com instalações locais.

---

### Passo 4 — Baixar o driver (só na primeira vez)

Na parte inferior da janela pode aparecer um aviso:

```
Driver files are missing. Download?
```

Clique em **Download** (ou **Edit Driver Settings → Download**). O DBeaver baixa o driver JDBC automaticamente.

---

### Passo 5 — Testar a conexão

Clique em **Test Connection**.

Se aparecer:

```
✅ Connected (PostgreSQL 16.x)
```

Está funcionando. Clique em **Finish** para salvar.

Se der erro, veja a seção de [Troubleshooting](#-troubleshooting) abaixo.

---

## 🗂️ 3. Explorando o banco no DBeaver

Após conectar, na aba **Database Navigator** (lateral esquerda) você verá:

```
localhost:5450/mydb
└── Databases
    └── mydb
        └── Schemas
            └── public
                └── Tables
                    ├── agent_configs
                    ├── agent_runs
                    ├── backlog
                    ├── conversations  ← principal
                    ├── feedbacks      ← principal
                    ├── internal_notes
                    ├── kb_chunks
                    ├── kb_documents
                    ├── knowledge_bases
                    ├── sensitive_items
                    ├── ticket_memory
                    └── tickets
```

**Para ver os dados de uma tabela:**

1. Expanda `Tables`
2. Clique duas vezes na tabela (ex: `conversations`)
3. Na aba **Data** você vê todas as linhas
4. Na aba **Properties** você vê a estrutura das colunas

---

## 📊 4. Executar queries SQL

### Abrir o editor SQL

- Clique com botão direito na conexão (ou no banco `mydb`)
- Selecione **SQL Editor → Open SQL Script**

Ou use: `Ctrl + ]`

---

### Queries úteis para explorar os dados

Cole e execute com `Ctrl + Enter` (executa a query onde está o cursor):

```sql
-- Ver todas as conversas
SELECT * FROM conversations LIMIT 10;

-- Contar tickets por status
SELECT ticket_status, COUNT(*) as total
FROM conversations
GROUP BY ticket_status
ORDER BY total DESC;

-- Ver feedbacks por canal
SELECT channel, COUNT(*) as total
FROM feedbacks
GROUP BY channel;

-- Execuções dos agentes
SELECT agent_name, COUNT(*) as execucoes
FROM agent_runs
GROUP BY agent_name;

-- Últimas 5 conversas abertas
SELECT ticket_id, speaker, message, timestamp
FROM conversations
WHERE ticket_status = 'open'
ORDER BY timestamp DESC
LIMIT 5;

-- Ver backlog por prioridade
SELECT prioridade, COUNT(*) as itens
FROM backlog
GROUP BY prioridade
ORDER BY itens DESC;
```

---

## 🔥 Troubleshooting

### Erro: "Connection refused" ou "Could not connect to server"

**Causa:** containers não estão rodando.

**Solução:** abra o PowerShell na pasta `modulo2_semana1` e execute:
```powershell
.\podman_start.ps1
```

---

### Erro: "FATAL: password authentication failed"

**Causa:** senha incorreta.

**Solução:** confirme que está usando exatamente `postgres123` (sem espaços).

---

### Erro: porta 5432 em vez de 5450

**Causa:** DBeaver preencheu a porta padrão automaticamente.

**Solução:** verifique que o campo **Port** está como `5450`, não `5432`.

---

### Driver não baixa (rede corporativa bloqueando)

**Causa:** o proxy da empresa bloqueia o download automático do driver JDBC.

**Solução:** baixe manualmente o driver PostgreSQL JDBC:

1. Acesse: https://jdbc.postgresql.org/download/
2. Baixe o arquivo `.jar` (ex: `postgresql-42.7.x.jar`)
3. No DBeaver: `Database → Driver Manager → PostgreSQL → Edit`
4. Na aba **Libraries**, clique em **Add File** e selecione o `.jar` baixado
5. Clique em **Find Class** e depois em **OK**

---

### DBeaver não aparece a aba "Data" ao clicar na tabela

**Solução:** clique duas vezes na tabela (não uma vez). Ou clique com botão direito → **View Data**.

---

## 📝 Referência rápida — dados de conexão

```
Host:     localhost
Port:     5450
Database: mydb
User:     postgres
Password: postgres123

Connection string:
postgresql://postgres:postgres123@localhost:5450/mydb
```

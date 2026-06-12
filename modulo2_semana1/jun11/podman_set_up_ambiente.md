# Setup do Ambiente (Podman)

> Versão adaptada para quem usa **Podman Desktop** no Windows com WSL.
> Se você usa Docker, consulte o arquivo `docker_set_up_ambiente.md`.

Antes de iniciar os exercícios, configure seu ambiente local seguindo os passos abaixo.

---

## 1. Atualizar o repositório

Abra um terminal na pasta do projeto e execute:

```bash
git pull
```

---

## 2. Iniciar o Podman Desktop

Abra o **Podman Desktop** e aguarde a VM `podman-machine-default` ficar com status **Running**.

> Se for a primeira vez, pode levar 1–2 minutos para a VM inicializar.

---

## 3. Subir o ambiente (PostgreSQL + PgAdmin)

Na pasta `modulo2_semana1`, execute o script de inicialização:

```powershell
.\podman_start.ps1
```

O script vai:
- Criar a network e os volumes automaticamente (se não existirem)
- Subir o container PostgreSQL na porta `5450`
- Subir o PgAdmin na porta `5051`
- Ativar o relay para que os containers apareçam no Podman Desktop

Mantenha o Podman Desktop aberto enquanto estiver usando o banco.

Para parar os containers ao terminar:

```powershell
.\podman_stop.ps1
```

---

## 4. Criar o arquivo `.env`

Se o projeto ainda não possuir um arquivo `.env`, rode o setup automático:

```powershell
.\setup.ps1 -SkipPodman
```

Ou crie manualmente o `.env` na raiz de `modulo2_semana1` com o conteúdo abaixo:

```env
# Banco de dados
DB_HOST=localhost

# Ollama (LLM local)
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2

# APIs de LLM (preencha conforme o exercício exigir)
OPENAI_API_KEY=sua-chave-aqui
GEMINI_API_KEY=sua-chave-aqui
ANTHROPIC_API_KEY=sua-chave-aqui
```

---

## 5. Instalar as dependências

Ative o ambiente virtual e instale os pacotes:

```powershell
# Ativar o venv
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt
```

Ou use o setup completo que faz tudo automaticamente:

```powershell
.\setup.ps1
```

---

## 6. Configurar o DBeaver

Crie uma nova conexão PostgreSQL com os seguintes parâmetros:

| Campo    | Valor       |
|----------|-------------|
| Host     | localhost   |
| Port     | 5450        |
| Database | mydb        |
| User     | postgres    |
| Password | postgres123 |

Após preencher os dados, clique em **Test Connection** para validar.

> Veja o arquivo `DBEAVER_CONEXAO.md` na raiz do módulo para instruções detalhadas com screenshots.

---

## 7. Executar o exercício

Com o venv ativo, navegue até a pasta do exercício e execute:

```bash
python <nome_do_arquivo>.py
```

Em alguns sistemas pode ser necessário usar `python3` em vez de `python`.

---

## Comandos úteis

| Ação | Comando |
|------|---------|
| Subir containers | `.\podman_start.ps1` |
| Parar containers (mantém dados) | `.\podman_stop.ps1` |
| Parar e remover tudo | `.\podman_stop.ps1 -Clean` |
| Verificar containers rodando | `wsl -d podman-machine-default -- podman ps` |
| Ver logs do PostgreSQL | `wsl -d podman-machine-default -- podman logs postgres_db` |
| Acessar o banco via CLI | `wsl -d podman-machine-default -- podman exec -it postgres_db psql -U postgres -d mydb` |

---

## Checklist

Antes de começar, confirme:

* [ ] Repositório atualizado (`git pull`)
* [ ] Podman Desktop aberto e VM `podman-machine-default` em **Running**
* [ ] Containers iniciados (`.\podman_start.ps1`)
* [ ] Arquivo `.env` criado e chaves de API preenchidas
* [ ] Ambiente virtual ativado (`.venv\Scripts\Activate.ps1`)
* [ ] Dependências instaladas (`pip install -r requirements.txt`)
* [ ] DBeaver conectado ao PostgreSQL (porta `5450`)
* [ ] Exercício executando sem erros

---

## Diferenças em relação ao Docker

| | Docker | Podman (Windows/WSL) |
|---|---|---|
| Comando para subir | `docker compose up` | `.\podman_start.ps1` |
| Comando para parar | `docker compose down -v` | `.\podman_stop.ps1 -Clean` |
| Porta PostgreSQL | `5450` | `5450` (mesma) |
| Porta PgAdmin | `5050` | `5051` |
| Daemon necessário | Sim (Docker Desktop) | Não (rootless) |
| Configuração extra | Nenhuma | Podman Desktop + WSL |

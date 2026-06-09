# =============================================================================
# setup.ps1 — Setup completo do ambiente modulo2_semana1
#
# O que este script faz:
#   1. Verifica pre-requisitos (Python, Podman/WSL)
#   2. Cria o arquivo .env se nao existir
#   3. Cria o ambiente virtual Python (.venv)
#   4. Instala todas as dependencias (requirements.txt)
#   5. Sobe os containers PostgreSQL + PgAdmin via Podman
#   6. Valida que o banco esta acessivel e com dados
#
# Uso:
#   .\setup.ps1              -> setup completo
#   .\setup.ps1 -SkipVenv    -> pula criacao do venv (ja existe)
#   .\setup.ps1 -SkipPodman  -> pula subida dos containers
#
# =============================================================================

param(
    [switch]$SkipVenv,
    [switch]$SkipPodman
)

$ROOT         = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VENV_DIR     = Join-Path $ROOT ".venv"
$REQ_FILE     = Join-Path $ROOT "requirements.txt"
$ENV_FILE     = Join-Path $ROOT ".env"
$WSL_DISTRO   = "podman-machine-default"

# Cores
function Write-Step([string]$msg)  { Write-Host "`n[$([char]0x25BA)] $msg" -ForegroundColor Cyan }
function Write-OK([string]$msg)    { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg)  { Write-Host "    [!]  $msg" -ForegroundColor Yellow }
function Write-Fail([string]$msg)  { Write-Host "    [X]  $msg" -ForegroundColor Red }

function Invoke-WSL([string]$cmd) {
    return (wsl -d $WSL_DISTRO -- bash -c $cmd 2>&1) -join "`n"
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  Setup - modulo2_semana1 (Podman + Python)  " -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta

# =============================================================================
# PASSO 1 — Verificar pre-requisitos
# =============================================================================
Write-Step "Verificando pre-requisitos..."

# Python
try {
    $pyVer = python --version 2>&1
    if ($pyVer -match "Python 3") {
        Write-OK "Python encontrado: $pyVer"
    } else {
        Write-Fail "Python 3 nao encontrado. Instale em https://python.org"
        exit 1
    }
} catch {
    Write-Fail "Python nao encontrado. Instale em https://python.org"
    exit 1
}

# WSL / Podman
if (-not $SkipPodman) {
    $wslCheck = wsl -d $WSL_DISTRO -- echo "ok" 2>&1
    if ($wslCheck -match "ok") {
        Write-OK "WSL com Podman encontrado ($WSL_DISTRO)"
    } else {
        Write-Warn "Distro '$WSL_DISTRO' nao encontrada ou nao iniciada."
        Write-Warn "Abra o Podman Desktop e aguarde a VM iniciar, ou instale em: https://podman-desktop.io/downloads/windows"
        Write-Warn "Os containers NAO serao subidos. Continuando com setup Python..."
        $SkipPodman = $true
    }
}

# =============================================================================
# PASSO 2 — Criar .env se nao existir
# =============================================================================
Write-Step "Verificando arquivo .env..."

if (-not (Test-Path $ENV_FILE) -or (Get-Item $ENV_FILE).Length -eq 0) {
    Write-Warn ".env nao encontrado ou vazio. Criando modelo..."

    $envTemplate = @"
# ================================================================
# Variaveis de ambiente - modulo2_semana1
# Preencha as chaves de API antes de rodar os exercicios
# ================================================================

# --- Banco de dados (ja configurado pelo setup.ps1) ---
DB_HOST=localhost

# --- APIs de LLM (preencha com suas chaves) ---
OPENAI_API_KEY=sua-chave-aqui
GEMINI_API_KEY=sua-chave-aqui
ANTHROPIC_API_KEY=sua-chave-aqui

# --- Outras APIs ---
EXA_API_KEY=sua-chave-aqui

# --- Langfuse (observabilidade - opcional) ---
LANGFUSE_PUBLIC_KEY=sua-chave-aqui
LANGFUSE_SECRET_KEY=sua-chave-aqui
LANGFUSE_BASE_URL=http://localhost:3008
"@

    Set-Content -Path $ENV_FILE -Value $envTemplate -Encoding UTF8
    Write-OK "Arquivo .env criado em: $ENV_FILE"
    Write-Warn "IMPORTANTE: edite o .env e adicione suas chaves de API antes de rodar os exercicios."
} else {
    Write-OK ".env ja existe e configurado."
}

# =============================================================================
# PASSO 3 — Criar e configurar ambiente virtual Python
# =============================================================================
if (-not $SkipVenv) {
    Write-Step "Configurando ambiente virtual Python..."

    if (Test-Path (Join-Path $VENV_DIR "Scripts\python.exe")) {
        Write-OK "Venv ja existe em: $VENV_DIR"
    } else {
        Write-Warn "Criando venv em: $VENV_DIR"
        python -m venv $VENV_DIR
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Erro ao criar venv. Verifique sua instalacao do Python."
            exit 1
        }
        Write-OK "Venv criado."
    }

    # Instalar dependencias
    $pip = Join-Path $VENV_DIR "Scripts\pip.exe"
    if (Test-Path $REQ_FILE) {
        Write-Warn "Instalando dependencias (pode demorar alguns minutos)..."
        & $pip install -r $REQ_FILE --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Fail "Erro ao instalar dependencias. Veja o erro acima."
            exit 1
        }
        Write-OK "Dependencias instaladas com sucesso."
    } else {
        Write-Warn "requirements.txt nao encontrado em $REQ_FILE"
        Write-Warn "Instale manualmente: pip install -r requirements.txt"
    }
} else {
    Write-Warn "[-SkipVenv] Criacao do venv ignorada."
}

# =============================================================================
# PASSO 4 — Subir containers via Podman
# =============================================================================
if (-not $SkipPodman) {
    Write-Step "Subindo containers PostgreSQL + PgAdmin via Podman..."

    $startScript = Join-Path $ROOT "podman_start.ps1"
    if (Test-Path $startScript) {
        & $startScript
    } else {
        Write-Warn "podman_start.ps1 nao encontrado. Subindo manualmente..."

        $NETWORK   = "modulo2_semana1_default"
        $INIT_WIN  = Join-Path $ROOT "init.sql"
        $INIT_WSL  = ($INIT_WIN -replace "\\", "/") -replace "^([A-Za-z]):", { "/mnt/" + $_.Groups[1].Value.ToLower() }

        # Network
        $nets = Invoke-WSL "podman network ls --format '{{.Name}}'"
        if ($nets -notmatch $NETWORK) {
            Invoke-WSL "podman network create --disable-dns $NETWORK" | Out-Null
        }

        # Postgres
        $containers = Invoke-WSL "podman ps -a --format '{{.Names}}'"
        if ($containers -notmatch "postgres_db") {
            $cmd = "podman run -d --name postgres_db --network $NETWORK " +
                   "-e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres123 " +
                   "-e POSTGRES_DB=mydb -e PGDATA=/var/lib/postgresql/data/pgdata " +
                   "-p 5450:5432 -v postgres_data:/var/lib/postgresql/data " +
                   "-v '${INIT_WSL}:/docker-entrypoint-initdb.d/init.sql:ro' " +
                   "docker.io/ankane/pgvector:latest"
            Invoke-WSL $cmd | Out-Null
        } else {
            Invoke-WSL "podman start postgres_db" | Out-Null
        }

        # PgAdmin
        if ($containers -notmatch "pgadmin") {
            $cmd2 = "podman run -d --name pgadmin --network $NETWORK " +
                    "-e PGADMIN_DEFAULT_EMAIL=admin@admin.com " +
                    "-e PGADMIN_DEFAULT_PASSWORD=admin123 " +
                    "-e PGADMIN_CONFIG_SERVER_MODE=False " +
                    "-p 5050:80 -v pgadmin_data:/var/lib/pgadmin " +
                    "docker.io/dpage/pgadmin4:latest"
            Invoke-WSL $cmd2 | Out-Null
        } else {
            Invoke-WSL "podman start pgadmin" | Out-Null
        }
    }
} else {
    Write-Warn "[-SkipPodman] Subida dos containers ignorada."
}

# =============================================================================
# PASSO 5 — Validar banco de dados
# =============================================================================
if (-not $SkipPodman) {
    Write-Step "Validando conexao com o banco de dados..."
    Start-Sleep -Seconds 4

    $tables = Invoke-WSL "podman exec postgres_db psql -U postgres -d mydb -c 'SELECT COUNT(*) FROM conversations;' 2>&1"
    if ($tables -match "\d+") {
        Write-OK "Banco acessivel e com dados."
    } else {
        Write-Warn "Banco pode ainda estar inicializando. Aguarde alguns segundos e tente novamente."
        Write-Warn "Verifique com: wsl -d podman-machine-default -- podman exec postgres_db psql -U postgres -d mydb -c 'SELECT COUNT(*) FROM conversations;'"
    }
}

# =============================================================================
# RESUMO FINAL
# =============================================================================
Write-Host ""
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host "  Setup concluido!                           " -ForegroundColor Magenta
Write-Host "=============================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "  Ambiente Python:" -ForegroundColor White
Write-Host "    Ativar venv  : .venv\Scripts\Activate.ps1" -ForegroundColor DarkGray
Write-Host "    Rodar script : python modulo2_semana1\jun8\exe1\support_agent_basic.py" -ForegroundColor DarkGray
Write-Host ""

if (-not $SkipPodman) {
    Write-Host "  Banco de dados:" -ForegroundColor White
    Write-Host "    PostgreSQL : localhost:5450  (postgres / postgres123 / mydb)" -ForegroundColor DarkGray
    Write-Host "    PgAdmin    : http://localhost:5050  (admin@admin.com / admin123)" -ForegroundColor DarkGray
    Write-Host "    DBeaver    : veja DBEAVER_CONEXAO.md para conectar" -ForegroundColor DarkGray
    Write-Host ""
}

if (Select-String -Path $ENV_FILE -Pattern "sua-chave-aqui" -Quiet 2>$null) {
    Write-Host "  ATENCAO: edite o arquivo .env e adicione suas chaves de API!" -ForegroundColor Yellow
    Write-Host "    Arquivo: $ENV_FILE" -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "  Para parar os containers : .\podman_stop.ps1" -ForegroundColor DarkGray
Write-Host "  Para subir novamente     : .\podman_start.ps1" -ForegroundColor DarkGray
Write-Host ""

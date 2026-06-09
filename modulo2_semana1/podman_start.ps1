# =============================================================================
# podman_start.ps1 — Sobe PostgreSQL + PgAdmin via Podman no Windows/WSL
#
# Uso: .\podman_start.ps1
# Requisitos: Podman Desktop instalado e WSL ativo (distro podman-machine-default)
# =============================================================================

$WSL_DISTRO  = "podman-machine-default"
$NETWORK     = "modulo2_semana1_default"
$PG_VOLUME   = "postgres_data"
$PGA_VOLUME  = "pgadmin_data"
$PG_NAME     = "postgres_db"
$PGA_NAME    = "pgadmin"

# Converte o path do init.sql para Linux/WSL
$SCRIPT_DIR   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$INIT_SQL_WIN = Join-Path $SCRIPT_DIR "init.sql"
$INIT_SQL_WSL = ($INIT_SQL_WIN -replace "\\", "/") -replace "^([A-Za-z]):", { "/mnt/" + $_.Groups[1].Value.ToLower() }

Write-Host ""
Write-Host "=== Podman Start - modulo2_semana1 ===" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------------------------------
# Helper: roda comando no WSL e retorna stdout como string
# --------------------------------------------------------------------------
function Invoke-WSL([string]$cmd) {
    return (wsl -d $WSL_DISTRO -- bash -c $cmd 2>&1) -join "`n"
}

# --------------------------------------------------------------------------
# 1. Checar se postgres já está rodando
# --------------------------------------------------------------------------
$running = Invoke-WSL "podman ps --format '{{.Names}}'"
if ($running -match $PG_NAME) {
    Write-Host "Containers ja estao rodando." -ForegroundColor Green
    Write-Host ""
    Write-Host "   PostgreSQL : localhost:5450  (postgres / postgres123 / mydb)"
    Write-Host "   PgAdmin    : http://localhost:5050  (admin@admin.com / admin123)"
    Write-Host ""
    exit 0
}

# --------------------------------------------------------------------------
# 2. Criar network (ignora erro se já existir)
# --------------------------------------------------------------------------
$netCheck = Invoke-WSL "podman network ls --format '{{.Name}}'"
if ($netCheck -match $NETWORK) {
    Write-Host "Network '$NETWORK' ja existe." -ForegroundColor DarkGray
} else {
    Write-Host "Criando network '$NETWORK'..." -ForegroundColor Yellow
    Invoke-WSL "podman network create --disable-dns $NETWORK" | Out-Null
}

# --------------------------------------------------------------------------
# 3. Subir PostgreSQL
# --------------------------------------------------------------------------
$allContainers = Invoke-WSL "podman ps -a --format '{{.Names}}'"

if ($allContainers -match $PG_NAME) {
    Write-Host "Iniciando container existente '$PG_NAME'..." -ForegroundColor Yellow
    Invoke-WSL "podman start $PG_NAME" | Out-Null
} else {
    Write-Host "Criando '$PG_NAME'..." -ForegroundColor Yellow
    $initSql = $INIT_SQL_WSL
    $pgCmd = "podman run -d --name $PG_NAME --network $NETWORK " +
             "-e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres123 " +
             "-e POSTGRES_DB=mydb -e PGDATA=/var/lib/postgresql/data/pgdata " +
             "-p 5450:5432 " +
             "-v ${PG_VOLUME}:/var/lib/postgresql/data " +
             "-v '${initSql}:/docker-entrypoint-initdb.d/init.sql:ro' " +
             "docker.io/ankane/pgvector:latest"
    Invoke-WSL $pgCmd | Out-Null
}

# --------------------------------------------------------------------------
# 4. Subir PgAdmin
# --------------------------------------------------------------------------
if ($allContainers -match $PGA_NAME) {
    Write-Host "Iniciando container existente '$PGA_NAME'..." -ForegroundColor Yellow
    Invoke-WSL "podman start $PGA_NAME" | Out-Null
} else {
    Write-Host "Criando '$PGA_NAME'..." -ForegroundColor Yellow
    $pgaCmd = "podman run -d --name $PGA_NAME --network $NETWORK " +
              "-e PGADMIN_DEFAULT_EMAIL=admin@admin.com " +
              "-e PGADMIN_DEFAULT_PASSWORD=admin123 " +
              "-e PGADMIN_CONFIG_SERVER_MODE=False " +
              "-p 5050:80 " +
              "-v ${PGA_VOLUME}:/var/lib/pgadmin " +
              "docker.io/dpage/pgadmin4:latest"
    Invoke-WSL $pgaCmd | Out-Null
}

# --------------------------------------------------------------------------
# 5. Aguardar e confirmar
# --------------------------------------------------------------------------
Write-Host "Aguardando containers iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$status = Invoke-WSL "podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
Write-Host ""
Write-Host $status
Write-Host ""
Write-Host "Pronto!" -ForegroundColor Green
Write-Host ""
Write-Host "   PostgreSQL : localhost:5450  (user: postgres / senha: postgres123 / db: mydb)"
Write-Host "   PgAdmin    : http://localhost:5050  (email: admin@admin.com / senha: admin123)"
Write-Host ""

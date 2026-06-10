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
$PGA_PORT    = 5051   # porta do host para o PgAdmin (5050 pode estar em uso pelo WSL relay)

# Converte o path do init.sql para Linux/WSL
$SCRIPT_DIR   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$INIT_SQL_WIN = Join-Path $SCRIPT_DIR "init.sql"
$INIT_SQL_WSL = ($INIT_SQL_WIN -replace "\\", "/") -replace "^([A-Za-z]):", { "/mnt/" + $_.Groups[1].Value.ToLower() }

# --------------------------------------------------------------------------
# Helper: garante que o win-sshproxy está ativo para o Podman Desktop enxergar
# os containers na aba "Running". Sem ele, o Desktop não consegue conectar
# ao socket do Podman via named pipe.
# --------------------------------------------------------------------------
function Start-PodmanDesktopRelay {
    $winSshProxy = "$env:LOCALAPPDATA\Programs\Podman\win-sshproxy.exe"
    $pipeName    = "podman-machine-default"
    $sshPort     = 49890
    $identity    = "$env:USERPROFILE\.local\share\containers\podman\machine\machine"
    $socket      = "/run/user/1000/podman/podman.sock"

    if (-not (Test-Path $winSshProxy)) {
        Write-Host "    [!]  win-sshproxy.exe nao encontrado — Podman Desktop pode nao mostrar status." -ForegroundColor Yellow
        return
    }

    # Verifica se o relay já está rodando para este pipe
    $existing = Get-Process -Name "win-sshproxy" -ErrorAction SilentlyContinue |
        Where-Object { (Get-WmiObject Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue).CommandLine -like "*$pipeName*" }

    if ($existing) {
        Write-Host "    [OK] Relay Podman Desktop (win-sshproxy) ja esta ativo." -ForegroundColor Green
        return
    }

    Write-Host "    Ativando relay para Podman Desktop..." -ForegroundColor Yellow
    Start-Process -FilePath $winSshProxy `
        -ArgumentList "127.0.0.1", $sshPort, $identity, "user", $socket, $pipeName `
        -WindowStyle Hidden `
        -ErrorAction SilentlyContinue

    Start-Sleep -Seconds 2

    $check = Get-Process -Name "win-sshproxy" -ErrorAction SilentlyContinue
    if ($check) {
        Write-Host "    [OK] Relay ativo — containers aparecerao como Running no Podman Desktop." -ForegroundColor Green
    } else {
        Write-Host "    [!]  Relay nao iniciou. Containers funcionam normalmente, mas podem nao aparecer no Desktop." -ForegroundColor Yellow
    }
}

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
    Start-PodmanDesktopRelay
    Write-Host ""
    Write-Host "   PostgreSQL : localhost:5450  (postgres / postgres123 / mydb)"
    Write-Host "   PgAdmin    : http://localhost:${PGA_PORT}  (admin@admin.com / admin123)"
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
              "-p ${PGA_PORT}:80 " +
              "-v ${PGA_VOLUME}:/var/lib/pgadmin " +
              "docker.io/dpage/pgadmin4:latest"
    Invoke-WSL $pgaCmd | Out-Null
}

# --------------------------------------------------------------------------
# 5. Ativar relay para Podman Desktop + Aguardar e confirmar
# --------------------------------------------------------------------------
Start-PodmanDesktopRelay

Write-Host "Aguardando containers iniciarem..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

$status = Invoke-WSL "podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
Write-Host ""
Write-Host $status
Write-Host ""
Write-Host "Pronto!" -ForegroundColor Green
Write-Host ""
Write-Host "   PostgreSQL : localhost:5450  (user: postgres / senha: postgres123 / db: mydb)"
Write-Host "   PgAdmin    : http://localhost:${PGA_PORT}  (email: admin@admin.com / senha: admin123)"
Write-Host ""

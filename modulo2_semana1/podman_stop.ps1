# =============================================================================
# podman_stop.ps1 — Para os containers PostgreSQL + PgAdmin
#
# Uso:
#   .\podman_stop.ps1          → Para containers (mantém dados)
#   .\podman_stop.ps1 -Clean   → Para e remove containers + volumes (apaga dados)
# =============================================================================

param(
    [switch]$Clean
)

$WSL_DISTRO = "podman-machine-default"
$PG_NAME    = "postgres_db"
$PGA_NAME   = "pgadmin"

Write-Host ""
Write-Host "=== Podman Stop — modulo2_semana1 ===" -ForegroundColor Cyan
Write-Host ""

if ($Clean) {
    Write-Host "⚠️  Modo CLEAN: vai remover containers e volumes (dados serão perdidos)." -ForegroundColor Red
    $confirm = Read-Host "Confirma? (s/n)"
    if ($confirm -ne "s") {
        Write-Host "Cancelado." -ForegroundColor Yellow
        exit 0
    }

    Write-Host "Removendo containers..." -ForegroundColor Yellow
    wsl -d $WSL_DISTRO -- bash -c "podman rm -f $PG_NAME $PGA_NAME 2>/dev/null; true" | Out-Null

    Write-Host "Removendo volumes..." -ForegroundColor Yellow
    wsl -d $WSL_DISTRO -- bash -c "podman volume rm postgres_data pgadmin_data 2>/dev/null; true" | Out-Null

    Write-Host "Removendo network..." -ForegroundColor Yellow
    wsl -d $WSL_DISTRO -- bash -c "podman network rm modulo2_semana1_default 2>/dev/null; true" | Out-Null

    Write-Host ""
    Write-Host "Tudo removido. Proximo start vai recriar do zero." -ForegroundColor Green
} else {
    Write-Host "Parando '$PGA_NAME'..." -ForegroundColor Yellow
    # Erros de limpeza de rede (netavark/aardvark) são esperados no WSL sem systemd — ignorados
    wsl -d $WSL_DISTRO -- bash -c "podman stop $PGA_NAME 2>/dev/null; true" | Out-Null

    Write-Host "Parando '$PG_NAME'..." -ForegroundColor Yellow
    wsl -d $WSL_DISTRO -- bash -c "podman stop $PG_NAME 2>/dev/null; true" | Out-Null

    Start-Sleep -Seconds 2
    Write-Host ""
    Write-Host "Containers parados. Dados preservados." -ForegroundColor Green
    Write-Host "Para reiniciar: .\podman_start.ps1" -ForegroundColor DarkGray
}
Write-Host ""

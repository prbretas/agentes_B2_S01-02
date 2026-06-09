# =============================================================================
# run_jun8.ps1 — Executa os exercicios de jun8 com Ollama
#
# Uso:
#   .\run_jun8.ps1          -> menu interativo
#   .\run_jun8.ps1 -Exe 1   -> roda exe1 diretamente
#   .\run_jun8.ps1 -Exe 2   -> roda exe2 diretamente
#   .\run_jun8.ps1 -Exe 3   -> roda exe3 diretamente
#   .\run_jun8.ps1 -All     -> roda os 3 em sequencia
# =============================================================================

param(
    [int]$Exe = 0,
    [switch]$All
)

$ROOT      = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VENV_PY   = Join-Path $ROOT ".venv\Scripts\python.exe"
$EXE1      = Join-Path $ROOT "jun8\exe1\support_agent_basic.py"
$EXE2      = Join-Path $ROOT "jun8\exe2\support_agent_toolcalling.py"
$EXE3      = Join-Path $ROOT "jun8\exe3\feedback_agent.py"
$ENV_FILE  = Join-Path $ROOT ".env"

# Cores
function Write-Step([string]$msg)  { Write-Host "`n[$([char]0x25BA)] $msg" -ForegroundColor Cyan }
function Write-OK([string]$msg)    { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn([string]$msg)  { Write-Host "    [!]  $msg" -ForegroundColor Yellow }
function Write-Fail([string]$msg)  { Write-Host "    [X]  $msg" -ForegroundColor Red }

# =============================================================================
# Verifica pre-requisitos
# =============================================================================
function Test-Prerequisites {
    # Python (venv)
    if (Test-Path $VENV_PY) {
        $pyVer = & $VENV_PY --version 2>&1
        Write-OK "Python (venv): $pyVer"
    } else {
        Write-Fail "Venv nao encontrado em $VENV_PY"
        Write-Warn "Execute primeiro: .\setup.ps1"
        return $false
    }

    # Ollama
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method GET -ErrorAction Stop
        $models = ($resp.models | ForEach-Object { $_.name }) -join ", "
        Write-OK "Ollama rodando. Modelos: $models"

        # Verifica se o modelo configurado no .env esta disponivel
        if (Test-Path $ENV_FILE) {
            $envContent = Get-Content $ENV_FILE -Raw
            if ($envContent -match 'OLLAMA_MODEL=(.+)') {
                $configuredModel = $Matches[1].Trim()
                $modelNames = $resp.models | ForEach-Object { $_.name -replace ':.*', '' }
                if ($modelNames -notcontains ($configuredModel -replace ':.*', '')) {
                    Write-Warn "Modelo '$configuredModel' nao encontrado localmente."
                    Write-Warn "Execute: ollama pull $configuredModel"
                    return $false
                } else {
                    Write-OK "Modelo '$configuredModel' disponivel."
                }
            }
        }
    } catch {
        Write-Fail "Ollama nao esta rodando em localhost:11434"
        Write-Warn "Inicie o Ollama com: ollama serve"
        Write-Warn "Ou abra o app Ollama no seu sistema."
        return $false
    }

    # Banco de dados (conexao rapida)
    try {
        $testScript = @"
import sys
sys.path.insert(0, r'$($ROOT -replace "\\", "\\")')
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
load_dotenv(r'$($ENV_FILE -replace "\\", "\\")')
host = os.getenv('DB_HOST', 'localhost')
engine = create_engine(f'postgresql+psycopg2://postgres:postgres123@{host}:5450/mydb', connect_args={'connect_timeout': 3})
with engine.connect() as c:
    r = c.execute(text('SELECT COUNT(*) FROM conversations')).scalar()
    print(f'OK:{r}')
"@
        $result = & $VENV_PY -c $testScript 2>&1
        if ($result -match "OK:(\d+)") {
            Write-OK "Banco de dados acessivel. Conversations: $($Matches[1])"
        } else {
            Write-Fail "Banco de dados nao acessivel."
            Write-Warn "Execute: .\podman_start.ps1"
            return $false
        }
    } catch {
        Write-Fail "Erro ao testar banco: $_"
        return $false
    }

    return $true
}

# =============================================================================
# Roda um exercicio
# =============================================================================
function Invoke-Exe([int]$num) {
    switch ($num) {
        1 {
            Write-Step "Exe1 — Agente Basico de Suporte (support_agent_basic.py)"
            Write-Host "   Analisa ticket via LLM Ollama: classifica, detecta followup e resume." -ForegroundColor DarkGray
            Write-Host ""

            # Pede o ticket_id para rodar
            $ticketInput = Read-Host "   Informe o ticket_id para analisar (Enter para usar 1001)"
            if (-not $ticketInput) { $ticketInput = "1001" }

            $runScript = @"
import sys
sys.path.insert(0, r'$((Join-Path $ROOT "jun8\exe1") -replace "\\", "\\")')
from support_agent_basic import SupportTicketAgentBasic
import json

agent = SupportTicketAgentBasic()
result = agent.run($ticketInput)
print(json.dumps(result, ensure_ascii=False, indent=2))
"@
            Write-Host ""
            & $VENV_PY -c $runScript
        }
        2 {
            Write-Step "Exe2 — Agente Tool Calling (support_agent_toolcalling.py)"
            Write-Host "   Agente orquestrado via Ollama com chamada de tools (banco + classificacao)." -ForegroundColor DarkGray
            Write-Host ""

            $ticketInput = Read-Host "   Informe o ticket_id para analisar (Enter para usar 1001)"
            if (-not $ticketInput) { $ticketInput = "1001" }

            Push-Location (Join-Path $ROOT "jun8\exe2")
            & $VENV_PY support_agent_toolcalling.py
            Pop-Location
        }
        3 {
            Write-Step "Exe3 — Analise de Feedbacks (feedback_agent.py)"
            Write-Host "   Le todos os feedbacks do banco, analisa com Ollama e gera relatorio." -ForegroundColor DarkGray
            Write-Host ""

            Push-Location (Join-Path $ROOT "jun8\exe3")
            & $VENV_PY feedback_agent.py
            Pop-Location
        }
        default {
            Write-Warn "Exercicio invalido: $num. Use 1, 2 ou 3."
        }
    }
}

# =============================================================================
# Menu interativo
# =============================================================================
function Show-Menu {
    Write-Host ""
    Write-Host "=============================================" -ForegroundColor Magenta
    Write-Host "   Exercicios jun8 — Ollama + PostgreSQL     " -ForegroundColor Magenta
    Write-Host "=============================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  [1] Exe1 — Agente basico de suporte" -ForegroundColor White
    Write-Host "      Classifica, detecta followup e resume ticket via Ollama" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [2] Exe2 — Agente com Tool Calling" -ForegroundColor White
    Write-Host "      Loop de tool calling: Ollama chama banco e classificador" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [3] Exe3 — Analise de feedbacks + relatorio" -ForegroundColor White
    Write-Host "      Processa todos os feedbacks e gera relatorio consolidado" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  [4] Rodar todos os exercicios em sequencia" -ForegroundColor White
    Write-Host ""
    Write-Host "  [0] Sair" -ForegroundColor DarkGray
    Write-Host ""
}

# =============================================================================
# MAIN
# =============================================================================

Write-Host ""
Write-Host "=== Verificando pre-requisitos ===" -ForegroundColor Cyan
$ok = Test-Prerequisites
if (-not $ok) {
    Write-Host ""
    Write-Fail "Pre-requisitos nao satisfeitos. Corrija os itens acima e tente novamente."
    exit 1
}

# Modo linha de comando
if ($All) {
    Write-Step "Rodando todos os exercicios em sequencia..."
    Invoke-Exe 1
    Invoke-Exe 2
    Invoke-Exe 3
    Write-Host ""
    Write-OK "Todos os exercicios concluidos."
    exit 0
}

if ($Exe -gt 0) {
    Invoke-Exe $Exe
    exit 0
}

# Menu interativo
while ($true) {
    Show-Menu
    $choice = Read-Host "Escolha"

    switch ($choice) {
        "1" { Invoke-Exe 1 }
        "2" { Invoke-Exe 2 }
        "3" { Invoke-Exe 3 }
        "4" {
            Invoke-Exe 1
            Invoke-Exe 2
            Invoke-Exe 3
            Write-OK "Todos os exercicios concluidos."
        }
        "0" {
            Write-Host "Ate logo!" -ForegroundColor Cyan
            exit 0
        }
        default {
            Write-Warn "Opcao invalida. Digite 1, 2, 3, 4 ou 0."
        }
    }
}

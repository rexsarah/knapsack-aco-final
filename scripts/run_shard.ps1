# scripts\run_shard.ps1
# Executa um shard de instâncias a partir de uma lista e compila o binário antes.

[CmdletBinding()]
param(
    [string]$ListFile = "config\sets\sanity_dificil_50.txt",
    [string]$Campaign = "seed12345",
    [int]$Repeats,
    [int]$Jobs
)

$ErrorActionPreference = "Stop"

function Write-Heading {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Text,
        [string]$Color = "Cyan"
    )
    Write-Host ""
    Write-Host "==> $Text" -ForegroundColor $Color
}

function Get-GxxPath {
    try {
        (Get-Command g++ -ErrorAction Stop).Source
    } catch {
        throw "g++ não foi encontrado no PATH. Instale MinGW-w64 (ou similar) e garanta que 'g++' esteja no PATH."
    }
}

function Invoke-Compilation {
    Write-Heading -Text "Compilando knapsack.exe"

    $gxx = Get-GxxPath
    $gxxArgs = @(
        "-std=c++17", "-O3",
        "-I", "include",
        "src\problem.cpp",
        "src\acs.cpp",
        "src\as.cpp",
        "src\asRank.cpp",
        "src\mmas.cpp",
        "src\main.cpp",
        "-o", "knapsack.exe"
    )

    Remove-Item .\knapsack.exe, .\test_knapsack.exe -ErrorAction SilentlyContinue

    & $gxx @gxxArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Falha na compilação (g++ retornou $LASTEXITCODE)."
    }

    Write-Host "OK: knapsack.exe gerado." -ForegroundColor Green
}

function Test-InstanceList {
    param([Parameter(Mandatory)][string]$Path)

    Write-Heading -Text "Validando lista: $Path"

    if (-not (Test-Path $Path)) {
        throw "Lista '$Path' não existe."
    }
    $lines = Get-Content $Path
    if ($null -eq $lines -or $lines.Count -eq 0) {
        throw "Lista '$Path' está vazia."
    }

    Write-Host ("Entradas: {0}" -f $lines.Count)
    Write-Host "Primeiras 5 linhas:" -ForegroundColor DarkGray
    $lines | Select-Object -First 5 | ForEach-Object { Write-Host "  $_" }
}

function Invoke-InstanceList {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Campaign,
        [int]$Repeats,
        [int]$Jobs
    )

    Write-Heading -Text "Executando binário sobre a lista" -Color "Yellow"

    # (1) Normaliza o caminho para barras /
    $PathFS = (Resolve-Path $Path).Path -replace '\\','/'

    # (2) Escreve a lista no local padrão esperado pelo binário
    $stdList = "config\sets\jooken_all.txt"
    New-Item -ItemType Directory -Force -Path (Split-Path $stdList) | Out-Null
    Copy-Item $Path $stdList -Force

    # (3) Argumentos (deixei --list também; mas a cópia acima garante funcionamento)
    $exeArgs = @(
        "--list=$PathFS",
        "--campaign=$Campaign"
    )
    if ($PSBoundParameters.ContainsKey('Repeats')) { $exeArgs += "--repeats=$Repeats" }
    if ($PSBoundParameters.ContainsKey('Jobs'))    { $exeArgs += "--jobs=$Jobs"       }

    Write-Host "Comando:" -ForegroundColor DarkGray
    Write-Host ("  .\knapsack.exe {0}" -f ($exeArgs -join ' ')) -ForegroundColor DarkGray

    & .\knapsack.exe @exeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Execução falhou (exit $LASTEXITCODE)."
    }

    Write-Host "Shard concluído." -ForegroundColor Green
}

try {
    Write-Heading -Text "Preparação do shard ($ListFile | $Campaign)"

    Test-InstanceList -Path $ListFile
    Invoke-Compilation
    Invoke-InstanceList -Path $ListFile -Campaign $Campaign -Repeats:$Repeats -Jobs:$Jobs

    Write-Heading -Text "Pronto! Verifique:"
    Write-Host "  - results\jooken\execucoes_jooken.csv"
    Write-Host "  - results\jooken\resumo_jooken.csv"
    Write-Host "  - results\jooken\execucoes_jooken_ALL.csv (após rebuild_all)"
    Write-Host "  - results\jooken\resumo_jooken_ALL.csv  (após rebuild_all)"
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}

# scripts/audit_runs.ps1  (v3 – compatível com Windows PowerShell 5.1)
# Auditoria do CSV de execuções (clássico ou difícil)

[CmdletBinding()]
param(
  [Parameter(Mandatory)]
  [string]$File,                                   # results\jooken\execucoes_jooken.csv  OU _ALL.csv
  [int]$ExpectedRepeats  = 20,
  [int]$ExpectedVariants = 4,
  [string]$OutDir        = "results\validation"
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Stop"

function Heading { param([string]$Text,[string]$Color="Cyan"); Write-Host ""; Write-Host "==> $Text" -ForegroundColor $Color }

# --- Checagens iniciais ---
Heading "Verificando arquivo de entrada"
if (-not (Test-Path $File)) { throw "Arquivo '$File' não encontrado." }
Write-Host "OK: $File"

# --- Carrega CSV (robusto para 1 linha) ---
Heading "Carregando CSV"
$rowsRaw = Import-Csv -Path $File
[array]$rows = $rowsRaw
$totalRows = ($rows | Measure-Object).Count
if ($totalRows -eq 0) { throw "CSV vazio." }

# --- Checa colunas mínimas ---
$first = $rows[0]
$need = @("instance","variant")
$have = $first.PSObject.Properties.Name
$missing = $need | Where-Object { $_ -notin $have }
if (($missing | Measure-Object).Count -gt 0) {
  throw "CSV sem colunas obrigatórias: $($missing -join ', ')"
}

# Normaliza chaves
$rows | ForEach-Object {
  $_.instance = ($_.instance).ToString().Trim()
  $_.variant  = ($_.variant ).ToString().Trim()
}

# --- Métricas gerais ---
Heading "Métricas gerais"
$uniquePairs = ( $rows | Select-Object instance,variant -Unique | Measure-Object ).Count
$uniqueInst  = ( $rows | Select-Object instance -Unique            | Measure-Object ).Count
$uniqueVars  = ( $rows | Select-Object variant  -Unique            | Measure-Object ).Count
Write-Host ("Linhas (execuções)........: {0}" -f $totalRows)
Write-Host ("Pares únicos (inst,var)...: {0}" -f $uniquePairs)
Write-Host ("Instâncias únicas.........: {0}" -f $uniqueInst)
Write-Host ("Variantes únicas..........: {0}" -f $uniqueVars)

# --- Repetições por (instance,variant) ---
Heading "Repetições por (instance, variant)"
$byPair = $rows |
  Group-Object instance, variant |
  Select-Object @{n="instance";e={$_.Group[0].instance}},
                @{n="variant"; e={$_.Group[0].variant }},
                @{n="repeats"; e={$_.Count}}
$badRepeats = $byPair | Where-Object { $_.repeats -ne $ExpectedRepeats } | Sort-Object instance,variant
$badRepeats = @($badRepeats)

# --- Cobertura de variantes por instância ---
Heading "Cobertura de variantes por instância"
$byInst = $rows |
  Group-Object instance |
  Select-Object @{n="instance";e={$_.Group[0].instance}},
                @{n="variants";e={( $_.Group | Select-Object variant -Unique | Measure-Object ).Count}},
                @{n="rows";    e={$_.Count}}
$badCoverage = $byInst | Where-Object { $_.variants -ne $ExpectedVariants } | Sort-Object instance
$badCoverage = @($badCoverage)

# --- Variantes ausentes (opcional) ---
$allVariants = @($rows | Select-Object -ExpandProperty variant -Unique | Sort-Object)
$missingDetail = @()
foreach ($g in ($rows | Group-Object instance)) {
  $inst = $g.Name
  $have = @($g.Group | Select-Object -ExpandProperty variant -Unique)
  $miss = Compare-Object -ReferenceObject $allVariants -DifferenceObject $have -PassThru
  if (($miss | Measure-Object).Count -gt 0) {
    $missingDetail += [pscustomobject]@{
      instance         = $inst
      missing_variants = (@($miss) -join "|")
    }
  }
}

# --- Saída ---
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$summaryPath = Join-Path $OutDir "audit_summary.txt"
$badRepPath  = Join-Path $OutDir "pairs_bad_repeats.csv"
$badCovPath  = Join-Path $OutDir "instances_bad_coverage.csv"
$missPath    = Join-Path $OutDir "instances_missing_variants.csv"

Heading "Gravando relatórios" "Yellow"
@"
Arquivo auditado: $File

-- Totais --
Linhas (execuções)........: $totalRows
Pares únicos (inst,var)...: $uniquePairs
Instâncias únicas.........: $uniqueInst
Variantes únicas..........: $uniqueVars

-- Parâmetros esperados --
ExpectedRepeats  = $ExpectedRepeats
ExpectedVariants = $ExpectedVariants

-- Problemas encontrados --
Pares com repeats != $ExpectedRepeats ..........: $(($badRepeats   | Measure-Object).Count)
Instâncias com variantes != $ExpectedVariants ..: $(($badCoverage  | Measure-Object).Count)
Instâncias com variantes ausentes (lista) ......: $(($missingDetail| Measure-Object).Count)

Saídas:
 - $badRepPath
 - $badCovPath
 - $missPath
"@ | Set-Content -Encoding UTF8 $summaryPath

# Export-Csv compatível com PowerShell 5.1 (sem -UseQuotes)
$badRepeats    | Export-Csv -Encoding UTF8 -NoTypeInformation -Path $badRepPath
$badCoverage   | Export-Csv -Encoding UTF8 -NoTypeInformation -Path $badCovPath
$missingDetail | Export-Csv -Encoding UTF8 -NoTypeInformation -Path $missPath

Write-Host "Resumo....: $summaryPath" -ForegroundColor Green
Write-Host "Repeats...: $badRepPath"   -ForegroundColor Green
Write-Host "Cobertura.: $badCovPath"   -ForegroundColor Green
Write-Host "Ausentes..: $missPath"     -ForegroundColor Green
Write-Host ""
Write-Host "Concluído." -ForegroundColor Green

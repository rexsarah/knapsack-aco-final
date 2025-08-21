<# 
  clean_everything.ps1
  Limpa resultados, relatórios, listas/sets, batches e binários.
  Use o parâmetro -PurgeData para também remover data\jooken\dificil (instâncias baixadas).

  Exemplos:
    powershell -ExecutionPolicy Bypass -File scripts\clean_everything.ps1
    powershell -ExecutionPolicy Bypass -File scripts\clean_everything.ps1 -PurgeData
#>

[CmdletBinding()]
param(
  [switch]$PurgeData
)

$ErrorActionPreference = "SilentlyContinue"

function Heading($t,$c="Cyan"){ Write-Host "`n==> $t" -ForegroundColor $c }

Heading "Limpando resultados e artefatos..."

# 1) Resultados e relatórios
Remove-Item "results\jooken\batches" -Recurse -Force
Remove-Item "results\jooken\execucoes*.csv" -Force
Remove-Item "results\jooken\resumo*.csv" -Force
Remove-Item "results\jooken\*_ALL.csv" -Force

Remove-Item "results\validation" -Recurse -Force
Remove-Item "results\excel\*.xlsx" -Force

# 2) Logs
Remove-Item "logs" -Recurse -Force

# 3) Listas/sets
Remove-Item "config\sets\classic_p01_p08.txt" -Force
Remove-Item "config\sets\jooken_dificil_all.txt" -Force
Remove-Item "config\sets\sanity_*.txt" -Force
Remove-Item "config\sets\*.txt" -Force  # segurança: apaga qualquer lista residual
New-Item -ItemType Directory -Force "config\sets" | Out-Null

# 4) Binários e objetos
Remove-Item ".\knapsack.exe" -Force
Remove-Item ".\test_knapsack.exe" -Force
Remove-Item ".\*.obj" -Force
Remove-Item ".\*.o"   -Force

# 5) (Opcional) também apaga os dados baixados das instâncias difíceis
if ($PurgeData) {
  Heading "Removendo dados baixados (data\jooken\dificil)..." "Yellow"
  Remove-Item "data\jooken\dificil" -Recurse -Force
}

Heading "Limpeza concluída." "Green"

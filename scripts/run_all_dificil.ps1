# Executa as instâncias difíceis do repositório de Jooken
# - Gera lista ASCII (sem BOM) a partir de data\jooken\dificil\**\test.in
# - Permite escolher quantidade para dry-run (top N)
# - Chama run_shard.ps1 com repeats/jobs
# - Opcional: consolida *_ALL.csv no final

[CmdletBinding()]
param(
  [int]$Repeats = 3,
  [int]$Jobs     = 4,
  [string]$Campaign = "seedHARD",
  [int]$TopN = 0,              # se >0, usa apenas as TopN instâncias para um dry-run
  [switch]$RebuildAllAfter
)

$ErrorActionPreference = "Stop"

function Heading($t,$c="Cyan"){ Write-Host "`n==> $t" -ForegroundColor $c }

# 1) Procurar test.in nas difíceis
Heading "Procurando instâncias difíceis (test.in)"
$root = "data\jooken\dificil"
if(-not (Test-Path $root)){ throw "Pasta não encontrada: $root (rode fetch/prepare antes)" }

$files = Get-ChildItem $root -Recurse -File -Filter "*.in" |
         Where-Object { $_.Name -like "test.in" } |
         Sort-Object FullName
if(-not $files){ throw "Nenhum test.in encontrado em $root" }

if($TopN -gt 0){
  $files = $files | Select-Object -First $TopN
  Write-Host "Dry-run: usando Top $TopN instâncias." -ForegroundColor DarkYellow
}
"Total na lista: $($files.Count)"

# 2) Salvar lista (ASCII)
New-Item -ItemType Directory -Force "config\sets" | Out-Null
$list = "config\sets\jooken_dificil_all.txt"
Heading "Salvando lista" "Yellow"
$files.FullName | Out-File $list -Encoding ascii
Write-Host "Lista: $list"

# 3) Rodar
Heading "Rodando difíceis (Repeats=$Repeats, Jobs=$Jobs, Campaign=$Campaign)"
powershell -ExecutionPolicy Bypass -File "scripts\run_shard.ps1" `
  -ListFile $list `
  -Campaign $Campaign `
  -Repeats $Repeats `
  -Jobs $Jobs

# 4) Dica de verificação
Heading "Concluído (difíceis)" "Green"
Write-Host "Verifique CSV em results\jooken\..."
Write-Host " - execucoes_jooken.csv"
Write-Host " - resumo_jooken.csv"
Write-Host "Rode 'python scripts\rebuild_all.py' para consolidar *_ALL.csv" -ForegroundColor DarkGray

if($RebuildAllAfter){
  Heading "Consolidando *_ALL.csv" "Yellow"
  python "scripts\rebuild_all.py"
}

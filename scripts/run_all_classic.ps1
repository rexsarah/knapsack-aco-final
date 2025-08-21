# Executa p01..p08 (instâncias "clássicas")
# - Gera lista ASCII (sem BOM)
# - Chama run_shard.ps1 com repeats/jobs configuráveis
# - Opcional: consolida *_ALL.csv no final

[CmdletBinding()]
param(
  [int]$Repeats = 20,
  [int]$Jobs     = 4,
  [string]$Campaign = "seedCLASSIC",
  [switch]$RebuildAllAfter   # se passado, roda python scripts/rebuild_all.py no fim
)

$ErrorActionPreference = "Stop"

function Heading($t,$c="Cyan"){ Write-Host "`n==> $t" -ForegroundColor $c }

# 1) Descobrir p01..p08
Heading "Descobrindo instâncias p01..p08"
$classic = Get-ChildItem -Path "data" -Recurse -File -Filter "p0*.txt" |
           Where-Object { $_.Name -match '^p0[1-8]\.txt$' } |
           Sort-Object Name
if(-not $classic){ throw "Nenhuma instância p01..p08 encontrada em .\data" }
"Encontradas: $($classic.Count)"
$classic.Name | ForEach-Object { "  $_" } | Write-Host

# 2) Salvar lista (ASCII)
New-Item -ItemType Directory -Force "config\sets" | Out-Null
$list = "config\sets\classic_p01_p08.txt"
Heading "Salvando lista" "Yellow"
$classic.FullName | Out-File $list -Encoding ascii
Write-Host "Lista: $list"

# 3) Rodar
Heading "Rodando p01..p08 (Repeats=$Repeats, Jobs=$Jobs, Campaign=$Campaign)"
powershell -ExecutionPolicy Bypass -File "scripts\run_shard.ps1" `
  -ListFile $list `
  -Campaign $Campaign `
  -Repeats $Repeats `
  -Jobs $Jobs

# 4) Dica de verificação
Heading "Concluído (p01..p08)" "Green"
Write-Host "Verifique os CSV em results\jooken\..."
Write-Host " - execucoes_jooken.csv"
Write-Host " - resumo_jooken.csv"
Write-Host "Rode 'python scripts\rebuild_all.py' para consolidar *_ALL.csv" -ForegroundColor DarkGray

if($RebuildAllAfter){
  Heading "Consolidando *_ALL.csv" "Yellow"
  python "scripts\rebuild_all.py"
}

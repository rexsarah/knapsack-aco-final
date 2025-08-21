# scripts/prepare_jooken.ps1
# Gera listas de instâncias Jooken difíceis a partir de data\jooken\dificil
# Mantém apenas arquivos "test.in" (formato de entrada), ignora logs/saídas.

$ErrorActionPreference = "Stop"

$root = Join-Path $PSScriptRoot "..\data\jooken\dificil" | Resolve-Path
$outDir = Join-Path $PSScriptRoot "..\config\sets"
$mestre = Join-Path $outDir "jooken_dificil_all.txt"
$sanity = Join-Path $outDir "sanity_dificil_50.txt"

Write-Host "Procurando instâncias em:" $root -ForegroundColor Cyan

# Apenas arquivos de instância: test.in
$inst = Get-ChildItem -Path $root -Recurse -File -ErrorAction Stop |
  Where-Object { $_.Name -ieq "test.in" } |
  Select-Object -ExpandProperty FullName

# Garante diretório de saída
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# Escreve arquivo mestre
$inst | Set-Content -Path $mestre -Encoding UTF8

# Subset para testes rápidos
$inst | Select-Object -First 50 | Set-Content -Path $sanity -Encoding UTF8

Write-Host "Arquivos de instância encontrados :" $inst.Count -ForegroundColor Green
Write-Host "Lista mestre salva em           :" $mestre
Write-Host "Lista de teste (50) salva em    :" $sanity

# Checagens rápidas
Write-Host "`n# Conferência" -ForegroundColor Yellow
"`nTotal no mestre:" | Write-Host
(Get-Content $mestre).Count
"`nPrimeiras 5 linhas do mestre:" | Write-Host
Get-Content $mestre -First 5

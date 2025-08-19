param(
  [string]$ListFile,                 # ex: config/sets/shards_all/shard_01.txt
  [string]$Campaign = "seed12345",   # nome da campanha (aparece nas pastas)
  [string]$Exe = ".\knapsack.exe"
)

if (!(Test-Path $Exe)) {
  Write-Host "Compilando..."
  g++ -std=c++17 -O3 -Iinclude src/*.cpp -o knapsack.exe
}

# pasta para guardar os CSVs deste shard
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outdir = "results\jooken\batches\$Campaign\$stamp"
New-Item -ItemType Directory -Force -Path $outdir | Out-Null

Write-Host "Rodando shard: $ListFile"
& $Exe --list $ListFile

if (!(Test-Path "results\jooken\execucoes_jooken.csv")) {
  Write-Error "CSV de execucoes nao encontrado. O programa rodou com erro?"
  exit 1
}

Copy-Item results\jooken\execucoes_jooken.csv "$outdir\execucoes.csv" -Force
Copy-Item results\jooken\resumo_jooken.csv    "$outdir\resumo.csv"    -Force

Write-Host "Shard concluido. Resultados em $outdir"

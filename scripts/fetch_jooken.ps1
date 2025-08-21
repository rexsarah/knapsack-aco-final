# Baixa instâncias difíceis do Jooken
$ErrorActionPreference = "Stop"

# pasta de destino
$dest = "data\jooken\dificil"
New-Item -ItemType Directory -Force $dest | Out-Null

# repositório remoto
$url = "https://github.com/JorikJooken/knapsackProblemInstances/archive/refs/heads/master.zip"
$tmp = "$env:TEMP\jooken.zip"

Write-Host "Baixando instâncias de $url ..."
Invoke-WebRequest -Uri $url -OutFile $tmp -UseBasicParsing

Write-Host "Extraindo para $dest ..."
Expand-Archive -Force $tmp $env:TEMP\jooken

# move somente problemInstances para dentro de data\jooken\dificil
Copy-Item "$env:TEMP\jooken\knapsackProblemInstances-master\problemInstances\*" $dest -Recurse -Force

Write-Host "Instâncias Jooken baixadas e organizadas em $dest"

# scripts\reset_results.ps1
# Zera todos os resultados e logs para iniciar as análises do zero.

[CmdletBinding()]
param()

Write-Host "==> Limpando resultados de execuções e resumos..." -ForegroundColor Cyan
Remove-Item "results\jooken\*.csv" -Force -ErrorAction SilentlyContinue
Remove-Item "results\jooken\batches" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "results\validation" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "logs" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "==> Resultados resetados com sucesso." -ForegroundColor Green
Write-Host "Agora você pode rodar novamente os testes na ordem correta!"

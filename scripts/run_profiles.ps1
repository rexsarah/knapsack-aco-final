# scripts\run_profiles.ps1
# Roda a mesma lista com diferentes campanhas (perfis).
# Se o binário aceitar flags de parâmetros (alpha, beta, rho, ants, iters, q0),
# descomente as linhas de -ParamsFlags abaixo.

[CmdletBinding()]
param(
  [string]$ListFile = "config\sets\jooken_dificil_all.txt",
  [int]$Repeats = 20,
  [int]$Jobs = 6
)

$profiles = @(
  @{ Tag="BALANCED"; Alpha=1; Beta=3; Rho=0.10; Ants=25; Iters=200; Q0=0.80 },
  @{ Tag="EXPLOIT";  Alpha=2; Beta=2; Rho=0.10; Ants=25; Iters=200; Q0=0.95 },
  @{ Tag="EXPLORE";  Alpha=1; Beta=5; Rho=0.30; Ants=25; Iters=200; Q0=0.60 },
  @{ Tag="MANY";     Alpha=1; Beta=3; Rho=0.10; Ants=50; Iters=150; Q0=0.80 },
  @{ Tag="FAST";     Alpha=1; Beta=3; Rho=0.20; Ants=10;  Iters=120; Q0=0.80 }
)

function Run-OneProfile {
  param(
    [string]$Tag,
    [string]$ListFile,
    [int]$Repeats,
    [int]$Jobs,
    [double]$Alpha,
    [double]$Beta,
    [double]$Rho,
    [int]$Ants,
    [int]$Iters,
    [double]$Q0
  )

  Write-Host ""
  Write-Host "==> Perfil $Tag | Repeats=$Repeats | Jobs=$Jobs" -ForegroundColor Cyan

  # Se o binário aceitar flags de parâmetros, monte-as aqui:
  # $ParamsFlags = @(
  #   "-alpha $Alpha", "-beta $Beta", "-rho $Rho",
  #   "-ants $Ants", "-iters $Iters", "-q0 $Q0"
  # ) -join ' '

  # Chama o wrapper padrão (compila e executa)
  powershell -ExecutionPolicy Bypass -File scripts\run_shard.ps1 `
    -ListFile $ListFile `
    -Campaign ("prof_"+$Tag) `
    -Repeats $Repeats `
    -Jobs $Jobs
    # Caso o binário aceite flags, passe-as (descomente e adapte no run_shard.ps1 para repassar):
    # -ExtraArgs $ParamsFlags
}

foreach ($p in $profiles) {
  Run-OneProfile @p -ListFile $ListFile -Repeats $Repeats -Jobs $Jobs
}

Write-Host ""
Write-Host "==> Consolidando tudo pós-perfis..." -ForegroundColor Yellow
python scripts\merge_any_results.py
python scripts\analyse_from_robust.py

Write-Host "`nFeito. Verifique results\analysis\classic_vs_difficult_summary.csv e coverage_from_robust.csv." -ForegroundColor Green

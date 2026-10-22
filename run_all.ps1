# Tek komutlu başlatıcı (Windows PowerShell). Kullanım:
#   .\run_all.ps1                 -> config.yaml'daki sırayla tüm aşamalar (scale: tam)
#   .\run_all.ps1 -Scale deneme   -> kısa deneme koşusu
#   .\run_all.ps1 -Stage ana      -> tek aşama;  -Stage veri,rapor  (tırnaksız da olur; dizi virgülle birleştirilir)
#   .\run_all.ps1 -NJobs 12       -> işçi sayısı (varsayılan config.yaml: 8)
# Kesilen koşu aynı komutla kaldığı yerden devam eder (out\checkpoints).
param(
  [string]$Scale = "",
  [string[]]$Stage = @(),
  [int]$NJobs = 0,
  [string]$EnvName = "cvdrev",
  [string]$Config = "config.yaml"
)
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# Uyku ve ekran kapanmasını koşu boyunca engelle
powercfg /change standby-timeout-ac 0 | Out-Null
powercfg /change hibernate-timeout-ac 0 | Out-Null
# Güç planı: yalnız Dengeli (381b4222-...) veya Güç tasarrufu (a1841308-...) etkinse Yüksek performansa yükseltilir;
# Nihai Performans ve Yüksek performans planlarına dokunulmaz.
try {
  $active = (powercfg /getactivescheme) -join " "
  if ($active -match "381b4222-f694-41f0-9685-ff5bb260df2e" -or $active -match "a1841308-3541-4fab-bc81-f71556f20b4a") {
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c 2>$null | Out-Null
  }
} catch {}

# Windows PowerShell 5.1'de "Stop" + 2>&1, yerel komutun ilk stderr satırında (ör. shap UserWarning) betiği durdurur;
# conda satırlarından önce "Continue"a geçilir. Hata kontrolü $LASTEXITCODE ile yapılır.
$ErrorActionPreference = "Continue"

# Conda ortamı yoksa oluştur
$envs = conda env list 2>$null
if (-not ($envs -match "^\s*$EnvName\s")) {
  Write-Host "[run_all] conda ortami olusturuluyor: $EnvName"
  conda env create -f environment.yml -n $EnvName
}

$args_ = @("run.py", "--config", $Config)
if ($Scale -ne "") { $args_ += @("--scale", $Scale) }
$StageStr = ($Stage -join ",")
if ($StageStr -ne "") { $args_ += @("--stage", $StageStr) }
if ($NJobs -gt 0) { $args_ += @("--n-jobs", $NJobs) }

$log = Join-Path $PSScriptRoot ("out\run_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".log")
New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot "out") | Out-Null
Write-Host "[run_all] conda run -n $EnvName python $($args_ -join ' ')  (kayit: $log)"
conda run -n $EnvName --no-capture-output python @args_ 2>&1 | Tee-Object -FilePath $log
if ($LASTEXITCODE -ne 0) { Write-Host "[run_all] HATA: cikis kodu $LASTEXITCODE; kayit: $log"; exit $LASTEXITCODE }
Write-Host "[run_all] tamamlandi."

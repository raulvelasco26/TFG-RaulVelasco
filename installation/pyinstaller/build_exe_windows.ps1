# =============================================================================
# build_exe_windows.ps1
# Genera el ejecutable Windows y lo empaqueta en un ZIP listo para distribuir.
# El usuario final NO necesita Python instalado.
#
# Uso (desde cualquier carpeta del proyecto, con el venv activado):
#   .\installation\pyinstaller\build_exe_windows.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$venvPy      = Join-Path $projectRoot "venv\Scripts\python.exe"
$venvPip     = Join-Path $projectRoot "venv\Scripts\pip.exe"
$specFile    = Join-Path $PSScriptRoot "pef_assistant.spec"
$distDir     = Join-Path $PSScriptRoot "dist"
$buildDir    = Join-Path $PSScriptRoot "build"
$outputDir   = Join-Path $distDir "PEF-AI-Assistant"
$zipName     = "PEF-AI-Assistant-Windows-exe.zip"
$zipPath     = Join-Path $PSScriptRoot $zipName

Write-Host ""
Write-Host "  PEF AI Assistant - Build ejecutable Windows"
Write-Host "  ============================================"
Write-Host ""

# 1. Activar venv del proyecto y verificar PyInstaller
Write-Host "  [1/4] Verificando entorno..."
if (-not (Test-Path $venvPy)) {
    Write-Host "  ERROR: No se encuentra el venv en $venvPy" -ForegroundColor Red
    Write-Host "         Crea el entorno primero: python -m venv venv && venv\Scripts\pip install -r requirements.txt"
    exit 1
}

$pyinstallerCheck = & $venvPy -m pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "        Instalando PyInstaller en el venv..."
    & $venvPip install pyinstaller | Out-Null
}

$piVersion = & $venvPy -m PyInstaller --version 2>&1
Write-Host "        PyInstaller $piVersion  |  venv OK"

# 2. Cerrar instancia anterior si está corriendo
$running = Get-Process -Name "PEF-AI-Assistant" -ErrorAction SilentlyContinue
if ($running) {
    Write-Host "        Cerrando instancia anterior del exe..."
    $running | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# 3. Limpiar builds anteriores
Write-Host "  [2/4] Limpiando builds anteriores..."
if (Test-Path $outputDir) { Remove-Item $outputDir -Recurse -Force }
if (Test-Path $buildDir)  { Remove-Item $buildDir  -Recurse -Force }
if (Test-Path $zipPath)   { Remove-Item $zipPath   -Force }

# 4. Compilar
Write-Host "  [3/4] Compilando (puede tardar 5-10 minutos la primera vez)..."
Set-Location $projectRoot
# PyInstaller escribe mensajes INFO en stderr; desactivamos Stop temporalmente
# para que PowerShell no los confunda con errores reales.
$ErrorActionPreference = "Continue"
& $venvPy -m PyInstaller $specFile --distpath $distDir --workpath $buildDir --noconfirm
$buildExitCode = $LASTEXITCODE
$ErrorActionPreference = "Stop"

if ($buildExitCode -ne 0 -or -not (Test-Path (Join-Path $outputDir "PEF-AI-Assistant.exe"))) {
    Write-Host "  ERROR: No se genero el ejecutable. Revisa los logs arriba." -ForegroundColor Red
    exit 1
}

# 5. Empaquetar en ZIP
Write-Host "  [4/4] Generando ZIP..."
Compress-Archive -Path "$outputDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 0)
Write-Host ""
Write-Host "  Listo: $zipName  ($sizeMB MB)" -ForegroundColor Green
Write-Host ""
Write-Host "  El usuario solo necesita:"
Write-Host "    1. Descomprimir el ZIP"
Write-Host "    2. Doble clic en PEF-AI-Assistant.exe"
Write-Host "    3. Sin instalar Python ni nada mas"
Write-Host ""

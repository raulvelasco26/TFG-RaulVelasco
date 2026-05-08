# =============================================================================
# crear_distribucion.ps1
# Genera el ZIP listo para distribuir al usuario final.
# Uso: ejecutar desde PowerShell estando en cualquier carpeta del proyecto.
#   .\installation\crear_distribucion.ps1
# =============================================================================

$ErrorActionPreference = "Stop"

# Rutas
$projectRoot = Split-Path $PSScriptRoot -Parent
$version     = "v1.0"
$zipName     = "PEF-AI-Assistant-$version.zip"
$zipPath     = Join-Path $projectRoot $zipName

# Carpetas y archivos que van en el ZIP
$include = @(
    "src",
    "templates",
    "resources",
    ".streamlit",
    "installation",
    "requirements.txt",
    "pyproject.toml",
    ".env.example",
    "README.md",
    "INSTALAR.bat"
)

# Patrones a excluir dentro de las carpetas copiadas
$excludePatterns = @(
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".pytest_cache",
    "*.egg-info"
)

Write-Host ""
Write-Host "  PEF AI Assistant - Generador de distribucion"
Write-Host "  ============================================="
Write-Host ""

# Comprobar que los archivos clave existen
foreach ($item in @("src", "requirements.txt", "INSTALAR.bat", "installation\setup.bat", "installation\launch.vbs")) {
    $fullPath = Join-Path $projectRoot $item
    if (-not (Test-Path $fullPath)) {
        Write-Host "  ERROR: No se encuentra '$item'" -ForegroundColor Red
        exit 1
    }
}

# Crear carpeta temporal
$tempDir = Join-Path $env:TEMP "pef_dist_$(Get-Random)"
New-Item -ItemType Directory -Path $tempDir | Out-Null
Write-Host "  [1/3] Copiando archivos..."

foreach ($item in $include) {
    $src = Join-Path $projectRoot $item
    $dst = Join-Path $tempDir $item
    if (Test-Path $src) {
        Copy-Item $src $dst -Recurse -Force
    }
}

# Eliminar archivos innecesarios de la copia
Write-Host "  [2/3] Limpiando archivos de desarrollo..."
foreach ($pattern in $excludePatterns) {
    Get-ChildItem $tempDir -Recurse -Include $pattern -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}

# Eliminar el propio script del ZIP (no es para el usuario final)
$scriptInZip = Join-Path $tempDir "installation\crear_distribucion.ps1"
if (Test-Path $scriptInZip) { Remove-Item $scriptInZip -Force }

# Crear ZIP
Write-Host "  [3/3] Generando ZIP..."
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

# Limpiar temp
Remove-Item $tempDir -Recurse -Force

# Resultado
$sizeMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
Write-Host ""
Write-Host "  Listo: $zipName  ($sizeMB MB)" -ForegroundColor Green
Write-Host ""
Write-Host "  Contenido del ZIP:"
Write-Host "    INSTALAR.bat         <- el usuario hace doble clic aqui"
Write-Host "    installation\"
Write-Host "      setup.bat          <- instalador (llamado por INSTALAR.bat)"
Write-Host "      launch.vbs         <- lanzador (acceso directo del escritorio)"
Write-Host "      INSTRUCCIONES.txt"
Write-Host "    src\  templates\  resources\  requirements.txt ..."
Write-Host ""

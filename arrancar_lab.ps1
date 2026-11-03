# arrancar_lab.ps1 — corre el lab R_LAB_HabeasData de punta a punta
# Uso:  .\arrancar_lab.ps1            (modo fixture, por defecto: sin secretos ni red)
#       .\arrancar_lab.ps1 -Modo real (contra la API de QA de CISA; ver docs/CREDENCIALES.md)
param(
    [ValidateSet("fixture", "real")]
    [string]$Modo = "fixture",
    [switch]$SoloVerificar
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $raiz
Write-Host "== Lab R_LAB_HabeasData — modo: $Modo ==" -ForegroundColor Cyan

# 1. Prerequisitos
function Comprobar($nombre, $comando) {
    if (Get-Command $comando -ErrorAction SilentlyContinue) {
        Write-Host "  [ok] $nombre" -ForegroundColor Green
    } else {
        Write-Host "  [FALTA] $nombre (comando '$comando' no encontrado)" -ForegroundColor Red
        exit 1
    }
}
Write-Host "`n-- Prerequisitos --"
Comprobar "Python" "python"
Comprobar "Node"   "node"

if ($Modo -eq "real") {
    Write-Host "  [..] Comprobando credencial R_LAB_HabeasData/Zeus/QA en el Administrador de credenciales"
    $cred = cmdkey /list 2>$null | Select-String "R_LAB_HabeasData/Zeus/QA"
    if (-not $cred) {
        Write-Host "  [FALTA] la credencial no existe. Ver docs/CREDENCIALES.md — el lab no hace llamadas sin ella." -ForegroundColor Red
        exit 1
    }
    Write-Host "  [ok] credencial presente" -ForegroundColor Green
    if (-not $env:ZEUS_REAL_AUTORIZADO) {
        Write-Host "  [AVISO] ZEUS_REAL_AUTORIZADO no está declarado: falta la autorización de uso de QA (ver docs/CREDENCIALES.md)" -ForegroundColor Yellow
    }
}

if ($SoloVerificar) { Write-Host "`nSolo verificación: todo listo." -ForegroundColor Cyan; exit 0 }

# 2. Tests unitarios (toda la suite: EP-001, EP-002 y EP-003)
Write-Host "`n-- Tests --"
python -m unittest discover -s tests -t . 2>&1 | Select-Object -Last 5
if ($LASTEXITCODE -ne 0) { Write-Host "  [FALLO] tests en rojo" -ForegroundColor Red; exit 1 }

# 3. Banco determinista: dos corridas para probar determinismo
Write-Host "`n-- Banco determinista (2 corridas) --"
foreach ($epica in "EP-001", "EP-002", "EP-003") {
    python banco/correr_matriz.py $epica --corridas 2
    if ($LASTEXITCODE -ne 0) { Write-Host "  [FALLO] matriz del banco $epica" -ForegroundColor Red; exit 1 }
}

# 4. Dónde queda la evidencia
Write-Host "`n-- Resultado --" -ForegroundColor Cyan
Write-Host "  Evidencia:   banco/evidencia/EP-00N/EVIDENCIA.md (N = 1, 2, 3)"
Write-Host "  Resultados:  banco/resultados/EP-00N_corrida1.json y _corrida2.json"
Write-Host "  Repositorio: studio/R_LAB_HabeasData/robot.db (robot de Studio) y Documentos/repositorio/lab.sqlite (se crea al correr)"
Write-Host "  Logs:        Logs/Auditoria y Logs/Sistema (carpeta AAAA/MM del día)"
Write-Host "  Reporte:     Reportes/AAAA/MM/"
Write-Host "  Flujo:       abrir el proyecto R_LAB_HabeasData en Rocketbot Studio"
Write-Host "`nLab corrido en modo $Modo." -ForegroundColor Green

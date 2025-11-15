<#
backup.ps1

Script PowerShell para localizar `pg_dump.exe` y crear un backup de PostgreSQL.

Uso (desde la carpeta del repo):
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\backup.ps1 -Host localhost -Port 5432 -User postgres -Password root -Database corteLazer -Output "backup\corteLazer.backup"

El script intentará localizar `pg_dump` en PATH y en las rutas comunes de instalación de PostgreSQL.
Si no lo encuentra, mostrará instrucciones para instalar PostgreSQL o indicar la ruta manual.
#>

Param(
    [string]$HostName = 'localhost',
    [int]$Port = 5432,
    [string]$User = 'postgres',
    [string]$Password = 'root',
    [string]$Database = 'corteLazer',
    [string]$Output = "$PSScriptRoot\backup\corteLazer.backup"
)

function Find-PgDump {
    # Primero ver si está en PATH
    $cmd = Get-Command pg_dump -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # Buscar en rutas típicas de instalación
    $results = @()
    $possibleRoots = @(
        "$env:ProgramFiles\PostgreSQL",
        "$env:ProgramFiles(x86)\PostgreSQL"
    ) | Where-Object { Test-Path $_ }

    foreach ($root in $possibleRoots) {
        $items = Get-ChildItem -Path $root -Filter pg_dump.exe -Recurse -ErrorAction SilentlyContinue
        foreach ($it in $items) { $results += $it.FullName }
    }

    if ($results.Count -gt 0) { return $results[0] }

    # Intentar where.exe (toma la primera línea de salida)
    try {
        $where = & where pg_dump 2>$null
        if ($where) {
            $first = $where -split "\r?\n" | Where-Object { $_ -ne '' } | Select-Object -First 1
            if ($first) { return $first.Trim() }
        }
    } catch { }

    return $null
}

Write-Host "Buscando pg_dump..."
$pgDump = Find-PgDump
if (-not $pgDump) {
    Write-Host "No se encontró 'pg_dump' en PATH ni en rutas típicas." -ForegroundColor Yellow
    Write-Host "Opciones:" -ForegroundColor Cyan
    Write-Host "  1) Instala PostgreSQL (incluye pg_dump): https://www.postgresql.org/download/windows/" -ForegroundColor Gray
    Write-Host "  2) Indica la ruta completa a pg_dump.exe y vuelve a ejecutar el script:" -ForegroundColor Gray
    Write-Host "     .\backup.ps1 -HostName $HostName -Port $Port -User $User -Password <pwd> -Database $Database -Output \"$Output\" -pgDumpPath 'C:\\Program Files\\PostgreSQL\\14\\bin\\pg_dump.exe'" -ForegroundColor Gray
    exit 1
}

Write-Host "pg_dump encontrado en: $pgDump" -ForegroundColor Green

# Asegurar que carpeta de salida existe
$outDir = Split-Path -Path $Output -Parent
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }

# Ejecutar pg_dump con variable de entorno temporal PGPASSWORD
$origPwd = $env:PGPASSWORD
$env:PGPASSWORD = $Password

$args = @(
    '-h', $HostName,
    '-p', $Port.ToString(),
    '-U', $User,
    '-F','c',
    '-b',
    '-v',
    '-f', $Output,
    $Database
)

Write-Host "Ejecutando pg_dump para la base '$Database' -> $Output (host: $HostName)"
& "$pgDump" @args
$exitCode = $LASTEXITCODE

# Restaurar PGPASSWORD anterior
if ($null -ne $origPwd) { $env:PGPASSWORD = $origPwd } else { Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue }

if ($exitCode -eq 0) {
    Write-Host "Backup completado correctamente: $Output" -ForegroundColor Green
} else {
    Write-Host "pg_dump finalizó con código de salida $exitCode" -ForegroundColor Red
}

exit $exitCode

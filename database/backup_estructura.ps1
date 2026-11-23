param(
    [string]$HostName = "localhost",
    [int]$Port = 3306,
    [string]$User = "root",
    [string]$Database = "ahp_veterinaria",
    [string]$OutputDirectory = "..\backups",
    [string]$MysqlDumpPath = ""
)

$ErrorActionPreference = "Stop"
$dumpExe = $null
if ($MysqlDumpPath) {
    if (-not (Test-Path -LiteralPath $MysqlDumpPath -PathType Leaf)) { throw "No existe MysqlDumpPath." }
    $dumpExe = (Resolve-Path -LiteralPath $MysqlDumpPath).Path
} else {
    foreach ($candidate in @("C:\xampp\mysql\bin\mysqldump.exe", "C:\Program Files\MySQL\MySQL Server 9.7\bin\mysqldump.exe")) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { $dumpExe = $candidate; break }
    }
    if (-not $dumpExe) { $dump = Get-Command mysqldump -ErrorAction SilentlyContinue; if ($dump) { $dumpExe = $dump.Source } }
    if (-not $dumpExe) { throw "No encuentro mysqldump. Indica -MysqlDumpPath." }
}
$directory = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $OutputDirectory))
New-Item -ItemType Directory -Path $directory -Force | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$output = Join-Path $directory "${Database}_estructura_${stamp}.sql"
if (Test-Path -LiteralPath $output) { throw "El destino ya existe; no se sobrescribió." }
$partial = "$output.partial"
if (Test-Path -LiteralPath $partial) { throw "El archivo parcial ya existe; no se sobrescribió." }
& $dumpExe --host=$HostName --port=$Port --user=$User --password --protocol=TCP --no-data --triggers --routines --events --single-transaction --skip-add-drop-table --result-file=$partial $Database
if ($LASTEXITCODE -ne 0) { throw "mysqldump falló con código $LASTEXITCODE; se conservó el archivo parcial para revisión." }
Move-Item -LiteralPath $partial -Destination $output
Write-Output "Backup de estructura creado: $output"

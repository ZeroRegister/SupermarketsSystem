$ErrorActionPreference = 'Stop'

$composeFile = Join-Path $PSScriptRoot '..\docker-compose.release.yml'
$envFile = Join-Path $PSScriptRoot '..\.env.release'

if (-not (Test-Path $envFile)) {
  Copy-Item (Join-Path $PSScriptRoot '..\.env.release.example') $envFile
  throw "Created .env.release. Edit it with your GHCR image prefix and passwords, then run this script again."
}

function Pull-Stack {
  & docker compose --env-file $envFile -f $composeFile pull
  if ($LASTEXITCODE -ne 0) { return $false }
  return $true
}

Write-Host 'Pulling application and database images from GHCR...'
if (-not (Pull-Stack)) {
  Write-Warning 'GHCR pull failed. Falling back to the official Docker Hub MySQL and Redis images.'
  $env:SHELFWISE_MYSQL_IMAGE = 'mysql:8.4.8'
  $env:SHELFWISE_REDIS_IMAGE = 'redis:7.4.9-alpine'
  if (-not (Pull-Stack)) {
    throw 'Image pull failed from both GHCR and Docker Hub.'
  }
}

& docker compose --env-file $envFile -f $composeFile up -d --wait
if ($LASTEXITCODE -ne 0) { throw 'The Shelfwise containers did not become healthy.' }
Write-Host 'Shelfwise is running at http://localhost:5173'

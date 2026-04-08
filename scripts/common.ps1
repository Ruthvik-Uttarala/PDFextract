Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RepoRoot {
  return (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

function Initialize-DockerConfig {
  $repoRoot = Get-RepoRoot
  $dockerConfig = Join-Path $repoRoot ".docker-config"
  New-Item -ItemType Directory -Force -Path $dockerConfig | Out-Null
  $env:DOCKER_CONFIG = $dockerConfig
}

function Assert-DockerCli {
  $null = Get-Command docker -ErrorAction Stop
}

function Assert-DockerDaemon {
  Initialize-DockerConfig
  Assert-DockerCli
  docker info --format '{{.ServerVersion}}' | Out-Null
}

function Test-TcpPort {
  param(
    [Parameter(Mandatory = $true)]
    [string]$HostName,
    [Parameter(Mandatory = $true)]
    [int]$Port
  )

  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $async = $client.BeginConnect($HostName, $Port, $null, $null)
    $wait = $async.AsyncWaitHandle.WaitOne(1000, $false)
    if (-not $wait) {
      return $false
    }
    $client.EndConnect($async) | Out-Null
    return $true
  } catch {
    return $false
  } finally {
    $client.Dispose()
  }
}

function Wait-Until {
  param(
    [Parameter(Mandatory = $true)]
    [scriptblock]$Condition,
    [Parameter(Mandatory = $true)]
    [string]$Description,
    [int]$TimeoutSeconds = 60
  )

  $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    if (& $Condition) {
      Write-Output "READY $Description"
      return
    }
    Start-Sleep -Seconds 2
  }
  throw "Timed out waiting for $Description"
}

. "$PSScriptRoot\\common.ps1"

Assert-DockerDaemon
$repoRoot = Get-RepoRoot
docker compose -f "$repoRoot\\docker-compose.yml" down --remove-orphans

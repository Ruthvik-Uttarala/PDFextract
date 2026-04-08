. "$PSScriptRoot\\common.ps1"

Assert-DockerDaemon
$repoRoot = Get-RepoRoot
docker compose -f "$repoRoot\\docker-compose.yml" up -d postgres minio kafka

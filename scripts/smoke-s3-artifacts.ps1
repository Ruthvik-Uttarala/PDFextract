. "$PSScriptRoot\\common.ps1"

param(
  [string]$UserId = "smoke-user",
  [string]$JobId = "",
  [switch]$Cleanup
)

$repoRoot = Get-RepoRoot
if (-not $JobId) {
  $JobId = "smoke-$((Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmss'))"
}

Push-Location "$repoRoot\\backend"
try {
  $args = @("-m", "app.cli", "smoke-s3-artifacts", "--user-id", $UserId, "--job-id", $JobId)
  if ($Cleanup) {
    $args += "--cleanup"
  }
  python @args
} finally {
  Pop-Location
}

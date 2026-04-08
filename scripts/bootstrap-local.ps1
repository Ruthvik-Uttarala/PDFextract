. "$PSScriptRoot\\common.ps1"

& "$PSScriptRoot\\start-local-infra.ps1"
& "$PSScriptRoot\\wait-local-infra.ps1"
& "$PSScriptRoot\\run-backend-checks.ps1"
& "$PSScriptRoot\\run-frontend-checks.ps1"

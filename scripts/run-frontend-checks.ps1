. "$PSScriptRoot\\common.ps1"

Assert-DockerDaemon
$repoRoot = Get-RepoRoot
$mount = "${repoRoot}:/repo"

$frontendCommand = "npm install && npm run typecheck && npm run lint && npm run test && npm run build"

docker run --rm `
  -v $mount `
  -w /repo/frontend `
  -e CI=true `
  -e NEXT_PUBLIC_FIREBASE_API_KEY=dummy-api-key `
  -e NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=pdfextract-local.firebaseapp.com `
  -e NEXT_PUBLIC_FIREBASE_PROJECT_ID=pdfextract-local `
  -e NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=pdfextract-local.appspot.com `
  -e NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=000000000000 `
  -e NEXT_PUBLIC_FIREBASE_APP_ID=1:000000000000:web:local `
  node:22.11.0 sh -lc $frontendCommand

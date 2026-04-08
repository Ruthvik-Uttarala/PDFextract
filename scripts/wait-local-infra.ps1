. "$PSScriptRoot\\common.ps1"

Assert-DockerDaemon

Wait-Until -Description "PostgreSQL on localhost:54329" -Condition { Test-TcpPort -HostName "127.0.0.1" -Port 54329 } -TimeoutSeconds 90
Wait-Until -Description "MinIO API on localhost:9000" -Condition {
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:9000/minio/health/live" -UseBasicParsing -TimeoutSec 3
    return $response.StatusCode -eq 200
  } catch {
    return $false
  }
} -TimeoutSeconds 90
Wait-Until -Description "Kafka on localhost:9092" -Condition { Test-TcpPort -HostName "127.0.0.1" -Port 9092 } -TimeoutSeconds 120

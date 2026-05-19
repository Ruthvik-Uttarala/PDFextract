param(
  [string]$Region = "us-east-2",
  [string]$BucketName = "pdfextract-artifacts-814117164451-us-east-2",
  [string]$DashboardName = "PDFextract-Storage",
  [switch]$CreateS3ErrorAlarms
)

$ErrorActionPreference = "Stop"

$dashboard = @{
  widgets = @(
    @{
      type = "metric"
      width = 12
      height = 6
      properties = @{
        title = "S3 Number Of Objects (AllStorageTypes)"
        region = $Region
        stat = "Average"
        period = 86400
        metrics = @(
          @("AWS/S3", "NumberOfObjects", "BucketName", $BucketName, "StorageType", "AllStorageTypes")
        )
      }
    },
    @{
      type = "metric"
      width = 12
      height = 6
      properties = @{
        title = "S3 Bucket Size Bytes (StandardStorage)"
        region = $Region
        stat = "Average"
        period = 86400
        metrics = @(
          @("AWS/S3", "BucketSizeBytes", "BucketName", $BucketName, "StorageType", "StandardStorage")
        )
      }
    }
  )
}

$dashboardJson = $dashboard | ConvertTo-Json -Depth 8 -Compress
aws cloudwatch put-dashboard --dashboard-name $DashboardName --dashboard-body $dashboardJson --region $Region
Write-Output "Dashboard updated: $DashboardName"

if ($CreateS3ErrorAlarms) {
  Write-Output "Creating S3 4xx/5xx alarms requires S3 request metrics to be enabled on the bucket."
  Write-Output "Console path: S3 > Buckets > $BucketName > Metrics > Request metrics > Enable."
  Write-Output "After enabling request metrics, create alarms in CloudWatch > Alarms > Create alarm > AWS/S3 namespace."
}

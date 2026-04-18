# ----------------------------------------
# Load API key from environment
# ----------------------------------------
$apiKey = $env:API_KEY

if (-not $apiKey) {
    Write-Host "❌ API_KEY is not set in environment"
    Write-Host "Run: `$env:API_KEY='your-key'"
    exit 1
}

Write-Host "Using API_KEY:" $apiKey.Substring(0,8) + "..."

# ----------------------------------------
# Request setup
# ----------------------------------------
$uri = "http://127.0.0.1:8000/v1/chat/completions"

$headers = @{
    "Authorization" = "Bearer $apiKey"
    "Content-Type"  = "application/json"
}

$body = @{
    model = "bot-army"
    messages = @(
        @{ role = "system"; content = "You are helpful" },
        @{ role = "user"; content = "hello" }
    )
    temperature = 0.7
    stream = $false
    tools = @()
    tool_choice = "auto"
} | ConvertTo-Json -Depth 10

# ----------------------------------------
# Send request
# ----------------------------------------
try {
    $response = Invoke-WebRequest -Uri $uri -Method Post -Headers $headers -Body $body

    Write-Host "`n✅ Status:" $response.StatusCode
    Write-Host "Response:`n"

    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "`n❌ Request FAILED"

    if ($_.Exception.Response) {
        $status = $_.Exception.Response.StatusCode.value__
        Write-Host "Status:" $status

        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $body = $reader.ReadToEnd()

        Write-Host "`nResponse Body:`n"
        Write-Host $body
    }
    else {
        Write-Host $_
    }
}
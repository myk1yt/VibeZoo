# VibeZoo 빌드 스크립트 (PowerShell)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$binDir = "bin"
New-Item -ItemType Directory -Force -Path $binDir | Out-Null

$targets = @(
    @{Name="scout"; Path="cmd/scout"},
    @{Name="reviewer"; Path="cmd/reviewer"},
    @{Name="tester"; Path="cmd/tester"},
    @{Name="deep-analyzer"; Path="cmd/deep-analyzer"}
)

foreach ($target in $targets) {
    Write-Host "Building $($target.Name)..." -ForegroundColor Cyan
    
    $output = Join-Path $binDir "$($target.Name).exe"
    go build -ldflags "-s -w" -o $output "./$($target.Path)"
    
    if ($LASTEXITCODE -eq 0) {
        $size = (Get-Item $output).Length / 1KB
        Write-Host "  ✅ $($target.Name).exe ($([math]::Round($size, 1)) KB)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $($target.Name) build failed" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Build complete! Binaries are in $binDir/" -ForegroundColor Green
Write-Host "To start all servers:"
Write-Host "  Start-Process .\bin\scout.exe -ArgumentList '--port', '9022'"
Write-Host "  Start-Process .\bin\reviewer.exe -ArgumentList '--port', '9023'"
Write-Host "  Start-Process .\bin\tester.exe -ArgumentList '--port', '9024'"
Write-Host "  Start-Process .\bin\deep-analyzer.exe -ArgumentList '--port', '9026'"

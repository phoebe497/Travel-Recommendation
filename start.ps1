# ========================================
# Travel Recommendation API - Quick Start
# ========================================
# 
# This script starts the API with Docker Compose

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Travel Recommendation API - Quick Start" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
Write-Host "`nChecking Docker daemon..." -ForegroundColor Yellow
try {
    docker ps | Out-Null
    Write-Host "✓ Docker daemon is running" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker daemon is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# Check if .env file exists
Write-Host "`nChecking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file found" -ForegroundColor Green
} else {
    Write-Host "✗ .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env created. Please update MongoDB URI if needed." -ForegroundColor Green
}

# Navigate to deployment folder
Write-Host "`nNavigating to deployment folder..." -ForegroundColor Yellow
Set-Location -Path "deployment"
Write-Host "✓ Current directory: $(Get-Location)" -ForegroundColor Green

# Start Docker Compose
Write-Host "`nStarting services with Docker Compose..." -ForegroundColor Yellow
Write-Host "(This may take 2-5 minutes on first run)`n" -ForegroundColor Cyan

docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "✓ Services started successfully!" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green
    
    Write-Host "Available Services:" -ForegroundColor Cyan
    Write-Host "  - API Server: http://localhost:8000" -ForegroundColor White
    Write-Host "  - Swagger Docs: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  - ReDoc: http://localhost:8000/redoc" -ForegroundColor White
    Write-Host "  - MongoDB: localhost:27017" -ForegroundColor White
    Write-Host "  - Mongo Express: http://localhost:8081" -ForegroundColor White
    
    Write-Host "`nWaiting for API to be ready..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    $apiReady = $false
    
    while ($attempt -lt $maxAttempts -and -not $apiReady) {
        $attempt++
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                $apiReady = $true
            }
        } catch {
            Write-Host "." -NoNewline
            Start-Sleep -Seconds 2
        }
    }
    
    if ($apiReady) {
        Write-Host "`n✓ API is ready!" -ForegroundColor Green
        
        Write-Host "`nNext Steps:" -ForegroundColor Cyan
        Write-Host "  1. Open Swagger UI: http://localhost:8000/docs" -ForegroundColor White
        Write-Host "  2. Run test script: python test_api.py" -ForegroundColor White
        Write-Host "  3. Check logs: docker logs travel-recommendation-api" -ForegroundColor White
        
        Write-Host "`nTo stop services:" -ForegroundColor Yellow
        Write-Host "  docker-compose down" -ForegroundColor White
        
    } else {
        Write-Host "`n⚠ API might still be starting up" -ForegroundColor Yellow
        Write-Host "Check status: docker ps" -ForegroundColor White
        Write-Host "View logs: docker logs travel-recommendation-api" -ForegroundColor White
    }
    
} else {
    Write-Host "`n✗ Failed to start services!" -ForegroundColor Red
    Write-Host "Check logs with: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# Return to root directory
Set-Location -Path ".."

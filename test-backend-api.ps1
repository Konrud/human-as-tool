# Backend API Testing Script
# Tests authentication, sessions, and core functionality

$baseUrl = "http://localhost:8000"
$testResults = @()

function Test-Endpoint {
    param(
        [string]$TestName,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "TEST: $TestName" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            UseBasicParsing = $true
        }
        
        if ($Body) {
            $params.Body = $Body
            if (-not $Headers.ContainsKey("Content-Type")) {
                $params.ContentType = "application/json"
            }
        }
        
        $response = Invoke-WebRequest @params
        
        Write-Host "✅ PASSED" -ForegroundColor Green
        Write-Host "Status: $($response.StatusCode)"
        Write-Host "Response: $($response.Content)"
        
        $testResults += @{
            Test = $TestName
            Status = "PASSED"
            Code = $response.StatusCode
            Response = $response.Content
        }
        
        return $response
    }
    catch {
        Write-Host "❌ FAILED" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)"
        
        $testResults += @{
            Test = $TestName
            Status = "FAILED"
            Error = $_.Exception.Message
        }
        
        return $null
    }
}

# Test 1: Server Status
Write-Host "`n=== PHASE 1: Server Status ===" -ForegroundColor Yellow
Test-Endpoint "Root Endpoint" "$baseUrl/"
Test-Endpoint "Health Check" "$baseUrl/health"

# Test 2: User Registration
Write-Host "`n=== PHASE 2: Authentication ===" -ForegroundColor Yellow

$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$registerBody = @{
    email = "test$timestamp@example.com"
    username = "testuser$timestamp"
    password = "TestPassword123!"
} | ConvertTo-Json

$registerResponse = Test-Endpoint "User Registration" "$baseUrl/api/auth/register" -Method POST -Body $registerBody

if ($registerResponse) {
    $tokens = $registerResponse.Content | ConvertFrom-Json
    $accessToken = $tokens.access_token
    $refreshToken = $tokens.refresh_token
    
    Write-Host "`nAccess Token: $($accessToken.Substring(0, 50))..." -ForegroundColor Gray
    
    # Test 3: Get Current User
    $authHeaders = @{
        "Authorization" = "Bearer $accessToken"
    }
    
    Test-Endpoint "Get Current User" "$baseUrl/api/auth/me" -Headers $authHeaders
    
    # Test 4: Login
    $loginBody = "username=testuser$timestamp&password=TestPassword123!"
    $loginHeaders = @{
        "Content-Type" = "application/x-www-form-urlencoded"
    }
    
    $loginResponse = Test-Endpoint "User Login" "$baseUrl/api/auth/login" -Method POST -Headers $loginHeaders -Body $loginBody
    
    # Test 5: Token Refresh
    $refreshBody = @{
        refresh_token = $refreshToken
    } | ConvertTo-Json
    
    Test-Endpoint "Token Refresh" "$baseUrl/api/auth/refresh" -Method POST -Body $refreshBody
    
    # Test 6: List Sessions
    Write-Host "`n=== PHASE 3: Session Management ===" -ForegroundColor Yellow
    Test-Endpoint "List Sessions (Empty)" "$baseUrl/api/sessions" -Headers $authHeaders
}

# Test 7: Docs Endpoints
Write-Host "`n=== PHASE 4: Documentation ===" -ForegroundColor Yellow
Test-Endpoint "Swagger UI" "$baseUrl/docs"
Test-Endpoint "ReDoc" "$baseUrl/redoc"

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$passed = ($testResults | Where-Object { $_.Status -eq "PASSED" }).Count
$failed = ($testResults | Where-Object { $_.Status -eq "FAILED" }).Count
$total = $testResults.Count

Write-Host "Total Tests: $total"
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Success Rate: $(($passed / $total * 100).ToString('0.00'))%"

if ($failed -eq 0) {
    Write-Host "`n✅ ALL TESTS PASSED!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ SOME TESTS FAILED" -ForegroundColor Yellow
}


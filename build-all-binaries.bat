@echo off
REM ZeroTrust DNS - Build All Platform Binaries (Windows)
REM Compiles endpoint.go for Windows and Linux (x64 and ARM64)

setlocal enabledelayedexpansion

echo ========================================
echo ZeroTrust DNS - Binary Builder
echo ========================================
echo.

REM Check if Go is installed
where go >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Go is not installed!
    echo.
    echo Install Go from: https://go.dev/dl/
    echo.
    pause
    exit /b 1
)

REM Get Go version
for /f "tokens=*" %%i in ('go version') do set GO_VERSION=%%i
echo Found: %GO_VERSION%
echo.

REM Check if endpoint.go exists
if not exist "endpoint.go" (
    echo ERROR: endpoint.go not found
    echo Expected location: %CD%\endpoint.go
    pause
    exit /b 1
)

echo Found: endpoint.go
echo.

REM Create output directory
if not exist "binaries" mkdir binaries

REM Initialize Go module if needed
if not exist "go.mod" (
    echo Initializing Go module...
    go mod init zerotrust-endpoint
    go get github.com/golang-jwt/jwt/v5
    go mod tidy
    echo.
)

REM Download dependencies
echo Downloading Go dependencies...
go mod download
go mod verify
echo.

echo Building binaries for all platforms...
echo --------------------------------------
echo.

REM Build Windows x64
echo Building ZeroTrust-Client-x64.exe ...
set GOOS=windows
set GOARCH=amd64
set CGO_ENABLED=0
go build -ldflags="-s -w -H=windowsgui" -trimpath -o binaries\ZeroTrust-Client-x64.exe endpoint.go
if %errorlevel% neq 0 (
    echo FAILED
    pause
    exit /b 1
)
echo OK
copy /Y binaries\ZeroTrust-Client-x64.exe binaries\ZeroTrust-Service-x64.exe >nul
echo Created ZeroTrust-Service-x64.exe
echo.

REM Build Windows ARM64
echo Building ZeroTrust-Client-ARM64.exe ...
set GOOS=windows
set GOARCH=arm64
set CGO_ENABLED=0
go build -ldflags="-s -w -H=windowsgui" -trimpath -o binaries\ZeroTrust-Client-ARM64.exe endpoint.go
if %errorlevel% neq 0 (
    echo FAILED
    pause
    exit /b 1
)
echo OK
copy /Y binaries\ZeroTrust-Client-ARM64.exe binaries\ZeroTrust-Service-ARM64.exe >nul
echo Created ZeroTrust-Service-ARM64.exe
echo.

REM Build Linux x64
echo Building ZeroTrust-Client-x86_64 ...
set GOOS=linux
set GOARCH=amd64
set CGO_ENABLED=0
go build -ldflags="-s -w" -trimpath -o binaries\ZeroTrust-Client-x86_64 endpoint.go
if %errorlevel% neq 0 (
    echo FAILED
    pause
    exit /b 1
)
echo OK
copy /Y binaries\ZeroTrust-Client-x86_64 binaries\ZeroTrust-Service-x86_64 >nul
echo Created ZeroTrust-Service-x86_64
echo.

REM Build Linux ARM64
echo Building ZeroTrust-Client-arm64 ...
set GOOS=linux
set GOARCH=arm64
set CGO_ENABLED=0
go build -ldflags="-s -w" -trimpath -o binaries\ZeroTrust-Client-arm64 endpoint.go
if %errorlevel% neq 0 (
    echo FAILED
    pause
    exit /b 1
)
echo OK
copy /Y binaries\ZeroTrust-Client-arm64 binaries\ZeroTrust-Service-arm64 >nul
echo Created ZeroTrust-Service-arm64
echo.

echo ========================================
echo Build Summary
echo ========================================
echo.
dir /B binaries\ZeroTrust-*
echo.
echo All binaries built successfully!
echo.
echo Next steps:
echo   1. Copy to server: xcopy /Y binaries\* \opt\zerotrust-dns\binaries\
echo   2. Or start server: python server.py
echo.
pause
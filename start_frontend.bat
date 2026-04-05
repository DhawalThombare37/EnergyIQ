@echo off
echo Starting EnergyIQ React Frontend...

:: Direct paths to node and npm engine
set "NODE_EXE=D:\NPM Doc\node.exe"
set "NPM_CLI=D:\node_modules\npm\bin\npm-cli.js"

:: Add Node folder to PATH so Vite can find it
set "PATH=D:\NPM Doc;%PATH%"

cd /d d:\NewProject\frontend

echo Step 1: Installing dependencies...
"%NODE_EXE%" "%NPM_CLI%" install
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Installation failed. If you see 'EBUSY', please restart your computer to unlock files.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Step 2: Starting development server...
"%NODE_EXE%" "%NPM_CLI%" run dev
pause

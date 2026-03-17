@echo off
REM ====================================
REM PM Agent Startup Script
REM ====================================

echo.
echo ========================================
echo   PM Agent - Project Manager
echo ========================================
echo.
echo Starting PM Agent...
echo.

REM Check if in correct directory
if not exist "agents\pm\AGENTS.md" (
    echo Error: Not in PM Agent template directory!
    echo Please run this script from the template root.
    exit /b 1
)

REM Start OpenCode with PM Agent
opencode --agent pm

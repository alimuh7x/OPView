@echo off
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo  OPView - One-Click Launcher (Windows)
echo ==========================================
echo.

:: ── Step 1: Find a supported Python (3.12 or 3.13) ──────────────────────
set "PY_CMD="

:: Try the Windows 'py' launcher first (most reliable on Windows)
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3.13 --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=py -3.13"
        goto :found_python
    )
    py -3.12 --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=py -3.12"
        goto :found_python
    )
)

:: Try direct commands
for %%P in (python3.13 python3.12 python) do (
    where %%P >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=2 delims= " %%V in ('%%P --version 2^>^&1') do (
            echo %%V | findstr /b "3.13 3.12" >nul
            if !errorlevel! equ 0 (
                set "PY_CMD=%%P"
                goto :found_python
            )
        )
    )
)

:: No supported Python found
echo ERROR: Python 3.12 or 3.13 not found.
echo.
echo Install Python from https://www.python.org/downloads/
echo Or run:  winget install Python.Python.3.12
echo.
echo IMPORTANT: Check "Add Python to PATH" during installation.
echo.
pause
exit /b 1

:found_python
for /f "tokens=*" %%V in ('!PY_CMD! --version 2^>^&1') do set "PY_VER=%%V"
echo [1/4] Found %PY_VER%

:: ── Step 2: Create or reuse virtual environment ─────────────────────────
cd /d "%~dp0"

if exist "myenv\Scripts\python.exe" (
    echo [2/4] Virtual environment already exists - reusing
) else (
    echo [2/4] Creating virtual environment...
    !PY_CMD! -m venv myenv
    if !errorlevel! neq 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: ── Step 3: Install / update dependencies ───────────────────────────────
echo [3/4] Installing dependencies...
call myenv\Scripts\activate.bat

python -m pip install --upgrade pip --quiet 2>nul
pip install --upgrade -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install dependencies.
    echo Trying again without --quiet for details...
    pip install --upgrade -r requirements.txt
    pause
    exit /b 1
)

:: Quick verification
python -c "import dash, vtk, pyvista, numpy; print('  All core modules OK')"
if %errorlevel% neq 0 (
    echo WARNING: Some modules failed to import, but continuing...
)

:: ── Step 4: Launch server and open browser ──────────────────────────────
echo [4/4] Starting OPView server...
echo.
echo ==========================================
echo  OPView will open at http://127.0.0.1:8050
echo  Press Ctrl+C to stop the server
echo ==========================================
echo.

:: Open browser after a short delay (gives the server time to start)
start "" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:8050"

:: Run the application (this blocks until Ctrl+C)
python OPView.py

:: Cleanup
call myenv\Scripts\deactivate.bat 2>nul
echo.
echo OPView stopped.
pause

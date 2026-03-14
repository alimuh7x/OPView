@echo off
setlocal enabledelayedexpansion

:: Configuration
set "APP_URL=http://127.0.0.1:8050"

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
echo Then Restart Terminal / Powershell again.
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
    :: Validate virtual environment was created successfully
    if not exist "myenv\Scripts\python.exe" (
        echo ERROR: Virtual environment creation failed - executable not found.
        pause
        exit /b 1
    )
)

:: ── Step 3: Check and install dependencies ──────────────────────────────
echo [3/4] Checking dependencies...
call myenv\Scripts\activate.bat

:: Validate virtual environment Python executable
myenv\Scripts\python.exe --version >nul 2>&1
if !errorlevel! neq 0 (
    set "NEED_REPAIR=1"
    echo   Virtual environment Python not functional - will repair
) else (
    :: Fast startup policy: verify essential runtime deps only.
    :: To force a full dependency repair, run with OPVIEW_REPAIR_DEPS=1.
    set "NEED_REPAIR=0"
    if "%OPVIEW_REPAIR_DEPS%"=="1" (
        set "NEED_REPAIR=1"
        echo   Repair mode enabled: installing all dependencies
    ) else (
        myenv\Scripts\python.exe -c "import dash, numpy, plotly, pandas, scipy, markdown, plyer, vtk, pyvista" >nul 2>&1
        if !errorlevel! neq 0 (
            set "NEED_REPAIR=1"
            echo   Missing essential dependencies
        ) else (
            echo   Essential dependencies present (skipping heavyweight import check)
        )
    )
)

if "!NEED_REPAIR!"=="1" (
    echo   Installing dependencies from requirements.txt...
    myenv\Scripts\python.exe -m pip install --upgrade pip --quiet 2>nul
    myenv\Scripts\python.exe -m pip install --upgrade -r requirements.txt
    if !errorlevel! neq 0 (
        echo.
        echo ERROR: Failed to install dependencies.
        echo   Please check your internet connection and try again.
        pause
        exit /b 1
    )
    echo   Verifying installation...
    myenv\Scripts\python.exe -c "import dash, numpy, plotly, pandas, scipy, markdown, plyer, vtk, pyvista; print('  All core modules OK')"
    if !errorlevel! neq 0 (
        echo ERROR: Installed dependencies failed verification.
        echo   Try running with OPVIEW_REPAIR_DEPS=1 to force reinstallation.
        pause
        exit /b 1
    )
)

:: ── Step 4: Launch server and open browser ──────────────────────────────
echo [4/4] Starting OPView server...
echo.
echo ==========================================
echo  OPView will open at %APP_URL%
echo  Press Ctrl+C to stop the server
echo ==========================================
echo.

:: Open browser after a short delay (gives the server time to start)
start "" cmd /c "timeout /t 3 /nobreak >nul & start %APP_URL%"

:: Run the application (this blocks until Ctrl+C)
myenv\Scripts\python.exe OPView.py

:: Cleanup
call myenv\Scripts\deactivate.bat 2>nul
echo.
echo OPView stopped.
pause

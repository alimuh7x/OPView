@echo off
REM VTK 2D Slice Viewer - Automated Setup Script
REM For Windows systems

ECHO ========================================
ECHO VTK 2D Slice Viewer - Setup
ECHO ========================================
ECHO.

REM Check for Python
where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Python not found!
    ECHO.
    ECHO Please install Python 3.12 or 3.13 from:
    ECHO https://www.python.org/downloads/
    ECHO.
    ECHO Note: Python 3.14 is NOT compatible with VTK
    ECHO.
    PAUSE
    EXIT /B 1
)

ECHO Found Python:
python --version
ECHO.

REM Check if virtual environment already exists
IF EXIST myenv\ (
    ECHO WARNING: Virtual environment 'myenv' already exists!
    SET /P REPLY="Do you want to remove it and create a fresh one? (y/n): "
    IF /I "%REPLY%"=="y" (
        ECHO Removing old virtual environment...
        RMDIR /S /Q myenv
        ECHO Old environment removed
    ) ELSE (
        ECHO Keeping existing environment and updating packages...
        CALL myenv\Scripts\activate
        python -m pip install --upgrade pip
        pip install --upgrade -r requirements.txt
        ECHO.
        ECHO Packages updated!
        ECHO.
        ECHO To run the application:
        ECHO   myenv\Scripts\activate
        ECHO   python app.py
        ECHO.
        PAUSE
        EXIT /B 0
    )
)

REM Create virtual environment
ECHO Creating virtual environment...
python -m venv myenv
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO ERROR: Failed to create virtual environment
    ECHO.
    ECHO Please ensure Python is properly installed
    ECHO.
    PAUSE
    EXIT /B 1
)
ECHO Virtual environment created
ECHO.

REM Activate virtual environment
ECHO Activating virtual environment...
CALL myenv\Scripts\activate
ECHO Virtual environment activated
ECHO.

REM Upgrade pip
ECHO Upgrading pip to latest version...
python -m pip install --upgrade pip --quiet
ECHO pip upgraded
ECHO.

REM Install requirements
ECHO Installing dependencies...
ECHO   This may take 3-5 minutes depending on your internet speed
ECHO   Total download size: ~200 MB
ECHO.
ECHO   Installing packages:
ECHO     - dash (web framework)
ECHO     - plotly (visualization)
ECHO     - numpy (numerical computing)
ECHO     - scipy (scientific computing)
ECHO     - pyvista (3D visualization)
ECHO     - vtk (112 MB - largest package)
ECHO     - and 42 other dependencies...
ECHO.

pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO ERROR: Failed to install dependencies
    ECHO.
    ECHO Please check:
    ECHO   1. Internet connection is stable
    ECHO   2. requirements.txt file exists
    ECHO   3. Sufficient disk space (~500 MB)
    ECHO.
    PAUSE
    EXIT /B 1
)

ECHO.
ECHO All dependencies installed successfully!
ECHO.

REM Verify installation
ECHO Verifying installation...
python -c "import dash; print('  OK Dash version:', dash.__version__)"
python -c "import plotly; print('  OK Plotly version:', plotly.__version__)"
python -c "import numpy; print('  OK NumPy version:', numpy.__version__)"
python -c "import scipy; print('  OK SciPy version:', scipy.__version__)"
python -c "import pyvista; print('  OK PyVista version:', pyvista.__version__)"
python -c "import vtk; print('  OK VTK version:', vtk.vtkVersion.GetVTKVersion())"

ECHO.
ECHO ========================================
ECHO Setup Complete!
ECHO ========================================
ECHO.
ECHO To run the application:
ECHO.
ECHO   1. Activate the virtual environment:
ECHO      myenv\Scripts\activate
ECHO.
ECHO   2. Run the app:
ECHO      python app.py
ECHO.
ECHO   3. Open your browser to:
ECHO      http://127.0.0.1:8050
ECHO.
ECHO To stop the app: Press Ctrl+C
ECHO To deactivate: Run 'deactivate'
ECHO.
ECHO ========================================
ECHO.

REM Ask if user wants to run the app now
SET /P REPLY="Would you like to run the application now? (y/n): "
IF /I "%REPLY%"=="y" (
    ECHO.
    ECHO Starting application...
    ECHO Access it at: http://127.0.0.1:8050
    ECHO Press Ctrl+C to stop
    ECHO.
    python app.py
)

PAUSE

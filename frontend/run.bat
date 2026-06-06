@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_EXE=D:\Tools\Miniconda3\envs\voicecal\python.exe"

echo ========================================
echo Starting Novel to Script Streamlit App
echo Project dir: %cd%
echo Python exe : %PYTHON_EXE%
echo ========================================
echo.

if not exist "%PYTHON_EXE%" (
    echo [ERROR] Python executable not found.
    echo Path:
    echo %PYTHON_EXE%
    echo.
    echo Please check whether this file exists:
    echo D:\Tools\Miniconda3\envs\voicecal\python.exe
    echo.
    pause
    exit /b 1
)

cd /d "%~dp0.."

if not exist "frontend\app.py" (
    echo [ERROR] frontend\app.py not found.
    echo Current directory:
    echo %cd%
    echo.
    echo Please ensure frontend\app.py exists.
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m streamlit run frontend/app.py

echo.
echo Streamlit exited with code: %errorlevel%
pause
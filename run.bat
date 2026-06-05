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

if not exist "app.py" (
    echo [ERROR] app.py not found in current directory.
    echo Current directory:
    echo %cd%
    echo.
    echo Please put run.bat in the same folder as app.py.
    echo.
    pause
    exit /b 1
)

"%PYTHON_EXE%" -m streamlit run app.py

echo.
echo Streamlit exited with code: %errorlevel%
pause
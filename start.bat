@echo off
echo 正在启动 Learning Community Backend...

REM 检查是否已激活conda环境
if "%CONDA_DEFAULT_ENV%"=="learning-community-backend" (
    echo Conda环境已激活: %CONDA_DEFAULT_ENV%
) else (
    echo 警告: Conda环境未激活或不是 learning-community-backend
    echo 请先运行: conda activate learning-community-backend
    pause
    exit /b 1
)

REM 检查依赖是否已安装
python -c "import flask" 2>nul
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
)

REM 启动Flask应用
echo 启动Flask应用...
python app.py

pause
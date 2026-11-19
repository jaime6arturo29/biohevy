@echo off
title BioHevy - Sistema de Prediccion de Fatiga EMG
color 0B

echo =================================================================
echo   ⚡ INICIANDO BIOHEVY: SISTEMA DE PREDICCION DE FATIGA EMG ⚡
echo =================================================================
echo.

:: 1. Verificar instalación de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python no esta instalado o no se encuentra en el PATH.
    echo Por favor, instala Python 3.9 o superior y marca la casilla "Add Python to PATH".
    pause
    exit
)

:: 2. Verificar instalación de Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Node.js no esta instalado.
    echo Por favor, instala Node.js LTS desde https://nodejs.org/ antes de correr.
    pause
    exit
)

:: 3. Instalar dependencias del Backend
echo [*] Configurando entorno de Python y dependencias del Backend...
cd backend
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARN] Hubo un problema instalando dependencias. Intentando continuar...
)
cd ..

:: 4. Instalar dependencias del Frontend
echo [*] Configurando dependencias del Frontend (React/Next.js)...
cd biohevy-web
if not exist node_modules (
    echo [*] Instalando modulos de Node (esto toma unos momentos)...
    npm install --no-audit --no-fund
)
cd ..

:: 5. Ejecutar Backend y Frontend en paralelo
echo.
echo =================================================================
echo   🚀 SERVIDORES INICIADOS EXITOSAMENTE.
echo   La aplicacion se abrira en tu navegador web.
echo   Para cerrar el programa, cierra esta ventana del CMD.
echo =================================================================
echo.

:: Lanzar Backend en segundo plano
start /b cmd /c "cd backend && python main.py"

:: Esperar 2 segundos para dar tiempo al backend
timeout /t 2 /nobreak >nul

:: Lanzar Frontend en segundo plano
start /b cmd /c "cd biohevy-web && npm run dev"

:: Abrir navegador en la aplicación automáticamente
timeout /t 3 /nobreak >nul
start http://localhost:3000

:: Mantener viva la terminal principal para logs
echo logs del sistema en ejecucion:
echo -----------------------------------------------------------------
cd backend
python main.py

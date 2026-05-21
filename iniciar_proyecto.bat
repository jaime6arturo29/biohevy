@echo off
title BioHevy Dev Suite Launcher
color 0b

echo =================================================================
echo   ____  _       _    _                      
echo  ^|  _ ^\^(_) ___ ^| ^|  ^| ^| ___ __   __ _   _ 
echo  ^| ^|_) ^| ^|/ _ \^| ^|_^| ^|/ _ \^\ \ / / ^| ^| ^| ^|
echo  ^|  _ ^(^| ^| (_) ^|  _  ^|  __/^\ V /^| ^|_^| ^| ^|
echo  ^|_^| ^\_^\_^|\___/^|_^| ^|_^|\___^| \_/  \__, ^| ^|
echo                                   ^|___/  
echo  =================================================================
echo   SISTEMA BIOMECANICO DE FATIGA MUSCULAR - MODO DESARROLLADOR
echo  =================================================================
echo.

echo [+] Iniciando Backend Engine (FastAPI en Puerto 8000)...
start "BioHevy Backend API" cmd /c "cd /d "%~dp0backend" && py -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo [+] Iniciando Frontend Dashboard (Next.js en Puerto 3000)...
start "BioHevy Frontend App" cmd /c "cd /d "%~dp0biohevy-web" && npm run dev"

echo [+] Esperando 3 segundos para el encendido del servidor...
timeout /t 3 /nobreak >nul

echo [+] Lanzando el panel de control en tu navegador...
start http://localhost:3000
start http://127.0.0.1:8000/docs

echo =================================================================
echo   [OK] TODO LISTO! Puedes cerrar esta ventana.
echo   Para detener los servidores, cierra las ventanas de terminal
echo   del Backend y del Frontend.
echo =================================================================
pause

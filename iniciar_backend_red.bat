@echo off
title BioHevy Backend API (Acceso Red Local)
color 0a
cd /d "%~dp0backend"
echo =================================================================
echo   INICIANDO BACKEND EN MODO RED LOCAL (ACEPTA CONEXION ESP32)
echo =================================================================
echo.
py main.py
pause

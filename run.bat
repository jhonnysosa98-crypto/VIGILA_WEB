@echo off
chcp 65001 > nul
title OmniGuard CCTV - Sistema de Monitoreo de Video
color 0A

echo.
echo  ========================================================
echo        OMNIGUARD CCTV v1.0 - SISTEMA DE MONITOREO
echo  ========================================================
echo.

:: Intentar abrir firewall automaticamente (funciona si tiene permisos)
netsh advfirewall firewall add rule name="OmniGuard5000" protocol=TCP dir=in localport=5000 action=allow profile=any > nul 2>&1

:: Verificar que Python esté instalado
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    py --version > nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo  [!] Python no encontrado. Instala Python desde python.org
        pause
        exit /b 1
    )
    :: Usar "py" en lugar de "python"
    echo  Iniciando con Waitress (acceso desde celular)...
    py run.py
    goto :fin
)

echo  Iniciando servidor...
python run.py

:fin
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo  [!] Ocurrio un error. Verifica que Python este instalado.
    pause
)

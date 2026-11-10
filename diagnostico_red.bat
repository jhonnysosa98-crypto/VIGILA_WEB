@echo off
title OmniGuard - Diagnostico de Red
color 0E

echo.
echo  =========================================================
echo    OMNIGUARD CCTV - Diagnostico de Conexion desde Celular
echo  =========================================================
echo.

echo  [1] Verificando IP de esta PC en la red Wi-Fi...
echo.
ipconfig | findstr /R "IPv4" | findstr /V "127.0.0.1" | findstr /V "169.254"
echo.

echo  [2] Verificando si el servidor esta corriendo en el puerto 5000...
netstat -an | findstr ":5000"
if errorlevel 1 (
    echo  [!] ADVERTENCIA: El servidor NO esta activo en el puerto 5000.
    echo      Inicia primero el sistema con run.bat o python run.py
) else (
    echo  [OK] El servidor esta activo y escuchando.
)
echo.

echo  [3] Verificando reglas del Firewall para el puerto 5000...
netsh advfirewall firewall show rule name="OmniGuard Puerto 5000 TCP" >nul 2>&1
if errorlevel 1 (
    echo  [!] PROBLEMA: No existe la regla del Firewall para OmniGuard.
    echo      Ejecuta "habilitar_acceso_celular.bat" como Administrador.
) else (
    echo  [OK] Regla del Firewall encontrada.
)
echo.

echo  [4] Estado general del Firewall de Windows...
netsh advfirewall show currentprofile state | findstr "Estado\|State"
echo.

echo  =========================================================
echo   RESUMEN:
echo   - Si el servidor NO esta activo: arranca run.bat primero
echo   - Si la regla del Firewall NO existe:
echo     Haz CLIC DERECHO en habilitar_acceso_celular.bat
echo     y elige "Ejecutar como administrador"
echo.
echo   URL para el celular (en el mismo Wi-Fi):
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4.*10\.\|IPv4.*192\.168\."') do (
    set IP=%%a
    goto :show
)
:show
set IP=%IP: =%
echo     http://%IP%:5000
echo  =========================================================
echo.
pause

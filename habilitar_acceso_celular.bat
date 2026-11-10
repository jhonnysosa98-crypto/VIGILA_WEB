@echo off
title OmniGuard - Habilitar Acceso desde Celular
color 0B

echo.
echo  =========================================================
echo    OMNIGUARD CCTV - Habilitar Acceso desde Celular
echo  =========================================================
echo.
echo  Este asistente abrira el puerto 5000 en el Firewall de
echo  Windows para que tu celular pueda conectarse al sistema.
echo.
echo  Necesitas permisos de Administrador para continuar.
echo  =========================================================
echo.

:: Verificar si se ejecuta como administrador
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo  [!] No tienes permisos de Administrador.
    echo.
    echo  ------ COMO EJECUTAR COMO ADMINISTRADOR ------
    echo.
    echo  1. Cierra esta ventana
    echo  2. Busca el archivo "habilitar_acceso_celular.bat"
    echo  3. Haz CLIC DERECHO sobre el archivo
    echo  4. Selecciona "Ejecutar como administrador"
    echo  5. Acepta la ventana de permisos (UAC)
    echo.
    echo  -----------------------------------------------
    echo.
    pause
    exit /b 1
)

echo  [1/3] Eliminando regla anterior si existe...
netsh advfirewall firewall delete rule name="OmniGuard Puerto 5000 TCP" >nul 2>&1
netsh advfirewall firewall delete rule name="OmniGuard Puerto 5000 UDP" >nul 2>&1

echo  [2/3] Creando nueva regla para el puerto 5000...
netsh advfirewall firewall add rule name="OmniGuard Puerto 5000 TCP" ^
    protocol=TCP dir=in localport=5000 action=allow profile=private,domain,public

netsh advfirewall firewall add rule name="OmniGuard Puerto 5000 UDP" ^
    protocol=UDP dir=in localport=5000 action=allow profile=private,domain,public

echo  [3/3] Verificando regla creada...
netsh advfirewall firewall show rule name="OmniGuard Puerto 5000 TCP" | findstr "Accion\|Action\|Puerto\|LocalPort"

echo.
echo  =========================================================
echo   LISTO! El puerto 5000 esta habilitado.
echo.

:: Detectar IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4.*10\.\|IPv4.*192\.168\.\|IPv4.*172\."') do (
    set IP=%%a
    goto :found_ip
)
:found_ip
set IP=%IP: =%

echo   Tu celular debe conectarse a:
echo.
echo     http://%IP%:5000
echo.
echo   Pasos:
echo   1. Tu celular debe estar en la misma red Wi-Fi
echo   2. Abre el navegador del celular (Chrome, Safari)
echo   3. Escribe la direccion de arriba
echo      O escanea el QR en la pantalla del sistema
echo  =========================================================
echo.
pause

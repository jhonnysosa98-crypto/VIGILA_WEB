import sys
import os
import time
import socket
import webbrowser
import threading

PORT = 5000

def get_local_ip():
    """Detecta la IP real de red (Wi-Fi/Ethernet), no la de loopback."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def verificar_puerto_libre(port):
    """Comprueba que el puerto no esté ocupado por otro proceso."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.close()
        return True
    except OSError as e:
        print(f"[!] ADVERTENCIA: Puerto {port} ocupado → {e}")
        print(f"    Cierra cualquier otra instancia del sistema e intenta de nuevo.")
        return False

def check_dependencies():
    missing_required = []
    try:
        import flask
    except ImportError:
        missing_required.append("flask")
    try:
        import psutil
    except ImportError:
        missing_required.append("psutil")

    if missing_required:
        print("[!] Instalando librerías requeridas:", ", ".join(missing_required))
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_required])

    missing_cv = []
    try:
        import cv2
    except ImportError:
        missing_cv.append("opencv-python")
    try:
        import numpy
    except ImportError:
        missing_cv.append("numpy")

    if missing_cv:
        print("--------------------------------------------------------")
        print("[i] Modo Simulación CCTV activo.")
        print("    Para conectar webcams reales: pip install opencv-python numpy")
        print("--------------------------------------------------------\n")
    else:
        print("[+] OpenCV detectado. Cámaras físicas habilitadas.\n")

def open_browser(url):
    time.sleep(1.5)
    print(f"[+] Abriendo navegador: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    check_dependencies()

    local_ip = get_local_ip()
    url_local   = f"http://127.0.0.1:{PORT}"
    url_celular = f"http://{local_ip}:{PORT}"

    print("=" * 58)
    print("      OMNIGUARD CCTV v1.0 - SISTEMA DE MONITOREO")
    print("=" * 58)
    print(f" Panel Web (esta PC):  {url_local}")
    print(f" Acceso desde Celular: {url_celular}")
    print("   (Escanea el QR en la pantalla o escribe esa URL)")
    print(" -------------------------------------------------------")

    # Verificar disponibilidad del puerto
    if not verificar_puerto_libre(PORT):
        print("\n[!] No se pudo iniciar. Cierra otras instancias e intenta de nuevo.")
        input("Presiona Enter para salir...")
        sys.exit(1)

    from app import app, camera_manager

    # Abrir navegador automáticamente
    threading.Thread(target=open_browser, args=(url_local,), daemon=True).start()

    print(f"\n[+] Iniciando servidor en 0.0.0.0:{PORT}...")

    try:
        # --- Waitress: servidor WSGI para Windows (mejor acceso en red) ---
        try:
            from waitress import serve
            print(f"[+] Motor: Waitress (acceso desde celular optimizado)")
            print(f"[+] Sistema listo. Presiona Ctrl+C para detener.\n")
            serve(app, host="0.0.0.0", port=PORT, threads=8,
                  channel_timeout=120, cleanup_interval=30)
        except ImportError:
            # Fallback a Werkzeug/Flask dev server
            print(f"[i] Motor: Flask dev server")
            print(f"[+] Sistema listo. Presiona Ctrl+C para detener.\n")
            app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True,
                    use_reloader=False)
    except KeyboardInterrupt:
        print("\n[*] Deteniendo sistema...")
    except Exception as e:
        print(f"\n[!] Error al iniciar servidor: {e}")
    finally:
        camera_manager.shutdown_all()
        print("[+] Sistema detenido correctamente.")

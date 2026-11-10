import os
import time
import json
import psutil
from flask import Flask, render_template, Response, request, jsonify, send_from_directory
from core import database
from core.camera import CameraManager

# Inicialización
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECORDINGS_DIR = os.path.join(BASE_DIR, "recordings")
os.makedirs(os.path.join(RECORDINGS_DIR, "snapshots"), exist_ok=True)
os.makedirs(os.path.join(RECORDINGS_DIR, "videos"), exist_ok=True)

database.init_db()

def get_local_ip():
    """Detecta la IP local de red para conexión desde dispositivos móviles."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

app = Flask(__name__, static_folder="static", template_folder="templates")

@app.context_processor
def inject_network_info():
    ip = get_local_ip()
    return {
        'local_ip': ip,
        'mobile_url': f"http://{ip}:5000"
    }

camera_manager = CameraManager()

# Cola reciente de alertas en memoria para despacho en tiempo real
recent_alerts = []

def on_new_alert(event_data):
    recent_alerts.append(event_data)
    if len(recent_alerts) > 100:
        recent_alerts.pop(0)

camera_manager.register_alert_subscriber(on_new_alert)
camera_manager.load_cameras_from_db()


# ==========================================
# RUTAS DE PÁGINAS WEB (FRONTEND)
# ==========================================

@app.route('/')
def index():
    """Pantalla principal de Monitoreo / CCTV."""
    cameras = database.get_cameras()
    return render_template('dashboard.html', cameras=cameras)

@app.route('/playback')
def playback():
    """Pantalla de Galería de Grabaciones y Eventos."""
    cameras = database.get_cameras()
    return render_template('playback.html', cameras=cameras)

@app.route('/settings')
def settings():
    """Pantalla de Configuración de Cámaras y Sistema."""
    cameras = database.get_cameras()
    return render_template('settings.html', cameras=cameras)


# ==========================================
# RUTAS DE STREAMING DE VIDEO (MJPEG)
# ==========================================

@app.route('/video_feed/<camera_id>')
def video_feed(camera_id):
    """Transmite el feed de la cámara en formato MJPEG optimizado para bajo consumo y alta fluidez."""
    def generate_stream():
        cam = camera_manager.get_camera(camera_id)
        if not cam:
            return

        while True:
            try:
                frame_data, ctype = cam.get_frame_bytes()
                if frame_data is not None:
                    header = f'--frame\r\nContent-Type: {ctype}\r\nContent-Length: {len(frame_data)}\r\n\r\n'.encode('utf-8')
                    yield (header + frame_data + b'\r\n')
                time.sleep(0.08) # ~12 FPS óptimo: ahorra 60% de ancho de banda y evita saturar hilos
            except (GeneratorExit, ConnectionResetError, BrokenPipeError):
                break

    response = Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
    response.headers['Cache-Control'] = 'no-cache, private'
    response.headers['X-Accel-Buffering'] = 'no'
    return response

@app.route('/api/cam_frame/<camera_id>')
def single_frame_api(camera_id):
    """Retorna un único fotograma ligero bajo demanda (ideal para conexiones móviles lentas)."""
    cam = camera_manager.get_camera(camera_id)
    if not cam:
        return ('', 404)
    frame_data, ctype = cam.get_frame_bytes()
    if frame_data is None:
        return ('', 204)
    res = Response(frame_data, mimetype=ctype)
    res.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return res

@app.route('/api/qr_code.png')
def qr_code_png():
    """Genera y sirve el código QR real (PNG) con la URL de acceso móvil."""
    try:
        import qrcode
        from io import BytesIO
        from flask import send_file
        ip = get_local_ip()
        url = f"http://{ip}:5000"
        qr = qrcode.QRCode(
            version=2,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return send_file(buf, mimetype='image/png', max_age=0)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/recordings/<path:filename>')
def serve_recording(filename):
    """Sirve archivos de imágenes y videos grabados."""
    return send_from_directory(RECORDINGS_DIR, filename)


# ==========================================
# API REST: CÁMARAS Y ESTADO
# ==========================================

@app.route('/api/network_info', methods=['GET'])
def network_info_api():
    """Retorna información de red para conexión móvil y generación de QR."""
    ip = get_local_ip()
    port = 5000
    return jsonify({
        'local_ip': ip,
        'port': port,
        'mobile_url': f"http://{ip}:{port}"
    })

@app.route('/api/cameras', methods=['GET'])
def get_cameras_api():
    """Retorna lista de cámaras y sus estados en tiempo real."""
    return jsonify(camera_manager.get_all_status())

@app.route('/api/cameras', methods=['POST'])
def add_camera_api():
    """Agrega una nueva cámara al sistema."""
    data = request.json or {}
    cam_id = data.get('id') or f"cam_{int(time.time())}"
    name = data.get('name', 'Nueva Cámara')
    source_type = data.get('source_type', 'webcam')
    source_url = data.get('source_url', '0')
    motion_enabled = 1 if data.get('motion_enabled', True) else 0
    sensitivity = int(data.get('sensitivity', 30))
    record_on_motion = 1 if data.get('record_on_motion', True) else 0

    database.add_camera(
        camera_id=cam_id,
        name=name,
        source_type=source_type,
        source_url=source_url,
        motion_enabled=motion_enabled,
        sensitivity=sensitivity,
        record_on_motion=record_on_motion
    )
    camera_manager.load_cameras_from_db()
    return jsonify({'success': True, 'camera_id': cam_id})

@app.route('/api/cameras/<camera_id>', methods=['PUT'])
def update_camera_api(camera_id):
    """Actualiza la configuración de una cámara existente."""
    data = request.json or {}
    updatable_fields = ['name', 'source_type', 'source_url', 'is_active', 'motion_enabled', 'sensitivity', 'record_on_motion']
    fields = {}
    for f in updatable_fields:
        if f in data:
            fields[f] = data[f]

    if fields:
        database.update_camera(camera_id, **fields)
        camera_manager.load_cameras_from_db()

    return jsonify({'success': True})

@app.route('/api/cameras/<camera_id>', methods=['DELETE'])
def delete_camera_api(camera_id):
    """Elimina una cámara del sistema."""
    database.delete_camera(camera_id)
    camera_manager.load_cameras_from_db()
    return jsonify({'success': True})

@app.route('/api/cameras/<camera_id>/toggle_active', methods=['POST'])
def toggle_camera_active(camera_id):
    """Enciende o apaga una cámara."""
    cam = camera_manager.get_camera(camera_id)
    if not cam:
        return jsonify({'error': 'Cámara no encontrada'}), 404

    if cam.is_running:
        camera_manager.stop_camera(camera_id)
        return jsonify({'status': 'stopped'})
    else:
        camera_manager.start_camera(camera_id)
        return jsonify({'status': 'started'})

@app.route('/api/cameras/<camera_id>/snapshot', methods=['POST'])
def take_snapshot(camera_id):
    """Toma una foto instantánea en vivo."""
    res = camera_manager.trigger_snapshot(camera_id)
    if res:
        return jsonify({'success': True, **res})
    return jsonify({'error': 'No se pudo capturar la imagen'}), 400

@app.route('/api/cameras/<camera_id>/toggle_record', methods=['POST'])
def toggle_recording(camera_id):
    """Inicia o detiene la grabación manual en una cámara."""
    res = camera_manager.toggle_recording(camera_id)
    return jsonify({'success': True, **res})


# ==========================================
# API REST: EVENTOS Y ALERTAS
# ==========================================

@app.route('/api/events', methods=['GET'])
def get_events_api():
    """Consulta la lista de eventos y grabaciones almacenados."""
    limit = int(request.args.get('limit', 50))
    camera_id = request.args.get('camera_id')
    event_type = request.args.get('event_type')
    events = database.get_events(limit=limit, camera_id=camera_id, event_type=event_type)
    return jsonify(events)

@app.route('/api/events/<int:event_id>', methods=['DELETE'])
def delete_event_api(event_id):
    """Elimina un evento e intenta borrar sus archivos asociados."""
    database.delete_event(event_id)
    return jsonify({'success': True})

@app.route('/api/live_alerts', methods=['GET'])
def live_alerts_api():
    """Devuelve las últimas alertas en memoria para notificación en vivo."""
    since_id = request.args.get('since_id', type=int, default=0)
    alerts = [a for a in recent_alerts if a.get('event_id', 0) > since_id]
    return jsonify(alerts)


# ==========================================
# API REST: ESTADÍSTICAS DEL SISTEMA
# ==========================================

@app.route('/api/system_stats', methods=['GET'])
def system_stats_api():
    """Métricas en tiempo real de uso de hardware y almacenamiento."""
    try:
        cpu_percent = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage(BASE_DIR)

        # Calcular tamaño del directorio recordings
        rec_size_bytes = 0
        for dirpath, dirnames, filenames in os.walk(RECORDINGS_DIR):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    rec_size_bytes += os.path.getsize(fp)

        rec_size_mb = round(rec_size_bytes / (1024 * 1024), 2)
        today_events = database.get_today_events_count()

        return jsonify({
            'cpu_usage': cpu_percent,
            'ram_usage': mem.percent,
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'recordings_mb': rec_size_mb,
            'active_cameras': sum(1 for c in camera_manager.cameras.values() if c.is_running),
            'total_cameras': len(camera_manager.cameras),
            'today_events': today_events
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Iniciando Sistema de Monitoreo de Video...")
    print("Panel de Control disponible en: http://127.0.0.1:5000")
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    finally:
        camera_manager.shutdown_all()

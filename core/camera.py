import time
import threading
import math
from datetime import datetime
from .detector import MotionDetector
from .recorder import VideoRecorder
from . import database

try:
    import cv2
    import numpy as np
    HAVE_CV2 = True
except ImportError:
    cv2 = None
    np = None
    HAVE_CV2 = False


class CameraStream:
    def __init__(self, camera_id, name, source_type, source_url, motion_enabled=True,
                 sensitivity=30, record_on_motion=True, recorder=None, alert_callback=None):
        self.camera_id = camera_id
        self.name = name
        self.source_type = source_type
        self.source_url = source_url
        self.motion_enabled = motion_enabled
        self.record_on_motion = record_on_motion
        self.recorder = recorder or VideoRecorder()
        self.alert_callback = alert_callback

        self.detector = MotionDetector(sensitivity=sensitivity)
        self.capture = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()

        self.current_frame = None
        self.current_bytes = None
        self.content_type = 'image/jpeg' if HAVE_CV2 else 'image/svg+xml'
        self.fps = 0.0
        self.is_online = False
        self.has_motion = False
        self.synth_step = 0

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.5)
        if self.capture and HAVE_CV2:
            try:
                self.capture.release()
            except Exception:
                pass
            self.capture = None
        self.is_online = False

    def _init_capture(self):
        if not HAVE_CV2 or self.source_type == 'synthetic':
            return True

        source = self.source_url
        if self.source_type == 'webcam':
            try:
                source = int(self.source_url)
                self.capture = cv2.VideoCapture(source, cv2.CAP_DSHOW)
            except Exception:
                self.capture = cv2.VideoCapture(source)
        else:
            self.capture = cv2.VideoCapture(source)

        if self.capture and self.capture.isOpened():
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.is_online = True
            return True
        else:
            self.is_online = False
            return False

    def _generate_synthetic_svg(self):
        """Genera un fotograma vectorial de alta definición para simulación CCTV sin dependencias externas."""
        self.synth_step += 1
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        w, h = 640, 480

        cycle = (self.synth_step % 120)
        has_target = 35 < cycle < 85
        target_x = int(60 + (cycle - 35) * 10) if has_target else 300
        target_y = int(240 + math.sin(cycle * 0.2) * 20) if has_target else 240

        is_rec = self.recorder.is_recording(self.camera_id)
        status_color = "#ef4444" if is_rec else ("#f59e0b" if has_target else "#10b981")
        status_text = "REC ●" if is_rec else ("ALERTA: INTRUSIÓN" if has_target else "EN VIVO [SEGURO]")

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
            <defs>
                <linearGradient id="bg" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#0b0f17"/>
                    <stop offset="45%" stop-color="#141c2b"/>
                    <stop offset="100%" stop-color="#090d14"/>
                </linearGradient>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1e293b" stroke-width="0.8"/>
                </pattern>
            </defs>
            <rect width="{w}" height="{h}" fill="url(#bg)"/>
            <rect width="{w}" height="{h}" fill="url(#grid)"/>

            <!-- Perspectiva y estructura de pasillo de seguridad -->
            <polygon points="120,120 520,120 640,480 0,480" fill="none" stroke="#334155" stroke-width="1.5"/>
            <line x1="120" y1="120" x2="260" y2="480" stroke="#1e293b" stroke-width="1"/>
            <line x1="520" y1="120" x2="380" y2="480" stroke="#1e293b" stroke-width="1"/>

            <!-- Puerta de acceso al fondo -->
            <rect x="290" y="80" width="60" height="100" fill="#1e293b" stroke="#475569" stroke-width="1"/>
            <circle cx="340" cy="130" r="3" fill="#94a3b8"/>

            <!-- Objetivo detectado si hay movimiento en el ciclo -->
            {f'''
            <g>
                <rect x="{target_x - 15}" y="{target_y - 20}" width="40" height="75" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="4"/>
                <circle cx="{target_x + 5}" cy="{target_y - 30}" r="12" fill="#ef4444" opacity="0.85"/>
                <rect x="{target_x - 8}" y="{target_y - 15}" width="26" height="50" rx="4" fill="#ef4444" opacity="0.75"/>
                <text x="{target_x - 30}" y="{target_y - 40}" fill="#ef4444" font-family="monospace" font-size="11" font-weight="bold">OBJETO DETECTADO</text>
            </g>
            ''' if has_target else ''}

            <!-- Barra Superior On-Screen Display (OSD) -->
            <rect x="0" y="0" width="{w}" height="32" fill="#05070a" opacity="0.8"/>
            <text x="14" y="21" fill="#f8fafc" font-family="monospace" font-size="13" font-weight="bold">CAM: {self.name.upper()}</text>
            <text x="440" y="21" fill="#00ffcc" font-family="monospace" font-size="13">{now_str}</text>

            <!-- Barra Inferior OSD -->
            <rect x="0" y="{h - 26}" width="{w}" height="26" fill="#05070a" opacity="0.8"/>
            <text x="14" y="{h - 9}" fill="#94a3b8" font-family="monospace" font-size="12">FPS: {self.fps:.1f}</text>
            <text x="460" y="{h - 9}" fill="{status_color}" font-family="monospace" font-size="12" font-weight="bold">{status_text}</text>

            <!-- Retículas en las esquinas estilo militar/CCTV -->
            <path d="M 12 44 L 28 44 M 12 44 L 12 60" stroke="#64748b" stroke-width="1.5" fill="none"/>
            <path d="M 628 44 L 612 44 M 628 44 L 628 60" stroke="#64748b" stroke-width="1.5" fill="none"/>
            <path d="M 12 444 L 28 444 M 12 444 L 12 428" stroke="#64748b" stroke-width="1.5" fill="none"/>
            <path d="M 628 444 L 612 444 M 628 444 L 628 428" stroke="#64748b" stroke-width="1.5" fill="none"/>
        </svg>"""
        return svg.encode('utf-8')

    def _capture_loop(self):
        consecutive_failures = 0
        frame_counter = 0
        fps_timer = time.time()

        if HAVE_CV2:
            self._init_capture()

        while self.is_running:
            if not HAVE_CV2 or self.source_type == 'synthetic' or not self.is_online:
                time.sleep(0.04) # ~25 FPS
                raw_frame = self._generate_synthetic_svg()
                self.content_type = 'image/svg+xml'
            else:
                ret, frame = self.capture.read()
                if not ret or frame is None:
                    consecutive_failures += 1
                    time.sleep(0.1)
                    if consecutive_failures > 15:
                        self.is_online = False
                    continue
                else:
                    consecutive_failures = 0
                    self.is_online = True
                    raw_frame = frame
                    self.content_type = 'image/jpeg'

            # Procesamiento de movimiento
            has_motion = False
            is_new_alert = False
            annotated_frame = raw_frame

            if self.motion_enabled:
                has_motion, is_new_alert, annotated_frame, _ = self.detector.process_frame(raw_frame)
            self.has_motion = has_motion

            # Si se dispara una alerta de movimiento
            if is_new_alert:
                snap_path = self.recorder.save_snapshot(self.camera_id, annotated_frame)
                video_path = None

                if self.record_on_motion and not self.recorder.is_recording(self.camera_id):
                    motion_rec_sec = int(database.get_setting('motion_record_seconds', '10'))
                    video_path = self.recorder.start_recording(self.camera_id, self.name, fps=15.0, duration=motion_rec_sec)

                event_id = database.log_event(
                    camera_id=self.camera_id,
                    camera_name=self.name,
                    event_type='motion',
                    snapshot_path=snap_path,
                    video_path=video_path,
                    details="Movimiento detectado en zona monitoreada"
                )

                if self.alert_callback:
                    self.alert_callback({
                        'event_id': event_id,
                        'camera_id': self.camera_id,
                        'camera_name': self.name,
                        'event_type': 'motion',
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'snapshot_path': snap_path,
                        'video_path': video_path
                    })

            # Grabación activa
            if self.recorder.is_recording(self.camera_id):
                self.recorder.write_frame(self.camera_id, annotated_frame)

            # Cálculo de FPS
            frame_counter += 1
            now = time.time()
            if now - fps_timer >= 1.0:
                self.fps = frame_counter / (now - fps_timer)
                frame_counter = 0
                fps_timer = now

            # Codificación
            if HAVE_CV2 and isinstance(annotated_frame, np.ndarray):
                ret_encode, buffer = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ret_encode:
                    with self.lock:
                        self.current_frame = annotated_frame
                        self.current_bytes = buffer.tobytes()
            else:
                with self.lock:
                    self.current_frame = annotated_frame
                    self.current_bytes = annotated_frame

        if self.capture and HAVE_CV2:
            self.capture.release()

    def get_frame_bytes(self):
        with self.lock:
            return self.current_bytes, self.content_type

    def get_snapshot(self):
        with self.lock:
            return self.current_frame


class CameraManager:
    def __init__(self):
        self.cameras = {}
        self.recorder = VideoRecorder()
        self.alert_subscribers = []
        self.lock = threading.Lock()

    def register_alert_subscriber(self, callback):
        self.alert_subscribers.append(callback)

    def _on_camera_alert(self, event_data):
        for sub in self.alert_subscribers:
            try:
                sub(event_data)
            except Exception:
                pass

    def load_cameras_from_db(self):
        with self.lock:
            for cam in self.cameras.values():
                cam.stop()
            self.cameras.clear()

            db_cams = database.get_cameras(active_only=False)
            for row in db_cams:
                cam = CameraStream(
                    camera_id=row['id'],
                    name=row['name'],
                    source_type=row['source_type'],
                    source_url=row['source_url'],
                    motion_enabled=bool(row['motion_enabled']),
                    sensitivity=row['sensitivity'],
                    record_on_motion=bool(row['record_on_motion']),
                    recorder=self.recorder,
                    alert_callback=self._on_camera_alert
                )
                if row['is_active']:
                    cam.start()
                self.cameras[row['id']] = cam

    def get_camera(self, camera_id):
        return self.cameras.get(camera_id)

    def get_all_status(self):
        res = []
        for cam_id, cam in self.cameras.items():
            res.append({
                'id': cam.camera_id,
                'name': cam.name,
                'source_type': cam.source_type,
                'source_url': cam.source_url,
                'is_running': cam.is_running,
                'is_online': cam.is_online or cam.source_type == 'synthetic' or not HAVE_CV2,
                'fps': round(cam.fps, 1),
                'motion_enabled': cam.motion_enabled,
                'has_motion': cam.has_motion,
                'is_recording': self.recorder.is_recording(cam.camera_id)
            })
        return res

    def start_camera(self, camera_id):
        cam = self.cameras.get(camera_id)
        if cam:
            cam.start()
            database.update_camera(camera_id, is_active=1)

    def stop_camera(self, camera_id):
        cam = self.cameras.get(camera_id)
        if cam:
            cam.stop()
            database.update_camera(camera_id, is_active=0)

    def trigger_snapshot(self, camera_id):
        cam = self.cameras.get(camera_id)
        if not cam:
            return None
        frame = cam.get_snapshot()
        snap_path = self.recorder.save_snapshot(camera_id, frame)
        event_id = database.log_event(
            camera_id=camera_id,
            camera_name=cam.name,
            event_type='snapshot',
            snapshot_path=snap_path,
            details="Captura manual tomada por el operador"
        )
        return {'event_id': event_id, 'snapshot_path': snap_path}

    def toggle_recording(self, camera_id):
        cam = self.cameras.get(camera_id)
        if not cam:
            return {'recording': False}

        if self.recorder.is_recording(camera_id):
            video_path = self.recorder.stop_recording(camera_id)
            database.log_event(
                camera_id=camera_id,
                camera_name=cam.name,
                event_type='recording',
                video_path=video_path,
                details="Grabación manual finalizada"
            )
            return {'recording': False, 'video_path': video_path}
        else:
            video_path = self.recorder.start_recording(camera_id, cam.name)
            return {'recording': True, 'video_path': video_path}

    def shutdown_all(self):
        for cam in self.cameras.values():
            cam.stop()

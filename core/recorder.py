import os
import time
import threading
from datetime import datetime

try:
    import cv2
    HAVE_CV2 = True
except ImportError:
    cv2 = None
    HAVE_CV2 = False

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SNAPSHOT_DIR = os.path.join(BASE_DIR, "recordings", "snapshots")
VIDEO_DIR = os.path.join(BASE_DIR, "recordings", "videos")

os.makedirs(SNAPSHOT_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

class VideoRecorder:
    def __init__(self):
        self.active_recordings = {}
        self.lock = threading.Lock()

    def save_snapshot(self, camera_id, frame):
        """Guarda una captura instantánea en disco."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]

        if HAVE_CV2 and frame is not None and not isinstance(frame, (str, bytes)):
            filename = f"snap_{camera_id}_{timestamp}.jpg"
            filepath = os.path.join(SNAPSHOT_DIR, filename)
            cv2.imwrite(filepath, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
            return f"/recordings/snapshots/{filename}"
        else:
            # Fallback en formato SVG vector o simulado
            filename = f"snap_{camera_id}_{timestamp}.svg"
            filepath = os.path.join(SNAPSHOT_DIR, filename)
            svg_content = frame if isinstance(frame, (str, bytes)) else f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480">
                <rect width="640" height="480" fill="#0d1117"/>
                <text x="30" y="40" fill="#00ffcc" font-family="monospace" font-size="16">CAPTURA: {camera_id.upper()}</text>
                <text x="30" y="70" fill="#888" font-family="monospace" font-size="14">FECHA: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</text>
                <rect x="180" y="160" width="280" height="160" fill="#1f2937" stroke="#ef4444" stroke-width="2"/>
                <text x="210" y="245" fill="#ef4444" font-family="sans-serif" font-size="18" font-weight="bold">INTRUSION REGISTRADA</text>
            </svg>"""
            if isinstance(svg_content, bytes):
                svg_content = svg_content.decode('utf-8', errors='ignore')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            return f"/recordings/snapshots/{filename}"

    def start_recording(self, camera_id, camera_name, fps=15.0, duration=None):
        """Inicia la grabación de un clip de video."""
        with self.lock:
            if camera_id in self.active_recordings:
                return self.active_recordings[camera_id]['video_rel_path']

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rec_{camera_id}_{timestamp}.mp4"
            filepath = os.path.join(VIDEO_DIR, filename)
            rel_path = f"/recordings/videos/{filename}"

            self.active_recordings[camera_id] = {
                'camera_name': camera_name,
                'filepath': filepath,
                'video_rel_path': rel_path,
                'writer': None,
                'fps': fps,
                'start_time': time.time(),
                'duration': duration,
                'frame_size': None,
                'frames_count': 0
            }
            return rel_path

    def write_frame(self, camera_id, frame):
        """Escribe un frame al archivo de video."""
        if not HAVE_CV2 or frame is None or isinstance(frame, (str, bytes)):
            return

        with self.lock:
            rec = self.active_recordings.get(camera_id)
            if not rec:
                return

            h, w = frame.shape[:2]
            if rec['writer'] is None:
                rec['frame_size'] = (w, h)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                rec['writer'] = cv2.VideoWriter(rec['filepath'], fourcc, rec['fps'], (w, h))

            rec['writer'].write(frame)
            rec['frames_count'] += 1

            if rec['duration'] and (time.time() - rec['start_time'] >= rec['duration']):
                threading.Thread(target=self.stop_recording, args=(camera_id,)).start()

    def stop_recording(self, camera_id):
        """Detiene y finaliza la grabación de video."""
        with self.lock:
            rec = self.active_recordings.pop(camera_id, None)
            if rec and rec['writer']:
                rec['writer'].release()
                return rec['video_rel_path']
            elif rec:
                return rec['video_rel_path']
        return None

    def is_recording(self, camera_id):
        with self.lock:
            return camera_id in self.active_recordings

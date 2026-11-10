import time

try:
    import cv2
    import numpy as np
    HAVE_CV2 = True
except ImportError:
    cv2 = None
    np = None
    HAVE_CV2 = False

class MotionDetector:
    def __init__(self, sensitivity=30, min_area=800, cooldown_seconds=4):
        self.sensitivity = sensitivity
        self.min_area = min_area
        self.cooldown_seconds = cooldown_seconds
        self.last_alert_time = 0
        self.prev_gray = None
        self.step_counter = 0

    def set_sensitivity(self, sensitivity):
        self.sensitivity = max(5, min(100, sensitivity))

    def process_frame(self, frame, draw_boxes=True):
        """
        Procesa el frame y determina si hay movimiento relevante.
        Retorna: (has_motion, is_new_alert, annotated_frame, contours_count)
        """
        current_time = time.time()

        # Si OpenCV no está disponible, o el frame es bytes/SVG (no array numpy), usar simulación
        if not HAVE_CV2 or frame is None or isinstance(frame, (str, bytes)):
            self.step_counter += 1
            # Simular intrusión cíclica cada 8-12 segundos para pruebas
            cycle = (self.step_counter % 120)
            has_motion = 35 < cycle < 75
            is_new_alert = False

            if has_motion and (current_time - self.last_alert_time >= self.cooldown_seconds):
                is_new_alert = True
                self.last_alert_time = current_time

            return has_motion, is_new_alert, frame, 1 if has_motion else 0

        # Modo OpenCV nativo
        h, w = frame.shape[:2]
        small_frame = cv2.resize(frame, (min(640, w), min(360, h)))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        has_motion = False
        is_new_alert = False
        annotated_frame = frame.copy()
        valid_contours = []

        if self.prev_gray is None:
            self.prev_gray = gray
            return False, False, annotated_frame, 0

        frame_diff = cv2.absdiff(self.prev_gray, gray)
        thresh_val = int(5 + (100 - self.sensitivity) * 0.55)
        _, thresh = cv2.threshold(frame_diff, thresh_val, 255, cv2.THRESH_BINARY)
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        scale_x = w / small_frame.shape[1]
        scale_y = h / small_frame.shape[0]

        for c in contours:
            area = cv2.contourArea(c) * (scale_x * scale_y)
            if area > self.min_area:
                has_motion = True
                valid_contours.append(c)
                if draw_boxes:
                    (x, y, cw, ch) = cv2.boundingRect(c)
                    rx, ry, rw, rh = int(x * scale_x), int(y * scale_y), int(cw * scale_x), int(ch * scale_y)
                    cv2.rectangle(annotated_frame, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), 2)
                    cv2.putText(annotated_frame, "MOVIMIENTO DETECTADO", (rx, max(20, ry - 7)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1, cv2.LINE_AA)

        self.prev_gray = gray

        if has_motion and (current_time - self.last_alert_time >= self.cooldown_seconds):
            is_new_alert = True
            self.last_alert_time = current_time

        return has_motion, is_new_alert, annotated_frame, len(valid_contours)

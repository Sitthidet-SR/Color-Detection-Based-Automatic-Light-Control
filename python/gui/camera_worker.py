"""อ่านภาพจากกล้องและตรวจจับสีใน QThread เพื่อไม่ให้หน้าจอค้าง"""
import copy
import time

import cv2
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

from core.detector import ColorDetector, StabilityFilter, annotate, roi_rect

VIEW_ORIGINAL, VIEW_GREEN, VIEW_RED = "original", "green", "red"


class CameraWorker(QThread):
    frame_ready = pyqtSignal(QImage)
    detection = pyqtSignal(dict)
    snapshot_saved = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, camera_index, cfg, parent=None):
        super().__init__(parent)
        self.camera_index = camera_index
        self._cfg = copy.deepcopy(cfg)
        self._new_cfg = None
        self._running = False
        self._snapshot_path = None
        # ค่าที่หน้าจอปรับได้ระหว่างทำงาน
        self.view = VIEW_ORIGINAL
        self.use_roi = True
        self.show_hud = True
        self.led_text = "?"

    def set_config(self, cfg):
        self._new_cfg = copy.deepcopy(cfg)

    def request_snapshot(self, path):
        self._snapshot_path = str(path)

    def stop(self):
        self._running = False
        self.wait(3000)

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            self.error.emit(f"เปิดกล้อง {self.camera_index} ไม่ได้")
            return
        detector = ColorDetector(self._cfg)
        stability = StabilityFilter(self._cfg["stable_frames"])
        fps, last = 0.0, time.monotonic()
        self._running = True

        while self._running:
            if self._new_cfg is not None:
                self._cfg, self._new_cfg = self._new_cfg, None
                detector.update(self._cfg)
                stability.n = self._cfg["stable_frames"]

            ok, frame = cap.read()
            if not ok:
                self.error.emit("อ่านภาพจากกล้องไม่ได้")
                break

            h, w = frame.shape[:2]
            roi = roi_rect(self._cfg, w, h) if self.use_roi else None
            det = detector.detect(frame, roi)
            stable_color = stability.update(det.color)

            now = time.monotonic()
            fps = 0.9 * fps + 0.1 * (1.0 / max(now - last, 1e-6)) if fps else 1.0 / max(now - last, 1e-6)
            last = now

            if self.view == VIEW_GREEN:
                out = cv2.cvtColor(det.green_mask, cv2.COLOR_GRAY2BGR)
            elif self.view == VIEW_RED:
                out = cv2.cvtColor(det.red_mask, cv2.COLOR_GRAY2BGR)
            else:
                out = frame.copy()
            hud = None
            if self.show_hud:
                hud = [f"FPS {fps:.1f}", f"LED: {self.led_text}",
                       f"Stable {stability.count}/{stability.n}"]
            annotate(out, det, roi, hud)

            if self._snapshot_path:
                path, self._snapshot_path = self._snapshot_path, None
                if cv2.imwrite(path, out):
                    self.snapshot_saved.emit(path)

            rgb = cv2.cvtColor(out, cv2.COLOR_BGR2RGB)
            image = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()
            self.frame_ready.emit(image)
            self.detection.emit({
                "color": det.color,
                "area": det.area,
                "stable_color": stable_color,
                "stable_count": stability.count,
                "stable_needed": stability.n,
            })

        cap.release()

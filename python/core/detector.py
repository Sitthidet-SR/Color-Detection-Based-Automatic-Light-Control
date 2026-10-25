"""ตรวจจับสีเขียว/แดงด้วย HSV Color Space (ไม่ขึ้นกับ GUI)"""
import copy
from dataclasses import dataclass

import cv2
import numpy as np

GREEN = "green"
RED = "red"

# สีสำหรับวาดบนภาพ (BGR)
DRAW_COLORS = {GREEN: (94, 197, 34), RED: (68, 68, 239)}

_KERNEL = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))


@dataclass
class Detection:
    color: str | None          # GREEN, RED หรือ None
    area: float
    bbox: tuple | None         # (x, y, w, h)
    green_mask: np.ndarray
    red_mask: np.ndarray


def _in_range(hsv, h, s, v):
    lower = np.array([h[0], s[0], v[0]], dtype=np.uint8)
    upper = np.array([h[1], s[1], v[1]], dtype=np.uint8)
    return cv2.inRange(hsv, lower, upper)


def _clean(mask):
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, _KERNEL)
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _KERNEL)


def roi_rect(cfg, width, height):
    """แปลง ROI จากสัดส่วนเป็นพิกเซล (x1, y1, x2, y2)"""
    x1, y1, x2, y2 = cfg["roi"]
    return int(x1 * width), int(y1 * height), int(x2 * width), int(y2 * height)


class ColorDetector:
    def __init__(self, cfg):
        self.update(cfg)

    def update(self, cfg):
        self.cfg = copy.deepcopy(cfg)

    def masks(self, hsv):
        g, r = self.cfg[GREEN], self.cfg[RED]
        green = _in_range(hsv, g["h"], g["s"], g["v"])
        red = cv2.bitwise_or(_in_range(hsv, r["h1"], r["s"], r["v"]),
                             _in_range(hsv, r["h2"], r["s"], r["v"]))
        return _clean(green), _clean(red)

    def detect(self, frame, roi=None):
        """คืนสีที่พบ (เลือกสีที่มีพื้นที่ใหญ่กว่า ถ้าพบทั้งสองสี)"""
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        green, red = self.masks(hsv)

        if roi is not None:
            x1, y1, x2, y2 = roi
            keep = np.zeros(green.shape, dtype=np.uint8)
            keep[y1:y2, x1:x2] = 255
            green = cv2.bitwise_and(green, keep)
            red = cv2.bitwise_and(red, keep)

        best = (None, 0.0, None)
        for color, mask in ((GREEN, green), (RED, red)):
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue
            biggest = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(biggest)
            if area >= self.cfg["min_area"] and area > best[1]:
                best = (color, area, cv2.boundingRect(biggest))
        return Detection(best[0], best[1], best[2], green, red)


class StabilityFilter:
    """กันไฟกระพริบ: ยืนยันสีเมื่อพบสีเดียวกันติดกันครบ n เฟรม"""

    def __init__(self, n):
        self.n = n
        self.color = None
        self.count = 0

    def update(self, color):
        if color is None:
            self.color, self.count = None, 0
            return None
        if color == self.color:
            self.count = min(self.count + 1, self.n)
        else:
            self.color, self.count = color, 1
        return color if self.count >= self.n else None


def annotate(img, det, roi=None, hud_lines=None):
    """วาด ROI, กรอบวัตถุ, ชื่อสี และ HUD ลงบนภาพ (แก้ไขภาพเดิม)"""
    if roi is not None:
        _dashed_rect(img, roi, (150, 150, 150))
    if det.color and det.bbox:
        x, y, w, h = det.bbox
        color = DRAW_COLORS[det.color]
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
        label = f"{det.color.upper()} - {int(det.area):,} px"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        ty = max(y - 8, th + 8)
        cv2.rectangle(img, (x, ty - th - 8), (x + tw + 12, ty + 4), color, -1)
        cv2.putText(img, label, (x + 6, ty - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (20, 20, 20), 2)
    if hud_lines:
        line_h = 22
        box_w = max(cv2.getTextSize(t, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0][0] for t in hud_lines) + 20
        overlay = img.copy()
        cv2.rectangle(overlay, (10, 10), (10 + box_w, 18 + line_h * len(hud_lines)), (20, 20, 20), -1)
        cv2.addWeighted(overlay, 0.65, img, 0.35, 0, img)
        for i, text in enumerate(hud_lines):
            cv2.putText(img, text, (20, 32 + i * line_h), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (235, 235, 235), 1)
    return img


def _dashed_rect(img, rect, color, dash=10):
    x1, y1, x2, y2 = rect
    for x in range(x1, x2, dash * 2):
        cv2.line(img, (x, y1), (min(x + dash, x2), y1), color, 1)
        cv2.line(img, (x, y2), (min(x + dash, x2), y2), color, 1)
    for y in range(y1, y2, dash * 2):
        cv2.line(img, (x1, y), (x1, min(y + dash, y2)), color, 1)
        cv2.line(img, (x2, y), (x2, min(y + dash, y2)), color, 1)

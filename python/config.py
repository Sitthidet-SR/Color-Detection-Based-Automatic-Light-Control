"""ค่าตั้งต้นของระบบ และการโหลด/บันทึก config.json"""
import copy
import json
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("config.json")

# ช่วง H ของ OpenCV คือ 0-180, S และ V คือ 0-255
DEFAULTS = {
    "green": {"h": [35, 85], "s": [80, 255], "v": [60, 255]},
    # สีแดงอยู่ทั้งต้นและปลายวง Hue จึงใช้ 2 ช่วง
    "red": {"h1": [0, 10], "h2": [170, 180], "s": [100, 255], "v": [70, 255]},
    "min_area": 1500,       # พื้นที่ contour ขั้นต่ำ (px) ที่นับว่าพบสี
    "stable_frames": 5,     # ต้องพบสีเดียวกันติดกันกี่เฟรมจึงสั่งไฟ
    "roi": [0.2, 0.15, 0.8, 0.85],  # กรอบ ROI เป็นสัดส่วนของภาพ (x1, y1, x2, y2)
    "baud": 115200,
}


def _merge(base, override):
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        elif key in base:
            base[key] = value
    return base


def defaults():
    return copy.deepcopy(DEFAULTS)


def load():
    cfg = defaults()
    if CONFIG_PATH.exists():
        try:
            _merge(cfg, json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    return cfg


def save(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

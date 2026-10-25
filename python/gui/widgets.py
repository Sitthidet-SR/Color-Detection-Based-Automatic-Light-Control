"""วิดเจ็ตเสริม: slider แบบเลือกช่วง และไฟ LED จำลอง"""
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QWidget

from . import styles


class RangeSlider(QWidget):
    """slider 2 หัว สำหรับเลือกค่า min-max"""

    rangeChanged = pyqtSignal(int, int)
    HANDLE = 16

    def __init__(self, minimum, maximum, low, high, color=styles.GREEN, parent=None):
        super().__init__(parent)
        self._min, self._max = minimum, maximum
        self._low, self._high = low, high
        self._color = QColor(color)
        self._drag = None
        self.setMinimumHeight(24)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def values(self):
        return self._low, self._high

    def setValues(self, low, high):
        low, high = max(self._min, min(low, high)), min(self._max, max(low, high))
        if (low, high) != (self._low, self._high):
            self._low, self._high = low, high
            self.update()
            self.rangeChanged.emit(low, high)

    def _span(self):
        r = self.HANDLE / 2
        return r, self.width() - r

    def _to_x(self, value):
        left, right = self._span()
        return left + (value - self._min) / (self._max - self._min) * (right - left)

    def _to_value(self, x):
        left, right = self._span()
        ratio = min(max((x - left) / (right - left), 0.0), 1.0)
        return round(self._min + ratio * (self._max - self._min))

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cy = self.height() / 2
        left, right = self._span()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#2A3441"))
        p.drawRoundedRect(QRectF(left, cy - 2, right - left, 4), 2, 2)
        x1, x2 = self._to_x(self._low), self._to_x(self._high)
        p.setBrush(self._color)
        p.drawRoundedRect(QRectF(x1, cy - 2, x2 - x1, 4), 2, 2)
        p.setPen(QPen(self._color, 2))
        p.setBrush(QColor("white"))
        r = self.HANDLE / 2 - 1
        for x in (x1, x2):
            p.drawEllipse(QPointF(x, cy), r, r)

    def mousePressEvent(self, event):
        x = event.position().x()
        d_low, d_high = abs(x - self._to_x(self._low)), abs(x - self._to_x(self._high))
        self._drag = "low" if d_low < d_high or (d_low == d_high and x < self._to_x(self._low)) else "high"
        self.mouseMoveEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag is None:
            return
        value = self._to_value(event.position().x())
        if self._drag == "low":
            self.setValues(min(value, self._high), self._high)
        else:
            self.setValues(self._low, max(value, self._low))

    def mouseReleaseEvent(self, _event):
        self._drag = None


class RangeRow(QWidget):
    """แถว: ชื่อค่า | RangeSlider | กล่องแสดงค่า"""

    rangeChanged = pyqtSignal(int, int)

    def __init__(self, name, minimum, maximum, values, color, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        label = QLabel(name)
        label.setFixedWidth(52)
        self.slider = RangeSlider(minimum, maximum, *values, color=color)
        self.value_label = QLabel()
        self.value_label.setObjectName("rangeValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)
        self.slider.rangeChanged.connect(self._changed)
        self._show(*values)

    def _show(self, low, high):
        self.value_label.setText(f"{low}-{high}")

    def _changed(self, low, high):
        self._show(low, high)
        self.rangeChanged.emit(low, high)

    def setValues(self, low, high):
        self.slider.setValues(low, high)
        self._show(low, high)


class LedIndicator(QWidget):
    """วงกลมแสดงสถานะ LED (เขียว = เปิด, เทา = ปิด)"""

    def __init__(self, size=84, parent=None):
        super().__init__(parent)
        self._on = False
        self.setFixedSize(size, size)

    def setOn(self, on):
        self._on = on
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        grad = QRadialGradient(rect.center() - QPointF(rect.width() * 0.15, rect.height() * 0.15),
                               rect.width() * 0.6)
        if self._on:
            grad.setColorAt(0, QColor("#86EFAC"))
            grad.setColorAt(0.55, QColor(styles.GREEN))
            grad.setColorAt(1, QColor("#15803D"))
        else:
            grad.setColorAt(0, QColor("#4B5563"))
            grad.setColorAt(1, QColor("#1F2937"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(grad)
        p.drawEllipse(rect)

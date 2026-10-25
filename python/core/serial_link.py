"""สื่อสารกับ ESP32 ผ่าน Serial (อ่านแบบ non-blocking ด้วย QTimer)"""
import serial
from serial.tools import list_ports
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

RESET_WAIT_MS = 2000  # ESP32 รีเซ็ตเมื่อเปิดพอร์ต ต้องรอก่อนส่งคำสั่ง


class SerialLink(QObject):
    line_received = pyqtSignal(str)
    connected_changed = pyqtSignal(bool)
    ready_changed = pyqtSignal()  # บอร์ดพร้อมรับคำสั่งแล้ว
    log = pyqtSignal(str, str)  # (ชนิด: info/tx/rx/error, ข้อความ)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ser = None
        self._buf = b""
        self._pending = None
        self.ready = False
        self.port = ""
        self.baud = 0
        self._timer = QTimer(self)
        self._timer.setInterval(20)
        self._timer.timeout.connect(self._poll)

    @staticmethod
    def available_ports():
        return [p.device for p in sorted(list_ports.comports())]

    @property
    def is_open(self):
        return self._ser is not None

    def open(self, port, baud):
        self.close()
        try:
            self._ser = serial.Serial(port, baud, timeout=0)
        except serial.SerialException as exc:
            self.log.emit("error", f"เปิดพอร์ต {port} ไม่ได้: {exc}")
            return False
        self.port, self.baud = port, baud
        self._buf = b""
        self.ready = False
        self.log.emit("info", f"Port {port} opened @{baud}, waiting 2s for reset…")
        QTimer.singleShot(RESET_WAIT_MS, self._mark_ready)
        self._timer.start()
        self.connected_changed.emit(True)
        return True

    def close(self):
        if self._ser is None:
            return
        self._timer.stop()
        try:
            self._ser.close()
        except serial.SerialException:
            pass
        self._ser = None
        self.ready = False
        self._pending = None
        self.log.emit("info", f"Port {self.port} closed")
        self.connected_changed.emit(False)

    def send(self, cmd, note=""):
        """ส่งคำสั่ง 1 ตัวอักษร ถ้าบอร์ดยังไม่พร้อมจะเก็บไว้ส่งทีหลัง (เก็บเฉพาะคำสั่งล่าสุด)"""
        if self._ser is None:
            return False
        if not self.ready:
            self._pending = (cmd, note)
            return True
        try:
            self._ser.write(f"{cmd}\n".encode("ascii"))
        except serial.SerialException as exc:
            self.log.emit("error", f"ส่งคำสั่งไม่สำเร็จ: {exc}")
            self.close()
            return False
        self.log.emit("tx", f"{cmd}{note}")
        return True

    def _mark_ready(self):
        if self._ser is None or self.ready:
            return
        self.ready = True
        self.ready_changed.emit()
        if self._pending:
            cmd, note = self._pending
            self._pending = None
            self.send(cmd, note)

    def _poll(self):
        if self._ser is None:
            return
        try:
            waiting = self._ser.in_waiting
            if waiting:
                self._buf += self._ser.read(waiting)
        except (serial.SerialException, OSError) as exc:
            self.log.emit("error", f"การเชื่อมต่อขาด: {exc}")
            self.close()
            return
        while b"\n" in self._buf:
            raw, self._buf = self._buf.split(b"\n", 1)
            line = raw.decode("ascii", errors="replace").strip()
            if not line:
                continue
            self.log.emit("rx", line)
            if line == "READY":
                self._mark_ready()
            self.line_received.emit(line)

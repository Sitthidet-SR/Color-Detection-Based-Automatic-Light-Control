"""หน้าต่างหลักของโปรแกรม"""
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QMainWindow, QPlainTextEdit, QProgressBar, QPushButton,
    QRadioButton, QSizePolicy, QSpinBox, QTabWidget, QToolBar, QToolButton,
    QVBoxLayout, QWidget,
)

import config
from core.detector import GREEN, RED
from core.serial_link import SerialLink

from . import styles
from .camera_worker import VIEW_GREEN, VIEW_ORIGINAL, VIEW_RED, CameraWorker
from .widgets import LedIndicator, RangeRow

SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "snapshots"
BAUD_RATES = ["9600", "57600", "115200", "230400"]
COLOR_NAMES = {GREEN: ("Green", styles.GREEN), RED: ("Red", styles.RED)}
LOG_COLORS = {"tx": styles.TX_BLUE, "rx": styles.GREEN, "error": styles.RED, "info": styles.TEXT}


def make_card(title, header_widget=None):
    """กล่องพื้นเข้มพร้อมหัวข้อ คืนค่า (frame, layout ของเนื้อหา)"""
    frame = QFrame()
    frame.setObjectName("card")
    outer = QVBoxLayout(frame)
    outer.setContentsMargins(14, 12, 14, 14)
    outer.setSpacing(10)
    header = QHBoxLayout()
    label = QLabel(title.upper())
    label.setObjectName("cardTitle")
    header.addWidget(label)
    header.addStretch(1)
    if header_widget is not None:
        header.addWidget(header_widget)
    outer.addLayout(header)
    return frame, outer


def color_icon(hex_color, size=10):
    pix = QPixmap(size, size)
    pix.fill(QColor(hex_color))
    return QIcon(pix)


def repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Color LED Control")
        self.resize(1280, 800)

        self.cfg = config.load()
        self.serial = SerialLink(self)
        self.worker = None
        self.auto_mode = True
        self.last_sent = None   # คำสั่งล่าสุดที่ส่ง ('G' / 'R')
        self.led_on = None      # สถานะที่ ESP32 ยืนยันแล้ว

        self._build_toolbar()
        self._build_central()
        self._build_statusbar()
        self._connect_signals()
        self.refresh_ports()
        self._update_led(None)
        self._update_connection_ui(False)
        QShortcut(QKeySequence("Q"), self, activated=self.close)

    # ---------- สร้างหน้าจอ ----------
    def _build_toolbar(self):
        bar = QToolBar()
        bar.setMovable(False)
        bar.setFloatable(False)
        self.addToolBar(bar)

        logo = QLabel()
        logo.setObjectName("appLogo")
        logo.setFixedSize(22, 22)
        title = QLabel("Color Detection LED Control")
        title.setObjectName("appTitle")
        bar.addWidget(logo)
        bar.addWidget(title)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bar.addWidget(spacer)

        self.camera_combo = QComboBox()
        self.camera_combo.addItems([f"Webcam {i}" for i in range(4)])
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(140)
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(BAUD_RATES)
        self.baud_combo.setCurrentText(str(self.cfg["baud"]))
        self.refresh_btn = QToolButton()
        self.refresh_btn.setText("⟳")
        self.refresh_btn.setToolTip("รีเฟรชรายการพอร์ต")
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setObjectName("connectBtn")
        self.connect_btn.setCheckable(True)
        self.conn_pill = QLabel()
        self.conn_pill.setObjectName("pill")

        for text, widget in (("Camera", self.camera_combo), ("Port", self.port_combo),
                             ("Baud", self.baud_combo)):
            label = QLabel(text)
            label.setObjectName("muted")
            bar.addWidget(label)
            bar.addWidget(widget)
        bar.addWidget(self.refresh_btn)
        bar.addWidget(self.connect_btn)
        bar.addWidget(self.conn_pill)

    def _build_central(self):
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(12)
        left.addWidget(self._build_camera_card(), 3)
        left.addWidget(self._build_log_card(), 1)

        right = QVBoxLayout()
        right.setSpacing(12)
        right.addWidget(self._build_led_card())
        right.addWidget(self._build_mode_card())
        right.addWidget(self._build_hsv_card(), 1)

        root.addLayout(left, 688)
        root.addLayout(right, 544)
        self.setCentralWidget(central)

    def _build_camera_card(self):
        seg = QFrame()
        seg.setObjectName("segmented")
        seg_layout = QHBoxLayout(seg)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(2)
        self.view_group = QButtonGroup(self)
        for i, (text, view) in enumerate((("Original", VIEW_ORIGINAL), ("Green mask", VIEW_GREEN),
                                          ("Red mask", VIEW_RED))):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("view", view)
            btn.setChecked(i == 0)
            self.view_group.addButton(btn)
            seg_layout.addWidget(btn)

        card, layout = make_card("Live Camera", seg)
        self.video = QLabel("กด Start Camera เพื่อเริ่มต้น")
        self.video.setObjectName("video")
        self.video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video.setMinimumSize(480, 300)
        self.video.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        layout.addWidget(self.video, 1)

        row = QHBoxLayout()
        self.start_btn = QPushButton("▶  Start Camera")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setCheckable(True)
        self.snapshot_btn = QPushButton("Snapshot")
        self.roi_check = QCheckBox("Show ROI")
        self.roi_check.setChecked(True)
        self.roi_check.setToolTip("ตรวจจับเฉพาะในกรอบ ROI (เอาออกเพื่อใช้ทั้งภาพ)")
        self.hud_check = QCheckBox("Show HUD")
        self.hud_check.setChecked(True)
        row.addWidget(self.start_btn)
        row.addWidget(self.snapshot_btn)
        row.addStretch(1)
        row.addWidget(self.roi_check)
        row.addWidget(self.hud_check)
        layout.addLayout(row)
        return card

    def _build_log_card(self):
        self.clear_btn = QPushButton("Clear")
        card, layout = make_card("Serial Log", self.clear_btn)
        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("log")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        self.log_view.setMinimumHeight(110)
        layout.addWidget(self.log_view)
        return card

    def _build_led_card(self):
        card, layout = make_card("LED Status")
        top = QHBoxLayout()
        top.setSpacing(16)
        self.led_indicator = LedIndicator(84)
        text_col = QVBoxLayout()
        text_col.addStretch(1)
        self.led_text = QLabel()
        self.led_text.setObjectName("ledText")
        self.led_sub = QLabel()
        self.led_sub.setObjectName("muted")
        text_col.addWidget(self.led_text)
        text_col.addWidget(self.led_sub)
        text_col.addStretch(1)
        top.addWidget(self.led_indicator)
        top.addLayout(text_col, 1)
        layout.addLayout(top)

        form = QFormLayout()
        form.setHorizontalSpacing(24)
        form.setVerticalSpacing(6)
        self.color_value = QLabel("—")
        self.area_value = QLabel("—")
        self.cmd_value = QLabel("—")
        self.cmd_value.setObjectName("mono")
        self.stable_value = QLabel("—")
        for key, value in (("Detected color", self.color_value), ("Contour area", self.area_value),
                           ("Last command", self.cmd_value), ("Stability", self.stable_value)):
            label = QLabel(key)
            label.setObjectName("formKey")
            form.addRow(label, value)
        layout.addLayout(form)
        self.stable_bar = QProgressBar()
        self.stable_bar.setTextVisible(False)
        self.stable_bar.setRange(0, self.cfg["stable_frames"])
        self.stable_bar.setValue(0)
        layout.addWidget(self.stable_bar)
        return card

    def _build_mode_card(self):
        card, layout = make_card("Control Mode")
        row = QHBoxLayout()
        self.auto_radio = QRadioButton("Auto (color)")
        self.manual_radio = QRadioButton("Manual")
        self.auto_radio.setChecked(True)
        mode_group = QButtonGroup(self)
        mode_group.addButton(self.auto_radio)
        mode_group.addButton(self.manual_radio)
        self.on_btn = QPushButton("Turn ON")
        self.off_btn = QPushButton("Turn OFF")
        row.addWidget(self.auto_radio)
        row.addSpacing(12)
        row.addWidget(self.manual_radio)
        row.addStretch(1)
        row.addWidget(self.on_btn)
        row.addWidget(self.off_btn)
        layout.addLayout(row)
        self._set_manual_enabled(False)
        return card

    def _build_hsv_card(self):
        card, layout = make_card("HSV Settings")
        self.hsv_tabs = QTabWidget()
        self.hsv_rows = {}

        g, r = self.cfg[GREEN], self.cfg[RED]
        green_tab = self._hsv_tab(GREEN, styles.GREEN, [
            ("H", "h", 180, g["h"]), ("S", "s", 255, g["s"]), ("V", "v", 255, g["v"])])
        red_tab = self._hsv_tab(RED, styles.RED, [
            ("H low", "h1", 180, r["h1"]), ("H high", "h2", 180, r["h2"]),
            ("S", "s", 255, r["s"]), ("V", "v", 255, r["v"])])
        self.hsv_tabs.addTab(green_tab, color_icon(styles.GREEN), "Green")
        self.hsv_tabs.addTab(red_tab, color_icon(styles.RED), "Red (2 ranges)")
        layout.addWidget(self.hsv_tabs)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        self.min_area_spin = QSpinBox()
        self.min_area_spin.setRange(100, 200000)
        self.min_area_spin.setSingleStep(100)
        self.min_area_spin.setValue(self.cfg["min_area"])
        self.stable_spin = QSpinBox()
        self.stable_spin.setRange(1, 30)
        self.stable_spin.setValue(self.cfg["stable_frames"])
        for col, (text, spin) in enumerate((("Min area (px)", self.min_area_spin),
                                            ("Stable frames", self.stable_spin))):
            label = QLabel(text)
            label.setObjectName("muted")
            grid.addWidget(label, 0, col)
            grid.addWidget(spin, 1, col)
        layout.addLayout(grid)
        layout.addStretch(1)

        buttons = QHBoxLayout()
        self.reset_btn = QPushButton("Reset defaults")
        self.save_btn = QPushButton("Save to config")
        self.save_btn.setObjectName("primary")
        buttons.addWidget(self.reset_btn)
        buttons.addStretch(1)
        buttons.addWidget(self.save_btn)
        layout.addLayout(buttons)
        return card

    def _hsv_tab(self, color, accent, rows):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(2)
        for name, key, maximum, values in rows:
            row = RangeRow(name, 0, maximum, values, accent)
            row.rangeChanged.connect(lambda lo, hi, c=color, k=key: self._on_hsv_changed(c, k, lo, hi))
            self.hsv_rows[(color, key)] = row
            layout.addWidget(row)
        return tab

    def _build_statusbar(self):
        sb = self.statusBar()
        self.sb_camera = QLabel()
        self.sb_serial = QLabel()
        self.sb_mode = QLabel()
        for w in (self.sb_camera, self.sb_serial, self.sb_mode):
            sb.addWidget(w)
        sb.addPermanentWidget(QLabel("Press Q or close window to exit"))
        self._update_statusbar()

    # ---------- เชื่อม signal ----------
    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self.refresh_ports)
        self.connect_btn.toggled.connect(self._on_connect_toggled)
        self.camera_combo.currentIndexChanged.connect(self._on_camera_changed)
        self.serial.log.connect(self.append_log)
        self.serial.connected_changed.connect(self._update_connection_ui)
        self.serial.line_received.connect(self._on_serial_line)
        self.serial.ready_changed.connect(self._on_serial_ready)

        self.start_btn.toggled.connect(self._on_start_toggled)
        self.snapshot_btn.clicked.connect(self._on_snapshot)
        self.view_group.buttonClicked.connect(self._apply_view_options)
        self.roi_check.toggled.connect(self._apply_view_options)
        self.hud_check.toggled.connect(self._apply_view_options)
        self.clear_btn.clicked.connect(self.log_view.clear)

        self.auto_radio.toggled.connect(self._on_mode_changed)
        self.on_btn.clicked.connect(lambda: self._send_command("G", " (manual)"))
        self.off_btn.clicked.connect(lambda: self._send_command("R", " (manual)"))

        self.min_area_spin.valueChanged.connect(lambda v: self._set_cfg("min_area", v))
        self.stable_spin.valueChanged.connect(self._on_stable_frames_changed)
        self.reset_btn.clicked.connect(self._reset_defaults)
        self.save_btn.clicked.connect(self._save_config)

    # ---------- Serial ----------
    def refresh_ports(self):
        current = self.port_combo.currentText()
        self.port_combo.clear()
        ports = SerialLink.available_ports()
        self.port_combo.addItems(ports)
        if current in ports:
            self.port_combo.setCurrentText(current)
        if not ports:
            self.port_combo.setPlaceholderText("ไม่พบพอร์ต")

    def _on_connect_toggled(self, checked):
        if checked and not self.serial.is_open:
            port = self.port_combo.currentText()
            if not port:
                self.append_log("error", "ยังไม่ได้เลือกพอร์ต (เสียบ ESP32 แล้วกด ⟳)")
                self.connect_btn.setChecked(False)
                return
            self.last_sent = None
            if not self.serial.open(port, int(self.baud_combo.currentText())):
                self.connect_btn.setChecked(False)
        elif not checked and self.serial.is_open:
            self.serial.close()

    def _update_connection_ui(self, connected):
        self.connect_btn.blockSignals(True)
        self.connect_btn.setChecked(connected)
        self.connect_btn.blockSignals(False)
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        for w in (self.port_combo, self.baud_combo, self.refresh_btn):
            w.setEnabled(not connected)
        if not connected:
            self._set_pill("● Disconnected", "")
            self._update_led(None)
        elif not self.serial.ready:
            self._set_pill("● Waiting for ESP32", "wait")
        self._update_statusbar()

    def _set_pill(self, text, state):
        self.conn_pill.setText(text)
        self.conn_pill.setProperty("state", state)
        repolish(self.conn_pill)

    def _on_serial_ready(self):
        self._set_pill("● ESP32 Connected", "ok")
        self.serial.send("?")  # ขอสถานะ LED ปัจจุบัน

    def _on_serial_line(self, line):
        if line == "LED:ON":
            self._update_led(True)
        elif line == "LED:OFF":
            self._update_led(False)

    def _send_command(self, cmd, note=""):
        if self.serial.send(cmd, note):
            self.last_sent = cmd
            self.cmd_value.setText(cmd)

    def append_log(self, kind, text):
        stamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"tx": "TX ", "rx": "RX ", "error": "ERR "}.get(kind, "")
        safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.log_view.appendHtml(
            f'<span style="color:{styles.MUTED}">{stamp}</span> '
            f'<span style="color:{LOG_COLORS[kind]}">{prefix}{safe}</span>')

    # ---------- LED ----------
    def _update_led(self, on):
        self.led_on = on
        self.led_indicator.setOn(bool(on))
        if on is None:
            self.led_text.setText("LED —")
            self.led_sub.setText("ยังไม่ได้รับสถานะจาก ESP32")
        else:
            self.led_text.setText("LED ON" if on else "LED OFF")
            self.led_sub.setText(f"Confirmed by ESP32 · {datetime.now():%H:%M:%S}")
        self.led_text.setProperty("on", "true" if on else "false")
        repolish(self.led_text)
        if self.worker:
            self.worker.led_text = {None: "?", True: "ON", False: "OFF"}[on]

    # ---------- กล้อง ----------
    def _on_start_toggled(self, checked):
        if checked:
            self._start_camera()
        else:
            self._stop_camera()

    def _start_camera(self):
        self.worker = CameraWorker(self.camera_combo.currentIndex(), self.cfg, self)
        self.worker.frame_ready.connect(self._show_frame)
        self.worker.detection.connect(self._on_detection)
        self.worker.error.connect(lambda msg: self.append_log("error", msg))
        self.worker.snapshot_saved.connect(lambda p: self.append_log("info", f"Snapshot saved: {p}"))
        self.worker.finished.connect(self._on_worker_finished)
        self._apply_view_options()
        self.worker.led_text = {None: "?", True: "ON", False: "OFF"}[self.led_on]
        self.worker.start()
        self.start_btn.setText("■  Stop Camera")
        self._update_statusbar()

    def _stop_camera(self):
        if self.worker:
            self.worker.stop()

    def _on_worker_finished(self):
        self.worker = None
        self.start_btn.blockSignals(True)
        self.start_btn.setChecked(False)
        self.start_btn.blockSignals(False)
        self.start_btn.setText("▶  Start Camera")
        self.video.setPixmap(QPixmap())
        self.video.setText("กล้องหยุดทำงาน")
        self.stable_bar.setValue(0)
        self._update_statusbar()

    def _on_camera_changed(self):
        if self.worker:
            self.worker.stop()
            self.start_btn.setChecked(True)

    def _apply_view_options(self, *_):
        if not self.worker:
            return
        checked = self.view_group.checkedButton()
        self.worker.view = checked.property("view") if checked else VIEW_ORIGINAL
        self.worker.use_roi = self.roi_check.isChecked()
        self.worker.show_hud = self.hud_check.isChecked()

    def _show_frame(self, image):
        pix = QPixmap.fromImage(image).scaled(
            self.video.size(), Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        self.video.setPixmap(pix)

    def _on_snapshot(self):
        if not self.worker:
            self.append_log("error", "ต้องเปิดกล้องก่อนจึงจะถ่ายภาพได้")
            return
        SNAPSHOT_DIR.mkdir(exist_ok=True)
        self.worker.request_snapshot(SNAPSHOT_DIR / f"snapshot_{datetime.now():%Y%m%d_%H%M%S}.png")

    def _on_detection(self, d):
        color = d["color"]
        if color:
            name, hex_color = COLOR_NAMES[color]
            self.color_value.setText(f'<span style="color:{hex_color}">■</span> <b>{name}</b>')
            self.area_value.setText(f'{int(d["area"]):,} px (min {self.cfg["min_area"]:,})')
        else:
            self.color_value.setText("ไม่พบสีที่กำหนด")
            self.area_value.setText("—")
        self.stable_bar.setMaximum(d["stable_needed"])
        self.stable_bar.setValue(d["stable_count"])
        self.stable_value.setText(f'{d["stable_count"]} / {d["stable_needed"]} frames')

        # โหมดอัตโนมัติ: เขียว -> เปิด, แดง -> ปิด, ไม่พบสี -> ไม่ส่งอะไร (คงสถานะเดิม)
        stable = d["stable_color"]
        if self.auto_mode and stable and self.serial.is_open:
            cmd = "G" if stable == GREEN else "R"
            if cmd != self.last_sent:
                self._send_command(cmd, f' → detected {stable.upper()} ({int(d["area"]):,} px)')

    # ---------- โหมดควบคุม ----------
    def _on_mode_changed(self, auto):
        self.auto_mode = auto
        self._set_manual_enabled(not auto)
        if auto:
            self.last_sent = None  # ให้ส่งคำสั่งตามสีปัจจุบันอีกครั้ง
        self._update_statusbar()

    def _set_manual_enabled(self, enabled):
        self.on_btn.setEnabled(enabled)
        self.off_btn.setEnabled(enabled)

    # ---------- HSV / config ----------
    def _on_hsv_changed(self, color, key, low, high):
        self.cfg[color][key] = [low, high]
        self._push_cfg()

    def _set_cfg(self, key, value):
        self.cfg[key] = value
        self._push_cfg()

    def _on_stable_frames_changed(self, value):
        self.stable_bar.setMaximum(value)
        self._set_cfg("stable_frames", value)

    def _push_cfg(self):
        if self.worker:
            self.worker.set_config(self.cfg)

    def _reset_defaults(self):
        baud = self.cfg["baud"]
        self.cfg = config.defaults()
        self.cfg["baud"] = baud
        for (color, key), row in self.hsv_rows.items():
            row.setValues(*self.cfg[color][key])
        self.min_area_spin.setValue(self.cfg["min_area"])
        self.stable_spin.setValue(self.cfg["stable_frames"])
        self._push_cfg()
        self.append_log("info", "คืนค่า HSV เริ่มต้นแล้ว (ยังไม่ได้บันทึก)")

    def _save_config(self):
        self.cfg["baud"] = int(self.baud_combo.currentText())
        try:
            config.save(self.cfg)
        except OSError as exc:
            self.append_log("error", f"บันทึกไม่สำเร็จ: {exc}")
            return
        self.append_log("info", f"บันทึกค่าลง {config.CONFIG_PATH.name} แล้ว")

    def _update_statusbar(self):
        self.sb_camera.setText("● Camera running" if self.worker else "○ Camera stopped")
        if self.serial.is_open:
            self.sb_serial.setText(f"Serial: {self.serial.port} @{self.serial.baud}")
        else:
            self.sb_serial.setText("Serial: not connected")
        self.sb_mode.setText(f"Mode: {'Auto' if self.auto_mode else 'Manual'}")

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
        self.serial.close()
        super().closeEvent(event)

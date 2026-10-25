# Color Detection-Based Automatic Light Control

ระบบควบคุมการเปิด–ปิดไฟ LED อัตโนมัติด้วยการตรวจจับสีจากกล้อง Webcam
ใช้ Python + OpenCV (HSV) ประมวลผลภาพ, PyQt6 เป็นหน้าจอ และส่งคำสั่งไปยัง ESP32 DevKit ผ่าน Serial

| ตรวจพบ | คำสั่ง | ผล |
|---|---|---|
| สีเขียว | `G` | เปิด LED |
| สีแดง | `R` | ปิด LED |
| ไม่พบสีที่กำหนด | (ไม่ส่ง) | คงสถานะไฟล่าสุด |

## โครงสร้างโปรเจกต์

```
esp32/led_control/led_control.ino   โค้ด ESP32 (Arduino IDE)
python/main.py                      จุดเริ่มโปรแกรม
python/config.py                    ค่าเริ่มต้น + โหลด/บันทึก config.json
python/core/detector.py             ตรวจจับสี HSV, ตัวกรองกันไฟกระพริบ, วาดผลบนภาพ
python/core/serial_link.py          เชื่อมต่อ ESP32 ผ่าน Serial
python/gui/main_window.py           หน้าต่างหลัก PyQt6
python/gui/camera_worker.py         QThread อ่านกล้อง + ตรวจจับ
python/gui/widgets.py               Range slider และไฟ LED จำลอง
python/gui/styles.py                ธีมสี (QSS)
docs/wiring.md                      การต่อวงจร
```

## 1. อัปโหลดโค้ดลง ESP32

1. ติดตั้ง Arduino IDE และเพิ่มบอร์ด ESP32 (Boards Manager → ค้นหา "esp32" by Espressif)
2. ต่อวงจรตาม [docs/wiring.md](docs/wiring.md)
3. เปิด `esp32/led_control/led_control.ino` เลือกบอร์ด **ESP32 Dev Module** และพอร์ต แล้วกด Upload
4. ทดสอบ: เปิด Serial Monitor (115200, Newline) พิมพ์ `G` ไฟต้องติด พิมพ์ `R` ไฟต้องดับ
5. **ปิด Serial Monitor ก่อนรันโปรแกรม Python** (ใช้พอร์ตพร้อมกันไม่ได้)

## 2. ติดตั้งและรันโปรแกรม Python (ต้องใช้ Python 3.10 ขึ้นไป)

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

บน Linux ถ้าเปิดพอร์ตไม่ได้ (Permission denied) ให้เพิ่มผู้ใช้เข้ากลุ่ม `dialout` แล้ว log out/in ใหม่:

```bash
sudo usermod -aG dialout $USER
```

## 3. วิธีใช้งาน

1. เลือกพอร์ต (เช่น `/dev/ttyUSB0`) กด ⟳ ถ้าไม่เห็น แล้วกด **Connect** รอประมาณ 2 วินาทีจนขึ้น *ESP32 Connected*
2. กด **Start Camera**
3. ถือวัตถุสีเขียวหรือสีแดงไว้ในกรอบเส้นประ (ROI) ค้างไว้ครบ 5 เฟรม ไฟจะเปิด/ปิดตามสี
4. ถ้าตรวจจับไม่แม่น ให้สลับไปดู **Green mask / Red mask** แล้วปรับ slider ในกล่อง **HSV Settings**
   จนวัตถุเป็นสีขาวชัดและพื้นหลังเป็นสีดำ จากนั้นกด **Save to config** (บันทึกลง `python/config.json`)
5. โหมด **Manual** ใช้ปุ่ม Turn ON / Turn OFF ทดสอบวงจรได้โดยไม่ต้องใช้กล้อง

ตัวเลือกอื่น:
- **Show ROI** เปิด = ตรวจจับเฉพาะในกรอบ, ปิด = ใช้ทั้งภาพ
- **Show HUD** แสดง FPS, สถานะ LED และความเสถียรบนภาพ
- **Snapshot** บันทึกภาพไว้ที่ `python/snapshots/`
- **Min area** พื้นที่ขั้นต่ำของวัตถุ (px), **Stable frames** จำนวนเฟรมที่ต้องเห็นสีเดิมก่อนสั่งไฟ
- กด `Q` เพื่อออกจากโปรแกรม

## หลักการตรวจจับสี

1. Gaussian Blur → แปลง BGR เป็น HSV
2. สร้าง mask ด้วย `cv2.inRange` (สีแดงใช้ 2 ช่วง H: 0–10 และ 170–180 แล้วรวมกัน)
3. Morphology open/close ลบจุดรบกวน
4. หา contour ที่ใหญ่ที่สุดของแต่ละสี ถ้าพื้นที่ ≥ Min area จึงนับว่าพบ ถ้าพบทั้งสองสีเลือกสีที่ใหญ่กว่า
5. ต้องพบสีเดียวกันติดกันครบ Stable frames จึงส่งคำสั่ง และส่งเฉพาะตอนสถานะเปลี่ยน

## โปรโตคอล Serial (115200 baud)

| ทิศทาง | ข้อความ | ความหมาย |
|---|---|---|
| PC → ESP32 | `G` | เปิด LED |
| PC → ESP32 | `R` | ปิด LED |
| PC → ESP32 | `?` | ขอสถานะปัจจุบัน |
| ESP32 → PC | `READY` | บอร์ดเริ่มทำงาน |
| ESP32 → PC | `LED:ON` / `LED:OFF` | ยืนยันสถานะไฟ |

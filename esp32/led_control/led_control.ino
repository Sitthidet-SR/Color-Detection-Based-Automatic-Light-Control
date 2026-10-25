/*
 * Color Detection-Based Automatic Light Control - ESP32 firmware
 *
 * รับคำสั่งจาก Python ผ่าน Serial (115200 baud)
 *   'G' -> เปิด LED  (ตรวจพบสีเขียว)
 *   'R' -> ปิด LED   (ตรวจพบสีแดง)
 *   '?' -> ถามสถานะปัจจุบัน
 * ตอบกลับ "LED:ON" หรือ "LED:OFF" ทุกครั้งเพื่อยืนยัน
 * และส่ง "READY" เมื่อบอร์ดเริ่มทำงาน
 */

const int LED_PIN = 23;          // LED ภายนอก ผ่านตัวต้านทาน 220 โอห์ม
const int BUILTIN_LED_PIN = 2;   // LED บนบอร์ด (แสดงสถานะเดียวกัน)
const long BAUD_RATE = 115200;

bool ledOn = false;

void reportState() {
  Serial.println(ledOn ? "LED:ON" : "LED:OFF");
}

void setLed(bool on) {
  ledOn = on;
  digitalWrite(LED_PIN, on ? HIGH : LOW);
  digitalWrite(BUILTIN_LED_PIN, on ? HIGH : LOW);
  reportState();
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUILTIN_LED_PIN, OUTPUT);
  Serial.begin(BAUD_RATE);
  setLed(false);
  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    switch (c) {
      case 'G':
      case 'g':
        setLed(true);
        break;
      case 'R':
      case 'r':
        setLed(false);
        break;
      case '?':
        reportState();
        break;
      default:
        // ข้าม '\n', '\r' และตัวอักษรอื่น
        break;
    }
  }
}

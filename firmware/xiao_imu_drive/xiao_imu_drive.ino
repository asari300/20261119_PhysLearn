// XIAO (内蔵 IMU LSM6DS3TR-C) + DRV8833 の 2 輪差動。取り決めは doc/protocol.md。
// MCU -> PC: "I <t_ms> ax ay az gx gy gz"（基板座標、m/s^2・rad/s）を 100 Hz で。
// PC -> MCU: "M <left> <right>"（duty -1..1）/ "S"（停止）。
// 必要なライブラリ: Seeed Arduino LSM6DS3（IMU の電源ピンと I2C バスはライブラリが板ごとに選ぶ）。

#include <Arduino.h>
#include "LSM6DS3.h"

// ---- 板ごとの違いはここだけ ----
#if defined(ARDUINO_Seeed_XIAO_nRF52840_Sense) || defined(ARDUINO_XIAO_MG24)
// 両板とも D0..D3 が PWM を出せる（nRF52840 は全 GPIO、MG24 は 4 本まで）
const int PIN_L_IN1 = D0, PIN_L_IN2 = D1;  // 左モーター (DRV8833 AIN1/AIN2)
const int PIN_R_IN1 = D2, PIN_R_IN2 = D3;  // 右モーター (DRV8833 BIN1/BIN2)
#else
#error "XIAO nRF52840 Sense か XIAO MG24 Sense を選ぶ"
#endif

// ---- 安全と周期 ----
const float DUTY_MAX = 0.6;               // |duty| の上限。PC が 1 を送ってもここで止める
const unsigned long WATCHDOG_MS = 200;    // 指令がこれだけ途絶えたら停止
const unsigned long PERIOD_US = 10000;    // IMU の送信周期 (100 Hz)
const float G = 9.80665, DEG = 0.01745329252;

LSM6DS3 imu(I2C_MODE, 0x6A);
bool imu_ok = false;
unsigned long last_cmd_ms = 0, next_us = 0;
char buf[48];
size_t len = 0;
bool overflow = false;

void drive(int in1, int in2, float d) {
  // IN/IN の fast decay: 片方を PWM、もう片方を 0。0 で両方 0（惰性で止まる）
  int pwm = (int)(fabsf(d) * 255 + 0.5);
  analogWrite(in1, d > 0 ? pwm : 0);
  analogWrite(in2, d < 0 ? pwm : 0);
}

void setMotors(float l, float r) {
  drive(PIN_L_IN1, PIN_L_IN2, constrain(l, -DUTY_MAX, DUTY_MAX));
  drive(PIN_R_IN1, PIN_R_IN2, constrain(r, -DUTY_MAX, DUTY_MAX));
}

// 1 行を解釈する。壊れた行は捨てて "# ERR" を返すだけ（ウォッチドッグは延長しない）
void handleLine(char *s) {
  char *end;
  if (s[0] == 'S' && s[1] == '\0') {
    setMotors(0, 0);
    last_cmd_ms = millis();
    return;
  }
  if (s[0] == 'M' && s[1] == ' ') {
    float l = strtof(s + 2, &end);
    char *p = end;
    float r = strtof(p, &end);
    while (*end == ' ' || *end == '\r') end++;
    if (p != s + 2 && end != p && *end == '\0' && isfinite(l) && isfinite(r)) {
      setMotors(l, r);
      last_cmd_ms = millis();
      return;
    }
  }
  Serial.println("# ERR bad line");
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      buf[len] = '\0';
      if (len > 0 && buf[len - 1] == '\r') buf[--len] = '\0';
      if (overflow) Serial.println("# ERR line too long");
      else if (len > 0) handleLine(buf);
      len = 0;
      overflow = false;
    } else if (len < sizeof(buf) - 1) {
      buf[len++] = c;
    } else {
      overflow = true;
    }
  }
}

void sendSample() {
  char out[128];
  int n = snprintf(out, sizeof(out), "I %lu %.3f %.3f %.3f %.4f %.4f %.4f\n", millis(),
                   imu.readFloatAccelX() * G, imu.readFloatAccelY() * G, imu.readFloatAccelZ() * G,
                   imu.readFloatGyroX() * DEG, imu.readFloatGyroY() * DEG, imu.readFloatGyroZ() * DEG);
  // PC が読まないとき書き込みで止まらないよう、入らない分は捨てる（ウォッチドッグを生かすため）
  if (Serial.availableForWrite() >= n) Serial.write(out, n);
}

void setup() {
  pinMode(PIN_L_IN1, OUTPUT);
  pinMode(PIN_L_IN2, OUTPUT);
  pinMode(PIN_R_IN1, OUTPUT);
  pinMode(PIN_R_IN2, OUTPUT);
  setMotors(0, 0);  // 起動時は停止
  Serial.begin(115200);
  imu_ok = imu.begin() == 0;
  next_us = micros();
}

void loop() {
  readSerial();
  if (millis() - last_cmd_ms > WATCHDOG_MS) setMotors(0, 0);
  if ((long)(micros() - next_us) >= 0) {
    next_us += PERIOD_US;
    if (imu_ok) sendSample();
    else if (Serial.availableForWrite() > 20) Serial.println("# ERR imu not found");
  }
}

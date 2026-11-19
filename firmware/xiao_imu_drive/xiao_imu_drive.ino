// XIAO (内蔵 IMU LSM6DS3TR-C) + DRV8835（秋月 AE-DRV8835-S、MODE=GND で IN/IN）の 2 輪差動。
// 取り決めは doc/protocol.md。配線は doc/textbook/03-hardware-firmware.md。
// MCU -> PC: "I <t_ms> ax ay az gx gy gz"（基板座標、m/s^2・rad/s）を 100 Hz で。
// PC -> MCU: "M <left> <right>"（duty -1..1）/ "S"（停止）。
// 必要なライブラリ: Seeed Arduino LSM6DS3（IMU の電源ピンと I2C バスはライブラリが板ごとに選ぶ。
// nRF52840 Sense では begin() が PIN_LSM6DS3TR_C_POWER を HIGH にする: ライブラリ 2.0.8 のソースで確認）。

#include <Arduino.h>
#include "LSM6DS3.h"
#include "fixed_fmt.h"

// ---- 板ごとの違いはここだけ ----
#if defined(ARDUINO_Seeed_XIAO_nRF52840_Sense) || defined(ARDUINO_XIAO_MG24)
// nRF52840: analogWrite は空いた PWM モジュールに割り当てるのでどの GPIO でもよい。既定は 8 bit・
// 16 MHz/255 ≈ 62.7 kHz（コア 1.1.13 の HardwarePWM.cpp）で、DRV8835 の上限 250 kHz 内。
// MG24 は未コンパイル・未確認
const int PIN_L_IN1 = D0, PIN_L_IN2 = D1;  // 左モーター (DRV8835 AIN1/AIN2)
const int PIN_R_IN1 = D2, PIN_R_IN2 = D3;  // 右モーター (DRV8835 BIN1/BIN2)
#else
#error "XIAO nRF52840 Sense か XIAO MG24 Sense を選ぶ"
#endif

// ---- 安全と周期 ----
const float DUTY_MAX = 0.6;               // |duty| の上限。PC 側 link.DUTY_MAX と同じ値に（tests/test_link.py が照合）
const unsigned long WATCHDOG_MS = 200;    // 指令がこれだけ途絶えたら停止
const unsigned long PERIOD_US = 10000;    // IMU の送信周期 (100 Hz)
const float G = 9.80665, DEG = 0.01745329252;

// 0x6A: XIAO の Sense 版の IMU の I2C アドレス（SA0 = GND）。ライブラリの LSM6DS3 の引数の既定も 0x6A だが、
// LSM6DS3Core 側の既定とコメントは 0x6B なので、取り違えないよう明示する（ライブラリ 2.0.8 のソースで確認）
LSM6DS3 imu(I2C_MODE, 0x6A);
bool imu_ok = false;
unsigned long last_cmd_ms = 0, next_us = 0;
char buf[48];
size_t len = 0;
bool overflow = false;

void drive(int in1, int in2, float d) {
  // DRV8835 IN/IN（データシート Table 3）: 10 正転・01 逆転・00 空転・11 ブレーキ。
  // fast decay（PWM の休みは空転）にする: duty 0・ウォッチドッグ停止が両入力 LOW の空転になり、
  // 停止で急ブレーキがかからず、入力 0 V はスリープ時の推奨とも合う。duty と速さの非線形は sysid に任せる
  int pwm = (int)(fabsf(d) * 255 + 0.5);
  analogWrite(in1, d > 0 ? pwm : 0);
  analogWrite(in2, d < 0 ? pwm : 0);
}

void setMotors(float l, float r) {
  drive(PIN_L_IN1, PIN_L_IN2, constrain(l, -DUTY_MAX, DUTY_MAX));
  drive(PIN_R_IN1, PIN_R_IN2, constrain(r, -DUTY_MAX, DUTY_MAX));
}

// PC が読まないとき書き込みで止まらないよう、入らない分は捨てる（ウォッチドッグを生かすため）。
// TinyUSB の CDC write は接続中に FIFO が埋まると空くまで待つ（コア 1.1.13 Adafruit_USBD_CDC.cpp:224）
void say(const char *msg) {
  if (Serial.availableForWrite() > (int)strlen(msg) + 2) Serial.println(msg);
}

// 1 行を解釈する。壊れた行は捨てて "# ERR" を返すだけ（ウォッチドッグは延長しない）
void handleLine(char *s) {
  char *end = s + 1;
  while (*end == ' ') end++;  // 端末から手で打った "S " でもすぐ止める
  if (s[0] == 'S' && *end == '\0') {
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
  say("# ERR bad line");
}

void readSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      buf[len] = '\0';
      if (len > 0 && buf[len - 1] == '\r') buf[--len] = '\0';
      if (overflow) say("# ERR line too long");
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
  // %f は使わない（MG24 のコアでは空になる見込み。fixed_fmt.h）。最長 12+3*9+3*10+1 = 70 文字 < 128
  char out[128];
  int n = snprintf(out, sizeof(out), "I %lu", millis());
  n += put_fixed(out + n, imu.readFloatAccelX() * G, 3);
  n += put_fixed(out + n, imu.readFloatAccelY() * G, 3);
  n += put_fixed(out + n, imu.readFloatAccelZ() * G, 3);
  n += put_fixed(out + n, imu.readFloatGyroX() * DEG, 4);
  n += put_fixed(out + n, imu.readFloatGyroY() * DEG, 4);
  n += put_fixed(out + n, imu.readFloatGyroZ() * DEG, 4);
  out[n++] = '\n';
  if (Serial.availableForWrite() >= n) Serial.write(out, n);
}

void setup() {
  pinMode(PIN_L_IN1, OUTPUT);
  pinMode(PIN_L_IN2, OUTPUT);
  pinMode(PIN_R_IN1, OUTPUT);
  pinMode(PIN_R_IN2, OUTPUT);
  setMotors(0, 0);  // 起動時は停止
  Serial.begin(115200);
  // ±1000 dps: sim で duty 0.5 の旋回が約 9 rad/s (≈515 dps) 出るので ±500 では飽和する。
  // 35 mdps/LSB ≈ 6.1e-4 rad/s/LSB。既定の ±2000 より 2 倍細かい。ライブラリは 125/245/500/1000/2000 以外を 2000 にする
  imu.settings.gyroRange = 1000;
  imu.settings.accelRange = 16;  // ライブラリの既定と同じ。衝突で飽和させないため明示
  imu_ok = imu.begin() == 0;
  next_us = micros();
}

void loop() {
  readSerial();
  if (millis() - last_cmd_ms > WATCHDOG_MS) setMotors(0, 0);
  if ((long)(micros() - next_us) >= 0) {
    next_us += PERIOD_US;
    if (imu_ok) sendSample();
    else say("# ERR imu not found");
  }
}

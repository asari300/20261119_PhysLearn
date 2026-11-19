// 小数を整数演算だけで文字列にする。snprintf の %f は MG24 のコア（nano.specs のみ、-u _printf_float なし）で
// 空になる見込みなので使わない。dtostrf は両方のコアにあるか未確認で、あっても丸め・桁の挙動が揃う保証が無い。
// このファイルは Arduino に依存しない（PC の g++ でそのまま試せる）。
#pragma once
#include <math.h>
#include <stdint.h>

// buf に ' ' + 小数 dec 桁（dec は 1..4）の固定小数を書き、書いた文字数を返す。NUL は付けない。
// buf には 10 バイト要る（空白 負号 整数 3 桁 小数点 小数 4 桁）。
// NaN は 0、|x| は 999 で頭打ち（センサーの範囲 ±16 g = 157 m/s^2・±1000 dps = 17.5 rad/s の外）。
// 丸めは四捨五入（%.Nf は float を正確な 2 進数として丸めるので、境界でごく稀に最後の桁が 1 違う。PC は数値として読む）。
// 負号は丸めた値が 0 でないときだけ付ける（"-0.000" を出さない）。
static inline int put_fixed(char *buf, float x, int dec) {
  int32_t scale = 1;
  for (int i = 0; i < dec; i++) scale *= 10;
  if (!(x == x)) x = 0;  // NaN
  if (x > 999.0f) x = 999.0f;
  if (x < -999.0f) x = -999.0f;
  int32_t v = (int32_t)lroundf(x * (float)scale);
  bool neg = v < 0;
  uint32_t u = neg ? (uint32_t)(-v) : (uint32_t)v;
  uint32_t ip = u / (uint32_t)scale, fp = u % (uint32_t)scale;
  char tmp[4];
  int n = 0, m = 0;
  buf[m++] = ' ';
  if (neg) buf[m++] = '-';
  do { tmp[n++] = '0' + ip % 10; ip /= 10; } while (ip);
  while (n) buf[m++] = tmp[--n];
  buf[m++] = '.';
  for (int i = dec - 1, d = scale / 10; i >= 0; i--, d /= 10) { buf[m++] = '0' + (fp / d) % 10; }
  return m;
}

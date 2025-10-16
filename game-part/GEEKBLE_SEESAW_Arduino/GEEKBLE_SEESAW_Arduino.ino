#define THRESHOLD 7   // 기준값 변동 허용치

int16_t bias = -60;   // horizontal bias

char c;

double x = 0;
double zero_x = 0;

bool calibrated = false;   // 영점 보정 완료 여부
bool out_of_range = false; // 현재 상태 (영점 벗어남 여부)

// ---------------------------
// 시리얼 버퍼 비우기
// ---------------------------
void flushSerialBuffer() {
  while (Serial.available() > 0) {
    Serial.read(); // 들어오는 데이터 읽고 버림
  }
}

void toggleLED() {
  int state = digitalRead(LED_BUILTIN);
  digitalWrite(LED_BUILTIN, !state);
}

// ---------------------------
// 아두이노 기본 구조
// ---------------------------
void setup() {
  Serial.begin(115200);

  pinMode(LED_BUILTIN, OUTPUT);

  // 초기 2초간 값 평균내서 영점 설정
  long startTime = millis();
  long count = 0;
  double sum_x = 0;

  while (millis() - startTime < 2000) {
    if (Serial.available()) {
      c = Serial.read();
      if (c == '*') {
        double temp_x = Serial.parseFloat() - bias;
        sum_x += temp_x;
        count++;
      }
    }
  }

  if (count > 0) {
    zero_x = sum_x / count;
    calibrated = true;
  }
}

void loop() {
  flushSerialBuffer();

  if (!calibrated) return;

  if (Serial.available()) {
    c = Serial.read();
    if (c == '*') {
      x = Serial.parseFloat() - bias;

      bool is_out = (abs(x - zero_x) >= THRESHOLD);

      // 범위 안 → 범위 밖으로 처음 넘어갈 때만 LED 토글
      if (is_out && !out_of_range) {
        Serial.println('1');
        out_of_range = true;

        toggleLED();  // LED ON/OFF
      }

      // 다시 범위 안이면 상태 복귀
      if (!is_out && out_of_range) {
        out_of_range = false;
      }
    }
  }
}

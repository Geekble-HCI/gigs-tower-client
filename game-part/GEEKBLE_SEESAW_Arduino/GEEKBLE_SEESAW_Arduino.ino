#define THRESHOLD 7   // 기준값 변동 허용치

int16_t bias = -60;   // horizontal bias

char c;

double x = 0;
double zero_x = 0;

bool calibrated = false;   // 영점 보정 완료 여부
bool out_of_range = false; // 현재 상태 (영점 벗어남 여부)

void setup() {
  Serial.begin(115200);

  // 초기 2초간 값 평균내서 영점 설정
  long startTime = millis();
  long count = 0;
  double sum_x = 0;

  while (millis() - startTime < 2000) {   // 2초 동안 수집
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

  // Serial.println("Calibration done!");
  // Serial.print("Zero X: "); Serial.println(zero_x);
}

void loop() {
  if (!calibrated) return;   // 아직 보정 안됐으면 무시

  if (Serial.available()) {
    c = Serial.read();
    if (c == '*') {
      x = Serial.parseFloat() - bias;

      bool is_out = (abs(x - zero_x) >= THRESHOLD);

      // 상태가 "범위 안 → 범위 밖"으로 바뀔 때만 1 출력
      if (is_out && !out_of_range) {
        Serial.println('1');
        out_of_range = true;
      }

      // 다시 범위 안으로 들어오면 상태 초기화
      if (!is_out && out_of_range) {
        out_of_range = false;
      }
    }
  }
}

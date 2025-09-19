#define Y_MIN 95
#define Y_MAX 105

int16_t bias = -60;  // horizontal bias

char c;

double x = 0;
double y = 0;
double z = 0;

bool was_below = false;  // 이전에 y가 MIN 이하였는지 기억

void setup() {
  Serial.begin(115200);   // 나노는 그냥 이렇게만 쓰면 됩니다
}

void loop() {
  if (Serial.available()) {
    c = Serial.read();
    if (c == '*') {
      x = Serial.parseFloat() - bias;
      y = Serial.parseFloat() - bias;
      z = Serial.parseFloat() - bias;

      // y값 디버깅 출력
      // Serial.print("Y: ");
      // Serial.println(y);

      // 조건: y가 MIN 이하 → MAX 이상으로 바뀔 때
      if (y <= Y_MIN) {
        was_below = true;   // 바닥 구간 통과
      }
      if (was_below && y >= Y_MAX) {
        Serial.println('1');   // 문자열 '1'이 아니라 숫자 1 출력
        was_below = false;  // 다시 초기화
      }
    }
  }
}

int16_t bias = -60;  // horizontal bias

char c;

double x = 0;
double y = 0;
double z = 0;

void setup() {
  Serial.begin(115200);   // 아두이노 나노 기본 시리얼 속도
}

void loop() {
  if (Serial.available()) {
    c = Serial.read();
    if (c == '*') {
      x = Serial.parseFloat() - bias;
      y = Serial.parseFloat() - bias;
      z = Serial.parseFloat() - bias;

      // XYZ 값 출력
      Serial.print("X: ");
      Serial.print(x);
      Serial.print("  Y: ");
      Serial.print(y);
      Serial.print("  Z: ");
      Serial.println(z);
    }
  }
}

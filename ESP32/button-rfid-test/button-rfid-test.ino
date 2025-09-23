const int buttonPin = SW_BUILTIN;  // 아두이노 내장 버튼
int lastButtonState = HIGH;        // 이전 버튼 상태 (풀업이라 기본 HIGH)

void setup() {
  Serial.begin(115200);            // 시리얼 시작
  pinMode(buttonPin, INPUT_PULLUP); // 내장 버튼 풀업 모드
}

void loop() {
  int buttonState = digitalRead(buttonPin);

  // 버튼이 눌렸을 때 (HIGH → LOW)
  if (buttonState == LOW && lastButtonState == HIGH) {
    // Serial.println("10");  // 시리얼로 "10" 출력
    Serial.println("-3");  // 시리얼로 "-3" 출력
    // Serial.println("BC2D5005");  // 시리얼로 "BC2D5005" 출력
    delay(50);             // 디바운스 처리
  }

  lastButtonState = buttonState;
}

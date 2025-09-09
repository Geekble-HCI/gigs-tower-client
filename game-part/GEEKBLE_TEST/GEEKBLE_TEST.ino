// 버튼 핀 정의
const int buttonPin = 2; // 버튼을 연결한 디지털 핀
int buttonState = 0;
int lastButtonState = 0;

void setup() {
  Serial.begin(115200);       // 시리얼 시작
  pinMode(buttonPin, INPUT_PULLUP); // 버튼 핀 풀업으로 설정
}

void loop() {
  buttonState = digitalRead(buttonPin);

  // 버튼이 눌렸을 때(풀업이므로 LOW일 때)
  if (buttonState == LOW && lastButtonState == HIGH) {
    Serial.println("10");  // 시리얼로 10 출력
    delay(50);             // 디바운스
  }

  lastButtonState = buttonState;
}

const int buttonPin = 2;   // 버튼 연결 핀 (D2)
bool prevState = HIGH;

void setup() {
  Serial.begin(115200);          // Micro는 Serial 그대로 사용 가능
  pinMode(buttonPin, INPUT_PULLUP); // 내부 풀업 저항 사용
}

void loop() {
  bool currentState = digitalRead(buttonPin);

  if (prevState == HIGH && currentState == LOW) {
    Serial.println('a');       // 시리얼로 숫자 전송
    delay(200);                  // 디바운싱
  }

  prevState = currentState;
}
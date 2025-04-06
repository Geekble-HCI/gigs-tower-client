const int buttonPin = 0;         // 내장 BOOT 버튼 (GPIO0)
const int ledPin = LED_BUILTIN;  // 내장 LED
bool prevState = HIGH;

void setup() {
  Serial.begin(115200);
  pinMode(buttonPin, INPUT_PULLUP); // 내부 풀업 사용
  pinMode(ledPin, OUTPUT);
  digitalWrite(ledPin, LOW);
}

void loop() {
  bool currentState = digitalRead(buttonPin);

  if (prevState == HIGH && currentState == LOW) {
    Serial.println('a');
    digitalWrite(ledPin, HIGH);
    delay(200);
    digitalWrite(ledPin, LOW);
  }

  prevState = currentState;
}
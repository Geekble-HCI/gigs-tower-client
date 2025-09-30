//=======================[ 헤더 및 핀 정의 ]=========================
#include "USB.h"               
#include "USBHIDKeyboard.h"    

#define BUTTON_PIN  SW_BUILTIN   // 보드 내장 버튼
#define LED_PIN     LED_BUILTIN  // 보드 내장 LED

//=======================[ 객체 생성 ]==============================
USBHIDKeyboard Keyboard; 

//=======================[ 더블 클릭 판별 변수 ]====================
unsigned long lastClickTime = 0;   // 마지막 클릭 시간
const unsigned long clickGap = 400; // 더블클릭 허용 간격(ms)
int clickCount = 0;

//=======================[ 초기 설정 ]=============================
void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  Keyboard.begin();
  USB.begin();
}

//=======================[ 메인 루프 ]=============================
void loop() {
  static bool lastButtonState = HIGH;  // 이전 버튼 상태
  bool buttonState = digitalRead(BUTTON_PIN);

  //--- 버튼 눌림 감지 (LOW 전환 순간) ---
  if (lastButtonState == HIGH && buttonState == LOW) {
    unsigned long now = millis();

    // 연속 클릭인지 확인
    if (now - lastClickTime <= clickGap) {
      clickCount++;
    } else {
      clickCount = 1;  // 새 클릭 시작
    }
    lastClickTime = now;
  }

  //--- 클릭 판정 ---
  if (clickCount == 1 && millis() - lastClickTime > clickGap) {
    // 단일 클릭 (Enter)
    digitalWrite(LED_PIN, HIGH);
    Keyboard.write(KEY_RETURN);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    clickCount = 0;
  } else if (clickCount == 2) {
    // 더블 클릭 (ESC)
    digitalWrite(LED_PIN, HIGH);
    Keyboard.write(KEY_ESC);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    clickCount = 0;
  }

  lastButtonState = buttonState;
}

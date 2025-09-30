#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

// SPI 핀 정의 (사용자 원래 정의 유지)
#define PN532_SCK   2 // orange
#define PN532_MISO  5 // yellow
#define PN532_MOSI  3 // green
#define PN532_SS    4 // blue

// 중복 감지 시간 (ms)
#define DEBOUNCE_MS 500

Adafruit_PN532 nfc(PN532_SCK, PN532_MISO, PN532_MOSI, PN532_SS);

// 상태 변수
unsigned long lastTagTime = 0;
String lastUID = "";
unsigned long loopCount = 0;
unsigned long detectedCount = 0;

void setup() {
  Serial.begin(115200);
  while (!Serial) ; // 시리얼 준비 대기

  // Serial.println(F("PN532 UID Reader (SPI) - starting..."));

  initNFC();
}

void loop() {
  loopCount++;

  uint8_t uid[7];       // UID를 담을 버퍼 (최대 7바이트)
  uint8_t uidLength;    // 실제 UID 길이

  // 카드가 있으면 true 반환
  if (nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength)) {
    // UID 문자열로 변환 (16진수, 앞자리 0 패딩)
    String currentUID = "";
    for (uint8_t i = 0; i < uidLength; i++) {
      if (uid[i] < 0x10) currentUID += "0";
      currentUID += String(uid[i], HEX);
    }
    // 소문자로 나오는 경우가 있으니 일관성 위해 대문자로 변환
    currentUID.toUpperCase();

    unsigned long now = millis();
    // 같은 카드가 DEBOUNCE_MS 이내이면 무시
    if (currentUID != lastUID || (now - lastTagTime) > DEBOUNCE_MS) {
      // 새로운(또는 허용된 시간 지난) 카드로 인식
      // Serial.print(F("UID: "));
      Serial.println(currentUID);
      lastUID = currentUID;
      lastTagTime = now;
      detectedCount++;
      // 필요하면 여기에 추가 동작(예: 시리얼 통신으로 전송, LED 점등 등) 작성
    } else {
      // 중복 감지 무시 (디버그용 출력 - 원치 않으면 주석 처리)
      // Serial.print(F("Ignored duplicate UID within "));
      // Serial.print(DEBOUNCE_MS);
      // Serial.println(F(" ms."));
    }
  }

  // 상태 출력 (원하면 주석)
  // if ((loopCount % 100) == 0) { // 100번 루프마다 상태 출력 (너무 자주 안 보이게)
  //   Serial.print(F("Loops: "));
  //   Serial.print(loopCount);
  //   Serial.print(F("  Detected: "));
  //   Serial.println(detectedCount);
  // }

  delay(50); // 루프 과부하 방지
}

// NFC 초기화 함수
void initNFC() {
  nfc.begin();

  // 펌웨어 버전 확인
  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println(F("Didn't find PN532 (check wiring)"));
    while (1) {
      delay(1000);
    }
  }

  // 출력(디버그)
  // Serial.print(F("Found PN532 chipset. Firmware version: "));
  // Serial.print((versiondata >> 24) & 0xFF, DEC);
  // Serial.print('.');
  // Serial.println((versiondata >> 16) & 0xFF, DEC);

  // 동작 모드 구성
  nfc.SAMConfig();                 // Secure Access Module config (일반적으로 필요)
  nfc.setPassiveActivationRetries(0xFF); // 계속 탐지(필요에 따라 조정)
  delay(100); // 모듈 안정화
}

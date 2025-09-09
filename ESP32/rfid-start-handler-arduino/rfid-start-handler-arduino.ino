#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

#define PN532_SCK   2 // orange
#define PN532_MISO  5 // yellow
#define PN532_MOSI  3 // green
#define PN532_SS    4 // blue

Adafruit_PN532 nfc(PN532_SCK, PN532_MISO, PN532_MOSI, PN532_SS);

void setup() {
  Serial.begin(115200);
  while (!Serial);
  nfc.begin();

  uint32_t versiondata = nfc.getFirmwareVersion();
  if (!versiondata) {
    Serial.println("PN532 not found");
    while (1);
  }
  nfc.setPassiveActivationRetries(0xFF);
}

void loop() {
  uint8_t success;
  uint8_t uid[7];
  uint8_t uidLength;

  success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);

  if (success) {
    Serial.println("a");   // 카드 감지 신호
    // delay(5000);           // 5초 대기

    // UID를 HEX 문자열로 변환해서 한 줄로 출력
    // for (uint8_t i = 0; i < uidLength; i++) {
    //   if (uid[i] < 0x10) Serial.print("0"); // 한 자리수면 앞에 0 붙이기
    //   Serial.print(uid[i], HEX);
    // }
    // Serial.println();

    delay(1000); // 중복 감지 방지
  }
}

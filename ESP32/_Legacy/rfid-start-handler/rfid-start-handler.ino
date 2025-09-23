/**************************************************************************/
/*!
    @file     iso14443as_target_game.ino
    @original Adafruit iso14443as_target example (modified)
    @license  BSD (see license.txt)
*/
/**************************************************************************/

#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

// SPI 연결 핀 정의 (보드에 맞게 변경하세요)
#define PN532_SCK   13
#define PN532_MISO  12
#define PN532_MOSI  11
#define PN532_SS    10

Adafruit_PN532 nfc(PN532_SCK, PN532_MISO, PN532_MOSI, PN532_SS);

void setup() {
  Serial.begin(115200);
  while (!Serial);
  delay(500);
  Serial.println("Setup Serial");

  nfc.begin();

  Serial.println("Called nfc.begin()");
  uint32_t versiondata = nfc.getFirmwareVersion();
  Serial.print("Firmware version: "); Serial.println(versiondata, HEX);

  if (!versiondata) {
    Serial.println("Didn't find PN532 board");
    while (1); // 무한 대기
  }

  nfc.setPassiveActivationRetries(0xFF);
  Serial.println("Setup NFC");
}

void loop() {
  uint8_t apduBuf[255];
  uint8_t apduLen;

  // 1) 카드 에뮬레이션 모드 진입
  nfc.AsTarget();

  // 2) 리더(또는 단말)에서 보낸 첫 APDU 읽기
  apduLen = 0;
  nfc.getDataTarget(apduBuf, &apduLen);
  if (apduLen > 0) {
    // 최초 APDU 수신 시
    Serial.println('a');
    delay(500);
  }
}
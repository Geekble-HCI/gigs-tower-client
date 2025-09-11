#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>

// SPI 핀 정의 (케이블 색상 표시)
#define PN532_SCK   2 // orange
#define PN532_MISO  5 // yellow
#define PN532_MOSI  3 // green
#define PN532_SS    4 // blue
#define PN532_PWR   7 // red, VCC 제어용 핀

#define DELAY_TIME 3000

Adafruit_PN532 nfc(PN532_SCK, PN532_MISO, PN532_MOSI, PN532_SS);

void setup() {
    Serial.begin(115200);
    while (!Serial);

    pinMode(PN532_PWR, OUTPUT);
    digitalWrite(PN532_PWR, HIGH); // NFC 전원 ON

    initNFC();
}

void loop() {
    uint8_t success;
    uint8_t uid[7];
    uint8_t uidLength;

    // 카드 감지
    success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
    if (success) {
        // UID 출력
        for (uint8_t i = 0; i < uidLength; i++) {
            if (uid[i] < 0x10) Serial.print("0");
            Serial.print(uid[i], HEX);
        }
        Serial.println();

        // 카드 인식 즉시 전원 차단
        digitalWrite(PN532_PWR, LOW);

        // 카드 중복 태그 방지 3초 대기
        delay(DELAY_TIME); 

        // NFC 전원 ON 후 재초기화
        digitalWrite(PN532_PWR, HIGH);
        delay(50); // 모듈 안정화
        initNFC();
    }
}

// NFC 초기화 함수
void initNFC() {
    nfc.begin();
    uint32_t versiondata = nfc.getFirmwareVersion();
    if (!versiondata) {
        Serial.println("PN532 not found");
        while (1);
    }
    nfc.setPassiveActivationRetries(0xFF);
}

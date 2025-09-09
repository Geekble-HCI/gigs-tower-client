#include <Wire.h>
#include <SPI.h>
#include <Adafruit_PN532.h>
#include <avr/wdt.h> // Watchdog Timer 사용

// SPI 핀 정의
#define PN532_SCK   2 // orange
#define PN532_MISO  5 // yellow
#define PN532_MOSI  3 // green
#define PN532_SS    4 // blue

Adafruit_PN532 nfc(PN532_SCK, PN532_MISO, PN532_MOSI, PN532_SS);

void setup() {
    Serial.begin(115200);
    while (!Serial); // 시리얼 준비 대기

    nfc.begin();

    uint32_t versiondata = nfc.getFirmwareVersion();
    if (!versiondata) {
        Serial.println("PN532 not found");
        while (1); // 장치 없음 시 무한 루프
    }

    nfc.setPassiveActivationRetries(0xFF); // 카드 감지 시도 횟수
    Serial.println("Ready to read NFC tag...");
}

void loop() {
    uint8_t success;
    uint8_t uid[7];
    uint8_t uidLength;

    // 카드 감지
    success = nfc.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength);
    if (success) {
        // UID 출력
        Serial.print("UID: ");
        for (uint8_t i = 0; i < uidLength; i++) {
            if (uid[i] < 0x10) Serial.print("0");
            Serial.print(uid[i], HEX);
        }
        Serial.println();

        // 바로 리부팅
        Serial.println("Restarting board...");
        wdt_enable(WDTO_15MS); // 15ms 후 강제 리셋
        while (1); // WDT가 트리거될 때까지 대기
    }
}

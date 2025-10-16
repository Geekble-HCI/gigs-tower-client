# ESP32 / Arduino 펌웨어

삼양 팝업 게임용 ESP32 및 Arduino 펌웨어입니다.

## 💡 간단 요약

- **button-rfid-test**: 버튼을 눌러 NFC 태그를 시뮬레이션
- **keyboard-esc-enter**: 긱블 나노 활용하여 타워 운용에 필요한 키보드 esc키와 enter키를 입력하는 코드
- **rfid-start-handler-arduino**: 실제 게임기에 설치 (NFC 카드 UID값 인식)

## 📌 주의 사항

- PN532보드는 로직레벨 3.3v이어서 ESP32계열 보드를 써야 코드가 작동.
- 긱블 나노 기준으로 \_Legacy폴더에 읽기 쓰기 코드 업데이트 해 두었음.

## 📁 구성

esp32/
├── \_LEGACY/ # 기존 코드 아카이브, PN532 읽기 쓰기 작동 코드
├── button-rfid-test/ # NFC 카드 시뮬레이션용 더미 장치 (Arduino Mini)
├── keyboard-esc-enter/ # 키보드 esc키와 enter키를 입력하는 코드
└── rfid-start-handler-arduino/ # rfid-start-handler Arduino Nano용

## 🎯 펌웨어 설명

### rfid-start-handler (메인, ESP32)

- **용도**: NFC 카드 감지해서 게임 시작
- **하드웨어**: ESP32 + PN532 NFC 모듈
- **동작**: 카드 터치 → 시리얼로 `'a'` 전송 → 5초 대기

### rfid-button-handler (테스트, ESP32)

- **용도**: 물리 버튼으로 게임 시작 테스트
- **하드웨어**: ESP32 + 푸시 버튼 (D2 핀)
- **동작**: 버튼 누름 → 시리얼로 `'a'` 전송

### button-rfid-test (Arduino Mini)

- **용도**: 버튼을 누르면 NFC 태그가 된 것처럼 동작 (더미 장치)
- **하드웨어**: Geekble Arduino Mini + 버튼
- **동작**: 버튼 누름 → 시리얼 출력 115200 → 문자열 `"BC2D5005"` 전송

### button-score-test (Arduino Mini)

- **용도**: 게임 장치를 대신하여 점수 전송 (더미 장치)
- **하드웨어**: Geekble Arduino Mini + 버튼
- **동작**: 버튼 누름 → 시리얼 출력 115200 → 문자열 `"10"` 전송

### rfid-start-handler-arduino (Arduino Nano)

- **용도**: 기존 rfid-start-handler ESP32 장치를 Arduino Nano용으로 변경
- **하드웨어**: Arduino Nano + PN532 NFC 모듈
- **동작**: 카드 터치 → 시리얼 출력 115200 → `'a'` 전송

## 🔌 연결 방법

### NFC 모듈 연결 (rfid-start-handler / Arduino Nano)

PN532 → ESP32 / Arduino Nano
SCK → SCK
MOSI → MOSI
MISO → MISO
SS → SS

css
코드 복사

### 버튼 연결 (rfid-button-handler / button-rfid-test / button-score-test)

버튼 한쪽 → D2 (GPIO 2)
버튼 다른쪽 → GND

markdown
코드 복사

## ⚙️ 사용법

1. **Arduino IDE에서 업로드**

   - 보드: ESP32 Dev Module 또는 Arduino Nano / Mini
   - 속도: 115200

2. **라이브러리 설치** (NFC용만)

   - Adafruit PN532

3. **시리얼 모니터 확인**
   - 115200 baud로 설정
   - 카드/버튼 동작 시 출력 확인
     - rfid-start-handler / rfid-start-handler-arduino: `'a'`
     - button-rfid-test: `"BC2D5005"`
     - button-score-test: `"10"`

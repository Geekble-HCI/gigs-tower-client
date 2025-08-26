# ESP32 펌웨어

삼양 팝업 게임용 ESP32 펌웨어입니다.

## 💡 간단 요약
- **rfid-start-handler**: 실제 게임기에 설치 (NFC 카드)
- **rfid-button-handler**: NFC 없이 개발/테스트할 때 (버튼)

## 📁 구성

```
esp32/
├── rfid-start-handler/     # NFC 카드로 게임 시작 (실제 운영용)
└── rfid-button-handler/    # 버튼으로 게임 시작 (테스트용)
```

## 🎯 펌웨어 설명

### rfid-start-handler (메인)
- **용도**: NFC 카드 감지해서 게임 시작
- **하드웨어**: ESP32 + PN532 NFC 모듈
- **동작**: 카드 터치 → 시리얼로 'a' 전송 → 5초 대기

### rfid-button-handler (테스트)
- **용도**: 물리 버튼으로 게임 시작 테스트
- **하드웨어**: ESP32 + 푸시 버튼 (D2 핀)
- **동작**: 버튼 누름 → 시리얼로 'a' 전송

## 🔌 연결 방법

### NFC 모듈 연결 (rfid-start-handler)
```
PN532 → ESP32
SCK   → SCK
MOSI  → MOSI  
MISO  → MISO
SS    → SS
```

### 버튼 연결 (rfid-button-handler)
```
버튼 한쪽 → D2 (GPIO 2)
버튼 다른쪽 → GND
```

## ⚙️ 사용법

1. **Arduino IDE에서 업로드**
   - 보드: ESP32 Dev Module
   - 속도: 115200

2. **라이브러리 설치** (NFC용만)
   - Adafruit PN532

3. **시리얼 모니터 확인**
   - 115200 baud로 설정
   - 카드/버튼 동작 시 'a' 출력 확인


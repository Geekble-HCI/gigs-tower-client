# GIGS Game Client

팝업 게임 클라이언트 - 6가지 IoT 게임을 지원하는 인터랙티브 게임 시스템

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 게임 실행

```bash
# 기본 실행 (게임 타입 1, 디바이스 ID 01)
python3 pop-client.py

# 특정 게임 실행 (농구 게임)
python3 pop-client.py --type 6 --device_id 6

# 테스트 모드 (키보드 입력 활성화)
python3 pop-client.py --type 5 --device_id 5 --test
```

### 3. 라즈베리파이 부팅 시 자동 실행

```bash
# 실행 권한 부여
chmod +x Shell/AutoStart_Game_Basketball.sh

# 크론탭 설정
crontab -e

# 다음 라인 추가:
# @reboot /home/pi/samyang-pop-client/Shell/AutoStart_Game_Basketball.sh
```

## 🎮 지원 게임

| 게임 타입 | 게임명 | 설명 |
|-----------|--------|------|
| 1 | 헬시 버거 챌린지 | 건강한 버거 만들기 게임 |
| 2 | 꿀잠 방해꾼 OUT! | 수면 방해 요소 제거 게임 |
| 3 | 불태워! 칼로링머신 | 칼로리 소모 운동 게임 |
| 4 | 볼볼볼 영양소 | 영양소 수집 게임 |
| 5 | 바이오데이터 에어시소 | 균형 감각 게임 |
| 6 | 슛잇! 무빙 골대 | 농구 슈팅 게임 |

## 🏗️ 시스템 구조

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ESP32 RFID    │───▶│  Game Client    │───▶│   MQTT Broker   │
│   Card Reader   │    │   (Python)      │    │   (Network)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Serial Comm.   │    │ Screen Display  │    │ Remote Control  │
│     (115200)    │    │   (Pygame)      │    │   Commands      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📋 명령행 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--type` | 게임 타입 (1-6) | 1 |
| `--device_id` | 장치 식별 ID | "01" |
| `--tcp` | TCP 연결 활성화 | False |
| `--test` | 테스트 모드 (키보드 입력) | False |
| `--enter` | 입장 화면 표시 | False |
| `--exit` | 퇴장 화면 표시 | False |
| `--score-wait-time` | 점수 대기 시간 (초) | 15 |
| `--countdown-time` | 카운트다운 시간 (초) | 10 |
| `--mqtt-broker` | MQTT 브로커 주소 | 자동 검색 |

## 🎯 게임 상태 흐름

```
     시작
      │
   ┌──▼──┐
   │INIT │ ◄─────────┐
   └──┬──┘           │
      │              │
   ┌──▼──┐           │
   │WAIT │ ◄─────────┤
   └──┬──┘           │
      │              │
   ┌──▼──┐           │
   │COUNT│           │
   └──┬──┘           │
      │              │
   ┌──▼──┐           │
   │PLAY │           │
   └──┬──┘           │
      │              │
   ┌──▼──┐           │
   │SCORE│───────────┤
   └──┬──┘           │
      │              │
   ┌──▼──┐           │
   │RESULT│──────────┘
   └─────┘
```

## 🔧 하드웨어 요구사항

### ESP32 설정
- **RFID 모듈**: PN532 (SPI 연결)
- **시리얼 통신**: 115200 baud
- **카드 감지**: 'a' 문자 전송
- **지연 시간**: 카드 감지 후 5초 대기

### 화면 설정
- **해상도**: 전체화면 (FULLSCREEN)
- **마진**: 좌측 68px, 상단 248px, 우측 48px, 하단 38px
- **폰트**: RoundSquare.ttf (30pt)
- **배경**: Image/bg.png

## 📡 통신 프로토콜

### MQTT 토픽 구조

```
device/register                    # 장치 등록
device/{ip_address}/state         # IP 기반 상태 발행
device/{ip_address}/command       # IP 기반 명령 수신
device/{device_id}/state          # ID 기반 상태 발행  
device/{device_id}/command        # ID 기반 명령 수신
```

### 지원 명령

| 명령 | 설명 | 매개변수 |
|------|------|----------|
| `GAME_START` | 게임 시작/진행 | - |
| `GAME_STOP` | 게임 중지 (점수 표시) | - |
| `GAME_RESET` | 게임 초기화 | - |
| `VOLUME` | 볼륨 조절 | 0.0-1.0 |

## 🎵 사운드 시스템

### 상태별 사운드 매핑

| 상태 | 파일명 | 설명 |
|------|--------|------|
| INIT | `init.mp3` | 시스템 초기화 |
| WAITING | `wait.wav` | 대기 상태 |
| COUNTDOWN | `countdown.wav` | 카운트다운 |
| PLAYING | `playing_{type}.wav` | 게임별 BGM (1-6) |
| SCORE | `score.wav` | 점수 표시 |
| RESULT | `result.wav` | 결과 화면 |
| ENTER | `enter.wav` | 입장 화면 |
| EXIT | `exit.wav` | 퇴장 화면 |

### 볼륨 제어
- **범위**: 0.0 (무음) ~ 1.0 (최대)
- **BGM**: 배경음악 (루프 재생)
- **SFX**: 효과음 (단발 재생)

## 🧪 테스트 모드

테스트 모드에서는 키보드 입력으로 게임을 제어할 수 있습니다:

| 키 | 동작 |
|----|------|
| **A** | 게임 시작/카운트다운 |
| **B** | 점수 표시 (플레이 중) |
| **ESC** | 프로그램 종료 |

```bash
# 테스트 모드 실행
python3 pop-client.py --type 5 --device_id 5 --test
```

## 📁 프로젝트 구조

```
samyang-pop-client/
├── pop-client.py              # 메인 엔트리 포인트
├── gigs.py                   # 핵심 게임 클래스
├── requirements.txt          # Python 의존성
├── README.md                # 프로젝트 문서
│
├── Module/                   # 핵심 모듈
│   ├── game_handler.py      # 게임 로직 처리
│   ├── game_state.py        # 게임 상태 관리
│   ├── screen_manager.py    # 화면 표시 관리
│   ├── sound_manager.py     # 사운드 관리 (싱글톤)
│   ├── mqtt_manager.py      # MQTT 통신 관리
│   ├── serial_handler.py    # 시리얼 통신
│   ├── tcp_handler.py       # TCP 통신
│   ├── input_handler.py     # 입력 처리
│   ├── score_manager.py     # 점수 관리
│   ├── command_handler.py   # 명령 처리
│   ├── mqtt_client.py       # MQTT 클라이언트
│   ├── mqtt_scanner.py      # MQTT 브로커 스캔
│   └── local_ip_resolver.py # IP 주소 확인
│
├── ESP32/                    # ESP32 펌웨어
│   ├── geekble-nano-handler/
│   ├── rfid-button-handler/
│   └── rfid-start-handler/
│
├── Shell/                    # 자동 시작 스크립트
│   ├── AutoStart_Enter.sh
│   ├── AutoStart_Exit.sh
│   ├── AutoStart_Game_Basketball.sh
│   ├── AutoStart_Game_Burger.sh
│   ├── AutoStart_Game_Pool.sh
│   ├── AutoStart_Game_Rowing.sh
│   ├── AutoStart_Game_Siso.sh
│   └── AutoStart_Game_Sleep.sh
│
├── Sound/                    # 사운드 파일
│   ├── init.mp3
│   ├── wait.wav
│   ├── countdown.wav
│   ├── playing_1.wav ~ playing_6.wav
│   ├── score.wav
│   ├── result.wav
│   ├── enter.wav
│   ├── exit.wav
│   └── Legacy/               # 레거시 사운드
│
├── Image/                    # 이미지 자원
│   └── bg.png               # 배경 이미지
│
├── Font/                     # 폰트 파일
│   └── RoundSquare.ttf      # 게임 폰트
│
└── Example/                  # 예제 코드
    ├── audio_test.py
    └── tcp-server.py
```

## 🔗 핵심 의존성

| 라이브러리 | 용도 | 버전 |
|------------|------|------|
| `pygame` | 화면 및 사운드 관리 | 2.6.1 |
| `paho-mqtt` | MQTT 통신 | 1.6.1 |
| `pyserial` | 시리얼 통신 | 3.5 |
| `keyboard` | 키보드 입력 처리 | 0.13.5 |

## 🚨 주의사항

1. **MQTT 브로커**: 최대 0.3초 타임아웃으로 네트워크 스캔
2. **연결 필수**: 초기 연결 실패 시 프로그램 자동 종료
3. **장치 등록**: MQTT 연결 후 반드시 등록 메시지 발행
4. **타이머 설정**: 게임 플레이 60초, 점수 대기 15초 (설정 가능)
5. **스레드 안전**: 화면 업데이트는 메인 스레드에서만 실행
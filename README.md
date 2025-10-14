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

# 입장
python3 pop-client.py --enter

# 퇴장
python3 pop-client.py --exit

# 특정 게임 실행 (농구 게임)
python3 pop-client.py --type 6

# 테스트 모드 (키보드 입력 활성화)
python3 pop-client.py --type  --test
```

### 3. 라즈베리파이 부팅 시 자동 실행

```bash
# 실행 권한 부여
chmod +x Shell/AutoStart_Game_Basketball.sh

# 크론탭 설정
crontab -e

# 다음 라인 추가:
# @reboot /home/pi/gigs-system/gigs-tower-client/gigs-tower/Shell/AutoStart_Game_Basketball.sh
```

## 🎮 지원 게임

| 게임 타입 | 게임명                | 설명                     |
| --------- | --------------------- | ------------------------ |
| 1         | 헬시 버거 챌린지      | 건강한 버거 만들기 게임  |
| 2         | 꿀잠 방해꾼 OUT!      | 수면 방해 요소 제거 게임 |
| 3         | 불태워! 칼로링머신    | 칼로리 소모 운동 게임    |
| 4         | 볼볼볼 영양소         | 영양소 수집 게임         |
| 5         | 바이오데이터 에어시소 | 균형 감각 게임           |
| 6         | 슛잇! 무빙 골대       | 농구 슈팅 게임           |
| 7         | 입장 화면             | 플레이어 입장 전용       |
| 8         | 퇴장 화면             | 플레이어 퇴장 전용       |

## 🏗️ 시스템 아키텍처

### 전체 구조

```
┌─────────────────┐    ┌─────────────────────────────────────────┐
│   ESP32 RFID    │───▶│           Game Client                   │
│   Card Reader   │    │         (Python/Pygame)                 │
│   (115200 baud) │    │                                         │
└─────────────────┘    │  ┌──────────────────────────────────┐   │
                       │  │     Core Components              │   │
                       │  │  • GameStateManager              │   │
                       │  │  • GameActionHandler             │   │
                       │  │  • ScreenManager (Pygame)        │   │
┌─────────────────┐    │  │  • SoundManager (Singleton)      │   │
│  MQTT Broker    │◀──▶│  │  • SerialHandler                 │   │
│   (Port 1883)   │    │  │  • MQTTManager                   │   │
└─────────────────┘    │  │  • ScoreManager                  │   │
                       │  └──────────────────────────────────┘   │
                       └─────────────────────────────────────────┘
                                       │
                       ┌───────────────┼───────────────┐
                       ▼               ▼               ▼
              ┌────────────┐  ┌────────────┐  ┌────────────┐
              │   Serial   │  │   MQTT     │  │  Display   │
              │   Events   │  │  Commands  │  │  Updates   │
              └────────────┘  └────────────┘  └────────────┘
```

### 핵심 컴포넌트

#### 1. GIGS (gigs.py)

- 메인 게임 클래스, 모든 컴포넌트를 통합 관리
- 게임 초기화 및 메인 루프 실행
- 컴포넌트 간 의존성 주입 관리

#### 2. GameStateManager (Module/game/game_state.py)

- 게임 상태 관리 (INIT, WAITING, COUNTDOWN, PLAYING, SCORE, RESULT, ENTER, EXIT, TAG, ERROR)
- 상태 전환 로직 및 타이머 관리
- MQTT를 통한 상태 발행

#### 3. GameActionHandler (Module/game/game_action_handler.py)

- 이벤트 처리 통합 핸들러 (Serial, MQTT, Keyboard)
- RFID 태그 검증 및 서버 응답 처리
- 게임 명령 처리 (START, STOP, RESET)
- 마스터 카드 특권 처리

#### 4. ScreenManager (Module/interface/screen_manager.py)

- Pygame 기반 화면 표시 관리
- 스레드 안전 메시지 큐
- 배경 이미지 및 텍스트 렌더링

#### 5. SoundManager (Module/interface/sound_manager.py)

- 싱글톤 패턴 사운드 관리
- BGM 및 SFX 재생
- 볼륨 제어 및 음소거 기능
- idempotent BGM 루프 (중복 재생 방지)

#### 6. SerialHandler (Module/serial/serial_handler.py)

- ESP32와의 시리얼 통신 (115200 baud)
- 다중 시리얼 포트 자동 감지 및 연결
- RFID 태그 및 점수 데이터 수신
- 자동 재연결 및 에러 복구

#### 7. MQTTManager (Module/mqtt/mqtt_manager.py)

- MQTT 브로커 자동 검색 및 연결
- 명령 수신 및 처리 (Command Pattern)
- 상태 발행 및 ACK/ERR 응답 처리
- 장치 등록 및 연결 유지

#### 8. ScoreManager (Module/interface/score_manager.py)

- 게임 점수 관리
- 점수 추가 및 조회

#### 9. InputHandler (Module/interface/input_handler.py)

- Pygame 이벤트 처리
- 테스트 모드 키보드 입력 (A: RFID, B: Score, ESC: Exit)

## 📋 명령행 옵션

| 옵션                | 설명                      | 기본값    |
| ------------------- | ------------------------- | --------- |
| `--type`            | 게임 타입 (1-8)           | 1         |
| `--device_id`       | 장치 식별 ID              | type 값   |
| `--test`            | 테스트 모드 (키보드 입력) | False     |
| `--enter`           | 입장 화면 표시            | False     |
| `--exit`            | 퇴장 화면 표시            | False     |
| `--score-wait-time` | 점수 대기 시간 (초)       | 15        |
| `--countdown-time`  | 카운트다운 시간 (초)      | 10        |
| `--mqtt-broker`     | MQTT 브로커 주소          | 자동 검색 |

## 🎯 게임 상태 흐름

```
     시작
      │
   ┌──▼──┐
   │INIT │
   └──┬──┘
      │
   ┌──▼──┐
   │WAIT │ ◄─────────┐
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

특수 상태:
- TAG: RFID 태그 인식 중
- ERROR: 에러 발생 및 자동 복구
- ENTER: 플레이어 입장 화면
- EXIT: 플레이어 퇴장 화면
```

## 🔧 하드웨어 요구사항

### ESP32 설정

- **RFID 모듈**: PN532 (SPI 연결)
- **시리얼 통신**: 115200 baud
- **카드 감지**: 8자리 UID 또는 'a' 문자 전송
- **점수 전송**: 숫자 값 전송

### 화면 설정

- **해상도**: 전체화면 (FULLSCREEN)
- **마진**: 좌측 0px, 상단 0px, 우측 0px, 하단 0px
- **폰트**: RoundSquare.ttf (30pt)
- **배경**: Image/bg.png

## 📡 통신 프로토콜

### MQTT 토픽 구조

```
device/register                        # 장치 등록
device/{ip_address}/state              # IP 기반 상태 발행
device/{ip_address}/command            # IP 기반 명령 수신
device/{device_id}/state               # ID 기반 상태 발행
device/{device_id}/command             # ID 기반 명령 수신
device/{device_id}/state/ack           # 상태 응답 (정상)
device/{device_id}/state/err           # 상태 응답 (에러)
device/{device_id}/player_feedback     # 플레이어 피드백
device/command/broadcast               # 브로드캐스트 명령
```

### 지원 명령

| 명령          | 설명                  | 매개변수 |
| ------------- | --------------------- | -------- |
| `GAME_START`  | 게임 시작/진행        | -        |
| `GAME_STOP`   | 게임 중지 (점수 표시) | -        |
| `GAME_RESET`  | 게임 초기화           | -        |
| `VOLUME`      | 볼륨 조절             | 0.0-1.0  |
| `MUTE_ON`     | 음소거 켜기           | -        |
| `MUTE_OFF`    | 음소거 끄기           | -        |
| `MUTE_TOGGLE` | 음소거 토글           | -        |
| `PING`        | 연결 확인             | -        |

### 상태 메시지 페이로드

```json
{
  "device_id": "6",
  "game_type": 6,
  "game_name": "슛잇! 무빙 골대",
  "state": "PLAYING",
  "progress_state": "INPROGRESS",
  "rfid": "ABCD1234",
  "score": 100,
  "timestamp": "2025-10-14T12:34:56",
  "replyTo": "device/6/state",
  "correlationId": "550e8400-e29b-41d4-a716-446655440000"
}
```

## 🎵 사운드 시스템

### 상태별 사운드 매핑

| 상태      | 파일명               | 설명             | 재생 방식 |
| --------- | -------------------- | ---------------- | --------- |
| INIT      | `init.mp3`           | 시스템 초기화    | BGM       |
| WAITING   | `wait.wav`           | 대기 상태        | BGM Loop  |
| COUNTDOWN | `countdown.wav`      | 카운트다운       | BGM       |
| PLAYING   | `playing_{type}.wav` | 게임별 BGM (1-6) | BGM Loop  |
| SCORE     | `score.wav`          | 점수 표시        | BGM       |
| RESULT    | `result.wav`         | 결과 화면        | BGM       |
| ENTER     | `enter.wav`          | 입장 화면        | BGM Loop  |
| EXIT      | `exit.wav`           | 퇴장 화면        | BGM Loop  |

### SFX (효과음)

| 이벤트      | 파일명           | 설명             |
| ----------- | ---------------- | ---------------- |
| 태그 시작   | `tag_start.wav`  | RFID 태그 인식   |
| 태그 종료   | `tag_end.wav`    | 게임 종료 태그   |
| 태그 에러   | `tag_error.wav`  | 태그 검증 실패   |
| 마스터 카드 | `tag_master.wav` | 마스터 카드 인식 |

### 볼륨 제어

- **범위**: 0.0 (무음) ~ 1.0 (최대)
- **BGM**: 배경음악 (루프 재생, idempotent)
- **SFX**: 효과음 (단발 재생, BGM에 영향 없음)

## 🧪 테스트 모드

테스트 모드에서는 키보드 입력으로 게임을 제어할 수 있으며, 개발/디버그를 위해 카운트다운 시간이 1초로 단축됩니다:

| 키      | 동작                                               |
| ------- | -------------------------------------------------- |
| **A**   | Mock RFID 이벤트 발생 (8자리 테스트 UID: QWER1234) |
| **B**   | Mock 점수 +10 이벤트 발생                          |
| **ESC** | 프로그램 종료                                      |

- **카운트다운 단축**: 테스트 모드에서는 countdown_time이 1초로 설정되어 빠른 테스트 가능

```bash
# 테스트 모드 실행
python3 pop-client.py --type 5 --test
```

## 📁 프로젝트 구조

```
gigs-tower-client/
├── README.md                          # 프로젝트 문서
│
└── gigs-tower/                        # 게임 클라이언트 메인 코드
    ├── pop-client.py                  # 메인 엔트리 포인트
    ├── gigs.py                        # 핵심 게임 클래스 (GIGS)
    ├── paths.py                       # 경로 헬퍼 유틸리티
    ├── requirements.txt               # Python 의존성
    │
    ├── Module/                        # 핵심 모듈 (패키지 구조)
    │   ├── __init__.py
    │   │
    │   ├── game/                      # 게임 로직 모듈
    │   │   ├── __init__.py
    │   │   ├── game_state.py          # 게임 상태 관리 (GameStateManager)
    │   │   ├── game_action_handler.py # 이벤트 처리 통합 핸들러
    │   │   ├── game_handler.py        # 게임 명령 처리
    │   │   ├── game_type_strategy.py  # 게임 타입별 전략 패턴
    │   │   ├── events.py              # 이벤트 타입 정의
    │   │   └── error_type.py          # 에러 타입 정의
    │   │
    │   ├── interface/                 # UI/UX 인터페이스 모듈
    │   │   ├── __init__.py
    │   │   ├── screen_manager.py      # 화면 표시 관리 (Pygame)
    │   │   ├── sound_manager.py       # 사운드 관리 (싱글톤)
    │   │   ├── input_handler.py       # 입력 처리 (키보드/이벤트)
    │   │   └── score_manager.py       # 점수 관리
    │   │
    │   ├── mqtt/                      # MQTT 통신 모듈
    │   │   ├── __init__.py
    │   │   ├── mqtt_manager.py        # MQTT 연결 및 명령 관리
    │   │   ├── mqtt_client.py         # MQTT 클라이언트 래퍼
    │   │   └── mqtt_scanner.py        # MQTT 브로커 자동 검색
    │   │
    │   ├── serial/                    # 시리얼 통신 모듈
    │   │   ├── __init__.py
    │   │   └── serial_handler.py      # 시리얼 통신 (ESP32)
    │   │
    │   ├── command/                   # 명령 처리 모듈
    │   │   ├── __init__.py
    │   │   └── command_handler.py     # 명령 디스패처 (Command Pattern)
    │   │
    │   ├── config/                    # 설정 모듈
    │   │   ├── __init__.py
    │   │   ├── game_config.py         # 게임 설정 상수
    │   │   └── message_loader.py      # 메시지 로더 (다국어 지원)
    │   │
    │   └── utils/                     # 유틸리티 모듈
    │       ├── __init__.py
    │       ├── local_ip_resolver.py   # 로컬 IP 확인
    │       └── net_utils.py           # 네트워크 유틸리티
    │
    ├── Shell/                         # 자동 시작 스크립트
    │   ├── AutoStart_Enter.sh
    │   ├── AutoStart_Exit.sh
    │   └── AutoStart_Game_*.sh        # 게임별 자동 시작 스크립트
    │
    ├── Sound/                         # 사운드 파일
    │   ├── init.mp3
    │   ├── wait.wav
    │   ├── countdown.wav
    │   ├── playing_1.wav ~ playing_6.wav
    │   ├── score.wav
    │   ├── result.wav
    │   ├── enter.wav
    │   ├── exit.wav
    │   ├── tag_start.wav              # SFX: 태그 시작
    │   ├── tag_end.wav                # SFX: 태그 종료
    │   ├── tag_error.wav              # SFX: 태그 에러
    │   ├── tag_master.wav             # SFX: 마스터 카드
    │   └── Legacy/                    # 레거시 사운드
    │
    ├── Image/                         # 이미지 자원
    │   └── bg.png                     # 배경 이미지
    │
    ├── Font/                          # 폰트 파일
    │   └── RoundSquare.ttf            # 게임 폰트
    │
    └── Example/                       # 예제 코드
        └── audio_test.py              # 오디오 테스트
```

## 🔗 핵심 의존성

| 라이브러리  | 용도                | 버전   |
| ----------- | ------------------- | ------ |
| `pygame`    | 화면 및 사운드 관리 | 2.6.1  |
| `paho-mqtt` | MQTT 통신           | 1.6.1  |
| `pyserial`  | 시리얼 통신         | 3.5    |
| `keyboard`  | 키보드 입력 처리    | 0.13.5 |

## 🚨 주요 기능

### 1. 자동 브로커 검색

- 로컬 네트워크에서 MQTT 브로커 자동 검색
- 최대 0.6초 타임아웃, 50개 스레드 병렬 스캔
- 선호 네트워크 인터페이스 우선 검색

### 2. 서버 검증 시스템

- RFID 태그 시 서버 검증 필수
- correlationId 기반 응답 대기
- ACK/ERR 메시지 처리
- 네트워크 에러 자동 복구

### 3. 에러 처리 및 복구

- ERROR 상태 자동 전환
- 설정 가능한 자동 복구 시간
- 이전 상태로 복구 (ENTER, EXIT, WAITING)
- 게임 차단 및 해제 관리

### 4. 마스터 카드 시스템

- 설정된 마스터 RFID로 특권 실행
- 에러 상태 강제 해제
- 짧은 카운트다운 (1초)
- 모든 검증 우회

### 5. 게임 타입별 전략 패턴

- 각 게임 타입별 검증 로직 분리
- ENTER/EXIT/GAME 모드별 처리
- 확장 가능한 전략 패턴 구조

### 6. 스레드 안전 화면 업데이트

- 메시지 큐 기반 화면 업데이트
- 메인 스레드에서만 Pygame 렌더링
- 다중 스레드 환경 지원

### 7. 시리얼 다중 포트 관리

- 여러 시리얼 포트 동시 연결
- 자동 재연결 및 복구
- DTR 리셋 지원

## 🔒 보안 및 검증

### RFID 검증 흐름

```
1. RFID 태그 감지 (Serial)
2. 게임 상태 확인 (차단 조건)
3. 중복 태그 방지 체크
4. 서버 검증 요청 (TAG 상태 발행)
5. correlationId 기반 응답 대기
6. ACK/ERR 응답 처리
7. 게임 타입별 전략 실행
```

### 에러 코드

| 코드                       | 설명                 | 복구 전략 |
| -------------------------- | -------------------- | --------- |
| `PLAYER_DUPLICATE_ENTER`   | 입장 중복            | 에러 표시 |
| `PLAYERGAME_DUPLICATE`     | 게임 중복 실행       | 에러 표시 |
| `PLAYER_NOT_FOUND_GAME`    | 게임 플레이어 미발견 | 에러 표시 |
| `PLAYER_NOT_FOUND_EXIT`    | 퇴장 플레이어 미발견 | 에러 표시 |
| `GAME_DUPLICATE_EXECUTION` | 게임 중복 실행       | 에러 표시 |
| `NETWORK_ERROR`            | 네트워크 연결 실패   | 자동 복구 |
| `TAG_BLOCKED`              | 게임 중 태그 차단    | 일시 표시 |
| `TAG_DUPLICATE`            | 중복 태그            | 일시 표시 |

## 📊 설정 (game_config.py)

```python
GAME_PLAY_TIMEOUT = 60              # 게임 플레이 제한 시간 (초)
SCORE_DISPLAY_WAIT = 15             # 점수 표시 대기 시간 (초)
RESULT_DISPLAY_WAIT = 5             # 결과 표시 대기 시간 (초)
COUNTDOWN_TIME = 10                 # 카운트다운 시간 (초)
ERROR_AUTO_RECOVERY_DELAY = 10      # 에러 자동 복구 시간 (초)
SERVER_VALIDATION_TIMEOUT = 5.0     # 서버 검증 타임아웃 (초)
SERVER_RESPONSE_CHECK_INTERVAL = 0.05  # 응답 체크 간격 (초)
TAG_DUPLICATE_DELAY = 1             # 중복 태그 메시지 표시 시간 (초)
EXIT_SUCCESS_HOLD = 3               # 퇴장 성공 메시지 유지 시간 (초)
MASTER_COUNTDOWN_TIME = 1           # 마스터 카드 카운트다운 시간 (초)
MASTER_RFID_CARDS = ["MASTER01"]    # 마스터 카드 RFID 목록
MAX_PENDING_RESPONSES = 10          # 최대 대기 응답 수
CLEANUP_RESPONSE_COUNT = 5          # 응답 정리 개수
```

## 🐛 디버깅

### 로그 레벨

```python
[SERIAL] - 시리얼 통신 로그
[MQTT] - MQTT 통신 로그
[GameState] - 게임 상태 로그
[Action] - 액션 핸들러 로그
[Validation] - 서버 검증 로그
[ERROR] - 에러 로그
[MASTER] - 마스터 카드 로그
[Performance] - 성능 측정 로그
```

### 추적 로그

```python
[TRACE] - 상세 추적 로그 (RFID 처리 흐름)
[DEBUG] - 디버그 정보 (응답 대기, 상태 변경)
```

## 📝 라이선스

이 프로젝트는 GIGS 시스템의 일부입니다.

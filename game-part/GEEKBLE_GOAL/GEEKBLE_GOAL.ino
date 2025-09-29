// ---------------------------
// 설정 파라미터
// ---------------------------
const int TRIG_1 = 6;
const int ECHO_1 = 3;

const int TRIG_2 = 7;
const int ECHO_2 = 2;

const int DIST_THRESHOLD = 15;    // cm 이하일 때 감지로 판단
const int DEAD_TIME = 500;        // ms, 중복 감지 방지 시간
const int SENSOR_TIMEOUT = 30000; // us, pulseIn 타임아웃 (30ms = 약 5m 거리)
const bool NOECHO_IS_HIT = true; // true → No echo도 감지 성공으로 간주, false → 실패로 간주

// ---------------------------
// 함수
// ---------------------------
float sensing(int trig, int echo) {
  digitalWrite(trig, LOW);
  delayMicroseconds(2);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);

  long duration = pulseIn(echo, HIGH, SENSOR_TIMEOUT);
  if (duration == 0) {
    if (NOECHO_IS_HIT) return 0;   // No echo도 감지로 처리
    else return -1;                // 감지 실패
  }
  float distance = duration * 0.0343 / 2;  // cm
  return distance;
}

// ---------------------------
// 아두이노 기본 구조
// ---------------------------
void setup() {
  Serial.begin(115200);
  pinMode(TRIG_1, OUTPUT); 
  pinMode(ECHO_1, INPUT);
  pinMode(TRIG_2, OUTPUT); 
  pinMode(ECHO_2, INPUT);
}

void loop() {
  float d1 = sensing(TRIG_1, ECHO_1);
  delay(10); // 두 센서 신호 겹침 방지
  float d2 = sensing(TRIG_2, ECHO_2);

  // 감지 조건 체크
  bool hit1 = (d1 > 0 && d1 <= DIST_THRESHOLD);
  bool hit2 = (d2 > 0 && d2 <= DIST_THRESHOLD);

  if (hit1 || hit2 || (NOECHO_IS_HIT && (d1 == 0 || d2 == 0))) {
    Serial.println("10");
    delay(DEAD_TIME); // 중복 감지 방지
  }

  // 디버그 출력
  // Serial.print("Sensor1: ");
  // if (d1 < 0) Serial.print("No echo");
  // else Serial.print(d1);
  // Serial.print(" cm | Sensor2: ");
  // if (d2 < 0) Serial.print("No echo");
  // else Serial.print(d2);
  // Serial.println(" cm");

  delay(50);
}

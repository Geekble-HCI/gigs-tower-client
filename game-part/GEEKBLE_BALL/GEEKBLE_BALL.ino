#define TRIG_1 17
#define TRIG_2 16
#define TRIG_3 10
#define TRIG_4 11
#define TRIG_5 21
#define TRIG_6 20
#define TRIG_7 19
#define TRIG_8 18

#define ECHO_1 6
#define ECHO_2 7
#define ECHO_3 8
#define ECHO_4 9
#define ECHO_5 2
#define ECHO_6 3
#define ECHO_7 4
#define ECHO_8 5

int16_t dead_time = 150;
int16_t d_goal = 2650;

uint16_t T = 0;
uint16_t T_prev = 0;
uint16_t dt = 0;

uint16_t Period_ping = 10;
uint16_t T_ping = 0;

int16_t T_1 = 0; int16_t T_2 = 0; int16_t T_3 = 0; int16_t T_4 = 0;
int16_t T_5 = 0; int16_t T_6 = 0; int16_t T_7 = 0; int16_t T_8 = 0;

uint16_t T_trig = 0;

uint16_t T_echo_1 = 0; uint16_t T_echo_2 = 0; uint16_t T_echo_3 = 0; uint16_t T_echo_4 = 0;
uint16_t T_echo_5 = 0; uint16_t T_echo_6 = 0; uint16_t T_echo_7 = 0; uint16_t T_echo_8 = 0;

int8_t s1 = 0; int8_t s2 = 0; int8_t s3 = 0; int8_t s4 = 0;
int8_t s5 = 0; int8_t s6 = 0; int8_t s7 = 0; int8_t s8 = 0;
int8_t s1_prev = 0; int8_t s2_prev = 0; int8_t s3_prev = 0; int8_t s4_prev = 0;
int8_t s5_prev = 0; int8_t s6_prev = 0; int8_t s7_prev = 0; int8_t s8_prev = 0;

uint16_t score = 0;
uint8_t mode = 'm';

float d1 = 0; float d2 = 0; float d3 = 0; float d4 = 0;
float d5 = 0; float d6 = 0; float d7 = 0; float d8 = 0;


void update(){  // echo pin state flip sensing
  s1_prev = s1;
  s2_prev = s2;
  s3_prev = s3;
  s4_prev = s4;
  s5_prev = s5;
  s6_prev = s6;
  s7_prev = s7;
  s8_prev = s8;
  s1 = digitalRead(ECHO_1);
  s2 = digitalRead(ECHO_2);
  s3 = digitalRead(ECHO_3);
  s4 = digitalRead(ECHO_4);
  s5 = digitalRead(ECHO_5);
  s6 = digitalRead(ECHO_6);
  s7 = digitalRead(ECHO_7);
  s8 = digitalRead(ECHO_8);
  if(T_1 <= 0){
    if(s1 == LOW && s1_prev == HIGH) {
      T_echo_1 = micros() - T_trig;
      if(T_echo_1 < d_goal){
        score += 1;
        Serial.println('2');
        T_1 += dead_time;
      }
    }
  }else{ T_1 -= dt; }

  if(T_2 <= 0){
    if(s2 == LOW && s2_prev == HIGH) {
      T_echo_2 = micros() - T_trig;
      if(T_echo_2 < d_goal){
        score += 1;
        Serial.println('2');
        T_2 += dead_time;
      }
    }
  }else{ T_2 -= dt; }

  if(T_3 <= 0){
    if(s3 == LOW && s3_prev == HIGH) {
      T_echo_3 = micros() - T_trig;
      if(T_echo_3 < d_goal){
        score += 1;
        Serial.println('2');
        T_3 += dead_time;
      }
    }
  }else{ T_3 -= dt; }

  if(T_4 <= 0){
    if(s4 == LOW && s4_prev == HIGH) {
      T_echo_4 = micros() - T_trig;
      if(T_echo_4 < d_goal){
        score += 1;
        Serial.println('2');
        T_4 += dead_time;
      }
    }
  }else{ T_4 -= dt; }

  if(T_5 <= 0){
    if(s5 == LOW && s5_prev == HIGH) {
      T_echo_5 = micros() - T_trig;
      if(T_echo_5 < d_goal){
        score += 1;
        Serial.println('2');
        T_5 += dead_time;
      }
    }
  }else{ T_5 -= dt; }

  if(T_6 <= 0){
    if(s6 == LOW && s6_prev == HIGH) {
      T_echo_6 = micros() - T_trig;
      if(T_echo_6 < d_goal){
        score += 1;
        Serial.println('2');
        T_6 += dead_time;
      }
    }
  }else{ T_6 -= dt; }

  if(T_7 <= 0){
    if(s7 == LOW && s7_prev == HIGH) {
      T_echo_7 = micros() - T_trig;
      if(T_echo_7 < d_goal){
        score += 1;
        Serial.println('2');
        T_7 += dead_time;
      }
    }
  }else{ T_7 -= dt; }

  if(T_8 <= 0){
    if(s8 == LOW && s8_prev == HIGH) {
      T_echo_8 = micros() - T_trig;
      if(T_echo_8 < d_goal){
        score += 1;
        Serial.println('2');
        T_8 += dead_time;
      }
    }
  }else{ T_8 -= dt; }


}

void trig(){  // all sensor's trigging is syncronized
    digitalWrite(TRIG_1, LOW); digitalWrite(TRIG_2, LOW);
    digitalWrite(TRIG_3, LOW); digitalWrite(TRIG_4, LOW);
    digitalWrite(TRIG_5, LOW); digitalWrite(TRIG_6, LOW);
    digitalWrite(TRIG_7, LOW); digitalWrite(TRIG_8, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_1, HIGH); digitalWrite(TRIG_2, HIGH);
    digitalWrite(TRIG_3, HIGH); digitalWrite(TRIG_4, HIGH);
    digitalWrite(TRIG_5, HIGH); digitalWrite(TRIG_6, HIGH);
    digitalWrite(TRIG_7, HIGH); digitalWrite(TRIG_8, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_1, LOW); digitalWrite(TRIG_2, LOW);
    digitalWrite(TRIG_3, LOW); digitalWrite(TRIG_4, LOW);
    digitalWrite(TRIG_5, LOW); digitalWrite(TRIG_6, LOW);
    digitalWrite(TRIG_7, LOW); digitalWrite(TRIG_8, LOW);
}

float sensing(int trig, int echo){  // test function
    digitalWrite(trig, LOW);
    delayMicroseconds(2);
    digitalWrite(trig, HIGH);
    delayMicroseconds(10);
    digitalWrite(trig, LOW);
    long duration = pulseIn(echo, HIGH);
    float distance = duration * 0.0343 / 2;  
    return distance;
}

void setup() {
    Serial.begin(115200);
    pinMode(TRIG_1, OUTPUT); pinMode(ECHO_1, INPUT);
    pinMode(TRIG_2, OUTPUT); pinMode(ECHO_2, INPUT);
    pinMode(TRIG_3, OUTPUT); pinMode(ECHO_3, INPUT);
    pinMode(TRIG_4, OUTPUT); pinMode(ECHO_4, INPUT);
    pinMode(TRIG_5, OUTPUT); pinMode(ECHO_5, INPUT);
    pinMode(TRIG_6, OUTPUT); pinMode(ECHO_6, INPUT);
    pinMode(TRIG_7, OUTPUT); pinMode(ECHO_7, INPUT);
    pinMode(TRIG_8, OUTPUT); pinMode(ECHO_8, INPUT);
}

void loop() {
  T_prev = T;
  T = millis();
  dt = T - T_prev;

  T_ping += dt;
  if(T_ping >= Period_ping){
    T_ping -= Period_ping;
    trig();
    T_trig = micros();
  }
  update();

}

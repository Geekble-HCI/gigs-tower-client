// PRIMARY SENSOR PIN
//#define TRIG_1 7
//#define ECHO_1 2

// SPARE SENSOR PIN
#define TRIG_1 6
#define ECHO_1 3


int16_t dead_time = 2000;
int16_t d_goal = 2800;

uint16_t T = 0;
uint16_t T_prev = 0;
uint16_t dt = 0;

uint16_t Period_ping = 25;
uint16_t T_ping = 0;

int16_t T_1 = 0;

uint16_t T_trig = 0;

uint16_t T_echo_1 = 0;

int8_t s1 = 0;
int8_t s1_prev = 0;

uint16_t score = 0;
uint8_t mode = 'm';

float d1 = 0;


void update(){
  s1_prev = s1;
  s1 = digitalRead(ECHO_1);


  if(T_1 <= 0){
    if(s1 == LOW && s1_prev == HIGH) {
      T_echo_1 = micros() - T_trig;
      if(T_echo_1 < d_goal){
        Serial.println("10");
        T_1 += dead_time;
      }
    }
  }else{ T_1 -= dt; }
}

void trig(){
    digitalWrite(TRIG_1, LOW);
    delayMicroseconds(2);
    digitalWrite(TRIG_1, HIGH);
    delayMicroseconds(10);
    digitalWrite(TRIG_1, LOW);
}

float sensing(int trig, int echo){
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

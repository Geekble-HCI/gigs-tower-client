#define SELECT_AXIS 'x'
// #define SELECT_AXIS 'y'
// #define SELECT_AXIS 'z'


int16_t bias = -60;  // horizontal bias

char c;

double x = 0;
double y = 0;
double z = 0;

double axis_value = 0;
double axis_sign = 0;
double axis_sign_prev = 0;

uint16_t T = 0;
uint16_t T_prev = 0;
uint16_t dt = 0;
int16_t T_dead = 0;
int16_t dead_time = 20;

int16_t T_ser = 0;
int16_t Period_ser = 100;


int16_t score = 0;

void setup() {
  Serial.begin(115200);

  Serial1.setTX(12);
  Serial1.setRX(13);
  Serial1.begin(115200);
}

void loop() {
  T_prev = T;
  T = micros();
  dt = T - T_prev;
  T_ser += dt;
  if(T_ser >= Period_ser){
    T_ser -= Period_ser;
    if(Serial1.available()) {
      c = Serial1.read();
      if(c == '*'){
        x = Serial1.parseFloat() - bias;
        y = Serial1.parseFloat() - bias;
        z = Serial1.parseFloat() - bias;

        if(SELECT_AXIS == 'x'){ axis_value = x; }
        if(SELECT_AXIS == 'y'){ axis_value = y; }
        if(SELECT_AXIS == 'z'){ axis_value = z; }

        axis_sign_prev = axis_sign;
        if(axis_value > 0){ axis_sign = 1; }
        else { axis_sign = 0; }

        if(T_dead <= 0){
          if(axis_sign != axis_sign_prev){
            Serial.println('1');
            score += 1;
            T_dead += dead_time;
          }
        }else{ T_dead -= dt; }
      }
    }
    //Serial.println(axis_value);
  }
}

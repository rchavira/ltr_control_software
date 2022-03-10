#define mux_s0 9
#define mux_s1 10
#define mux_s2 11
#define mux_s3 12
#define mux_sig 2
#define mux_en 8
#define t_sense A4


int f_cnt = 0;

void cntr() {
  f_cnt++;
}

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  pinMode(mux_s0, OUTPUT);
  pinMode(mux_s1, OUTPUT);
  pinMode(mux_s2, OUTPUT);
  pinMode(mux_s3, OUTPUT);
  pinMode(mux_en, OUTPUT);

  digitalWrite(mux_en, HIGH);  //disable mux chip (for now...)
}

void enableInterrupt() {
  attachInterrupt(digitalPinToInterrupt(mux_sig), cntr, FALLING);  //pulse counter for reading fan tag
}

void disableInterrupt() {
  detachInterrupt(digitalPinToInterrupt(mux_sig));  //pulse counter for reading fan tag
}


void loop() {
  // put your main code here, to run repeatedly:
  int rpm = 0;
  for(int i=0;i<8;i++){
    rpm = get_rpm(i);
    Serial.print("Channel[");
    Serial.print(i);
    Serial.print("]_rpm:");
    Serial.print(rpm);
    Serial.println();
  }
  read_temp();
}


float mapfloat(float x, float in_min, float in_max, float out_min, float out_max)
{
  return (float)(x - in_min) * (out_max - out_min) / (float)(in_max - in_min) + out_min;
}

void read_temp() {
  int t_in = analogRead(t_sense);
  float tmp_v = mapfloat(t_in, 0, 1023, 0, 5);
  float t_C = mapfloat(tmp_v, 0.5, 2.5, 0, 120);
  Serial.print("Temperature:");
  Serial.print(t_C);
  Serial.println();
}


void setMux(int ch) {
  digitalWrite(mux_s0, bitRead(0, ch) ? HIGH : LOW);
  digitalWrite(mux_s1, bitRead(1, ch) ? HIGH : LOW);
  digitalWrite(mux_s2, bitRead(2, ch) ? HIGH : LOW);
  digitalWrite(mux_s3, bitRead(3, ch) ? HIGH : LOW);
}

int get_rpm(int ch){
  f_cnt = 0;
  digitalWrite(mux_en, LOW);
  setMux(ch);
  enableInterrupt();
  delay(1000);
  disableInterrupt();
  digitalWrite(mux_en, HIGH);
  return f_cnt * 60;
}

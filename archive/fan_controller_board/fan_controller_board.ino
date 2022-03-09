/*
   fan_controller_board v1 firmware
   Author: Ricardo Chavira

   This firmware is to control the fan controller board v1 design.
   This is to be uploaded to an Arduino Nano that is onboard the PCB.

   This project communicates to an onboard PCA9685 adafruit 16 channel
   PWM driver board with the default address of 0x40.

   It is also attatched through digital i/o to a 16 channel
   CD74HC4067M mux chip. This chip channels in opto-isolated fan
   tach pulse signals.

   The board can be controlled manually, by toggling the control switch,
   by adjusting the potentiometer knob positions, or through a connected
   serial interface.  The v1 version of the board implements the
   serial itnerface through a usb connection, this can be changed later.

   All serial commands have the following format:
   [C][DATA]\n
   where:
      C is a command character described below
      DATA is described below for each command using ',' as a delimiter

   The serial interface is described as follows:
   PWM Command - Sets the pwm for a specified channel
   usage: p[channel][pwm duty cycle]
   returns: '.'

   Sample time divider Command - sets the sample time divider for reading
   rpm.  1 gives you a value of one second per channel.
   usage: d[divider]
   returns: '.'

   Mode query - Ask for the current mode
   usage: m
   returns: "Mode:[mode]"

   Report output toggle - enables or disables report output through serial
   interface
   usage: !
   returns: '.'

   read rpm command - reads the rpm from a specific channel using a specific divider
   usage: r[channel][divider]
   returns: Channel[channel]_rpm:[rpm]

   read temperature - reads the onboard temperature from the sensor
   usage: t
   returns: "Temp:[temperature C]"

   set all pwm: Sets the pwm for all channels
   usage: #[pwm duty cycle]
   returns: '.'

   set group pwm: Sets all top or bottom channels to a pwm
   usage: @[pwm duty cycle]
   returns: '.'

*/

#define mux_s0 9
#define mux_s1 10
#define mux_s2 11
#define mux_s3 12
#define mux_sig 2
#define mux_en 8
#define toggle_in 3
#define pot1 A2
#define pot2 A3
#define t_sense A4

#include <EEPROM.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

int pwm_values[16];
int pwm_request[16];
int rpm_values[16];
int f_cnt = 0;
int rpm_div = 0;
int mode = 0;
bool report_out = true;
long next_report = 0;
int report_delay = 1000;

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver(0x40);  //change i2c address here if different.

/*
   cntr: Attached to mux signal interrupt.  Increments pulse counter.

*/
void cntr() {
  f_cnt++;
}

/*
   setup: built-in function, runs once on startup.
*/
void setup() {
  int i;
  //noInterrupts();  //disable interrupts (for now...)
  Serial.begin(115200); //start Serial interface
  Serial.println("Serial Interface:started");

  load_config();  //load config from EEPROM
  Serial.println("E2 Config:Loaded");

  //pwm.begin();  //start pwm i2c interface
  Serial.println("PWM Driver:started");

  //pwm.setPWMFreq(1600); //set pwm frequency
  //initialize storage arrays
  for (i = 0; i < 16; i++) {
    pwm_request[i] = 0;
    pwm_values[i] = 0;
    rpm_values[i] = 0;
  }

  //set pin modes
  pinMode(mux_s0, OUTPUT);
  pinMode(mux_s1, OUTPUT);
  pinMode(mux_s2, OUTPUT);
  pinMode(mux_s3, OUTPUT);
  pinMode(mux_en, OUTPUT);
  pinMode(toggle_in, INPUT);

  //attachInterrupt(digitalPinToInterrupt(mux_sig), cntr, FALLING);  //pulse counter for reading fan tag

  digitalWrite(mux_en, HIGH);  //disable mux chip (for now...)

  next_report = 0;
  Serial.println("Main Loop:started");
}

void enableInterrupt() {
  attachInterrupt(digitalPinToInterrupt(mux_sig), cntr, FALLING);  //pulse counter for reading fan tag
}

void disableInterrupt() {
  detachInterrupt(digitalPinToInterrupt(mux_sig));  //pulse counter for reading fan tag
}

/*
   loop:  built-in function, main execution loop
*/
void loop() {
  //check mode
  check_mode();
  if (mode == 0)
    setPWM_values();  //set PWM from serial interface requests
  else if (mode == 1)
    manual_control(); //set PWM from potentiometers

  getRPM_values(rpm_div);  //read RPM signals from fans
  if (report_out)
    report();  //report information
}

void check_mode() {
  int mread = digitalRead(toggle_in) == HIGH ? 1 : 0;
  if (mread != mode) {
    mode = mread;
    Serial.print("Mode:");
    Serial.print(mode);
    Serial.println();
  }
}

/*
   load_config: load values for running fans from Eeprom
   Memory map:
   Field:       Address:      Type
   rpm_div      0             int
   report_out   2             int
*/
void load_config() {
  rpm_div = EEPROM.read(0);
  if (rpm_div < 1)
    rpm_div = 4;
  report_out = (EEPROM.read(2) == 1);
  report_delay = EEPROM.read(4);
  //if(report_delay = 0)
  report_delay = 1000;

  Serial.print("rpm_div:");
  Serial.print(rpm_div);
  Serial.println();

  Serial.print("report_output:");
  Serial.print(report_out);
  Serial.println();

  Serial.print("report_delay:");
  Serial.print(report_delay);
  Serial.println();
}

/*
   save_config: save values to EEPROM.
   See memory map in load_config notes.
*/
void save_config() {
  EEPROM.write(0, rpm_div);
  EEPROM.write(2, report_out ? 1 : 0);
  EEPROM.write(4, report_delay);
}

/*
   report: sends system information to serial interface
   report sample output:
   [channel],[pwm],[rpm]
   0,0,0
   1,0,0
   2,50,1600
   ...
*/
void report() {
  int i;
  if (millis() > next_report) {
    for (i = 0; i < 16; i++) {
      /*Serial.print("Channel[");
      Serial.print(i);
      Serial.print("]_pwm:");
      Serial.print(pwm_values[i]);
      Serial.println();//*/
      if(rpm_values[i] > 0){
        Serial.print("Channel[");
        Serial.print(i);
        Serial.print("]_rpm:");
        Serial.print(rpm_values[i]);
        Serial.println();
      }
    }
    read_temp();
    next_report = millis() + report_delay;
  }
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

/*
   manual_control: reads the value from the potentiometers to set PWM on top/bottom groups
*/
void manual_control() {
  int p1 = analogRead(pot1);  //top board knob
  int p2 = analogRead(pot2);  //bottom board knob
  int dc1 = map(p1, 0, 1024, 0, 100);  //map analog input to 0-100 scale
  int dc2 = map(p2, 0, 1024, 0, 100);
  int i;

  for (i = 0; i < 16; i++) {
    if (i < 8) {
      setPWM(i, dc1); //set pwm for top board
    } else {
      setPWM(i, dc2); //set pwm for bottom board
    }
  }
}

/*
   getRPM_values: reads all the rpm values coming from the 16 fan channels using the specified divider
      - divider: is the sample time divider with 1 second as the base.
      A divider of 1 will take 16 seconds to read all of the channels.
*/
int getRPM_values(int divider) {
  int i;
  for (i = 0; i < 16; i++) {
    getRPM(i, divider);
  }
}

/*
   getRPM: reads the rpm from a specified channel using the sample time divider.  The fan tach signal
   is muxed in, and then counted for the specified time.  That time is converted to rpm.
*/
int getRPM(int ch, int divider) {
  f_cnt = 0;
  digitalWrite(mux_en, LOW);
  setMux(ch);
  enableInterrupt();
  delay(1000 / divider);
  disableInterrupt();
  rpm_values[ch] = f_cnt * (60 * divider);
  digitalWrite(mux_en, HIGH);
  return rpm_values[ch];
}

/*
   setPWM: sets the pwm value on a specified channel
     - ch: the channel to set, 0-15
     - pwm_V: the duty cycle % value for pwm [0-100]
*/
void setPWM(int ch, int pwm_v) {
  if (pwm_values[ch] != pwm_v) {
    pwm.setPWM(ch, 0, pwm_v);
    pwm_values[ch] = pwm_v;
  }
}

/*
   setPWM_values: updates all channels based on the requested pwm values.
*/
void setPWM_values() {
  int i;
  for (i = 0; i < 16; i++)
    setPWM(i, pwm_request[i]);
}

/*
   setMux: Mux for the selected channel
     - ch: the channel to set, 0-15
*/
void setMux(int ch) {
  digitalWrite(mux_s0, bitRead(0, ch) ? HIGH : LOW);
  digitalWrite(mux_s1, bitRead(1, ch) ? HIGH : LOW);
  digitalWrite(mux_s2, bitRead(2, ch) ? HIGH : LOW);
  digitalWrite(mux_s3, bitRead(3, ch) ? HIGH : LOW);
}

/*
   serialEvent: implements the serial interface for control
   fires when serial data is received.
*/
void serialEvent() {
  if (Serial.available() > 0) {
    String recvd = Serial.readStringUntil('\n');
    char cmd = recvd.charAt(0);
    int rpm;
    int group;
    int channel = 0;
    int duty_cycle = 0;
    int divider;
    int i;
    switch (cmd) {
      case 'p':
      case 'P':  //PWM command
        channel = getInt(recvd, 1, ',');  //0-15
        duty_cycle = getInt(recvd, 2, ','); //0-100
        pwm_request[channel] = duty_cycle;
        Serial.print('.');
        Serial.println();
        break;
      case 'd':
      case 'D':  //set rpm divider (see getRPM for notes)
        rpm_div = getInt(recvd, 1, ',');
        save_config();
        Serial.print('.');
        Serial.println();
        break;
      case 'm':
      case 'M':  //query the current mode
        Serial.print("Mode:");
        Serial.print(mode);
        Serial.println();
        break;
      case '!':  //change the report output
        report_out = !report_out;
        save_config();
        Serial.print('.');
        Serial.println();
        break;
      case 'i':
      case 'I':  //set report delay
        report_delay = getInt(recvd, 1, ',');  //0 - 65335 milliseconds
        if (report_delay = 0) {
          report_delay = 1000;
          report_out = false;
        }
        save_config();
        Serial.print('.');
        Serial.println();
        break;
      case 'r':
      case 'R':  //read specific RPM from channel, with specified sample time divider (1 == 1 second, 2 = 0.5 seconds, ...) 0 = use default
        channel = getInt(recvd, 1, ','); //0-15
        divider = getInt(recvd, 2, ','); //0 - 255
        if (divider == 0) {
          divider = rpm_div;
        }
        rpm = getRPM(channel, divider);
        Serial.print("Channel[");
        Serial.print(channel);
        Serial.print("]_rpm:");
        Serial.print(rpm);
        Serial.println();
        break;
      case 't':
      case 'T':
        read_temp();
        break;
      case '#':  //set all PWM to one value
        duty_cycle = getInt(recvd, 1, ','); //0 - 100
        for (i = 0; i < 16; i++) {
          pwm_request[i] = duty_cycle;
        }
        Serial.print('.');
        Serial.println();
        break;
      case '@':  //set group to one PWM Value (0 = top group, 1 = bottom group)
        group = getInt(recvd, 1, ',');  //0 - 1
        duty_cycle = getInt(recvd, 2, ','); //0 - 100
        for (i = (group * 8); i < (group * 8) + 8; i++) {
          pwm_request[i] = duty_cycle;
        }
        Serial.print('.');
        Serial.println();
        break;
    }
  }
}

/*
   getInt: Helper function to parse parameter data from strings
      - str: string to parse
      - parameter: parameter index to return  ie: the number of parameter1,parameter2,parameter3,...
      - delim: the delimiter to use to separate parameters
*/
int getInt(String str, int parameter, char delim) {
  int i;
  int pcount = 1;
  String data = "";
  for (i = 1; i < str.length(); i++) {
    if (str.charAt(i) != delim)
      data += str.charAt(i);
    else {
      if (parameter == pcount)
        break;
      else {
        pcount += 1;
        data = "";
      }
    }
  }
  return data.toInt();
}

# LTR Interconnect Board v3.5 Software Users Guide

[![Build Status](https://shields.io/github/workflow/status/pimoroni/mcp9600-python/Python%20Tests.svg)](https://github.com/rchavira/ltr_control_software/actions/workflows/test.yml)

Revision 0.2
Updated for V2 control software implementation

##Overview
The LTR control software runs as a multi-threaded modbus server application, updating registers with information that it reads from sensors and states, and reading commands from registers to run the system outputs.

##SSH Service
SSH access is also enabled by default and you can gain access from any terminal by running

For windows you can install putty

ssh pi@[ip address] 

Password is 
raspberry

All software is located in the the following location
/home/pi/control_software

##Modbus Service
The interface is accessible via Modbus TCP at the IP address of the PI using port 502.
You can use any modbus client tool (for windows I have used Modbus Examiner.)

The modbus server exposes two types of registers, Holding Registers and Input registers.  Holding Registers are able to be read from and written to via a modbus client, while input registers are read only.

###Holding registers
The holding registers are used to receive 3 specific commands from a modbus TCP client: 
- Run (addr: 0) - When set to 1, the system will run the ttv drivers to the power target value.  When set to 0, ttv output is turned off.
- Shutdown (addr: 1) - When set to 0, the system will not shutdown, when set to any value other than 0, the system will shutdown the software.  Note: The system service daemon will restart the service by default.  This can be used to restart the service to load new values, or to shutdown remotely when run from the command line.
- Power Target Value (addr: 10) - this is the value to set the power target to.  This value must not be greater than the max power value in the system_config.json file.  If power ramp setting is applied in driver_config.json, the power will ramp up to this target value.

The addresses for these registers can be modified in the modbus_config.json file.

###Input Registers
The input registers are used by the system to relay specific sensor information and system information.  These registers are read only to any modbus TCP Client.

###System Registers
These registers relay information about the current system condition.  
- Running_ttv (addr: 0) - 1 indicates the ttvs are running to a power target, 0 indicates that they are not.
- System_stop (addr: 1) - 0 indicates normal operation, 1 indicates that a shutdown command was received.
- Leak_detected (addr: 2) - 0 indicates normal operation, 1 indicates that a leak was detected.  Settings for leak detection are in the sensors_manager.json.
- Thermal_fault (addr: 3) - 0 indicates normal operation, 1 indicates that the thermal manager has detected temperatures above the indicated settings in thermal_manager.json settings.
- Sensor_fault (addr: 4) - 0 indicates normal operation, 1 indicates that one or more sensors has returned a fault or error.
- Current_power (addr: 5) - indicates the current power level being commanded.  If the drivers require a power ramp, this will indicate the actual power being commanded instead of the power target requested
- Run_time (addr: 6) - if the drivers require a power ramp, this will show the time in seconds at that stage of the power ramp.  Once power has been reached, this time will not increment.  For example, if ramp is 10w/minute, this timer will count up to 60 before taking the next increment at each step.  Once the target is reached, the value will remain 60.
- Driver state registers (addr: 10-15)  - The current duty cycle being commanded to each driver including fans. 
  - 10 - TTV bus 1
  - 11 - TTV bus 2
  - 12 - TTV bus 3
  - 13 - TTV bus 4
  - 14 - Fan Bus 1
  - 15 - Fan Bus 2
###Sensor Registers
These registers indicate the current values of each sensor or input in the system.  The value is stored as an integer, so a decimal place value helps to convert this to a floating point number.

####Thermocouples
Divide all thermocouple values by 100 (2 decimal places) to get the temperature in degrees Celsius.
- T1 - T8 (addr: 20-27) - TTV Tcase thermocouples.
- T9 - T10 (addr: 28, 29) - Inlet Thermocouples.
- T11-T12 (addr: 38, 39) - Outlet temperature
- T13-T14 (addr: 42, 43) - board temperature
- TFCB (addr:55) - fan control board temperature
####Current Sensors
- I1-I4 (addr:30-33) - TTV Bus 1-4 current
- I5 (addr: 44) - System Current
####Voltage Sensing
- V1-V4 (addr:34-37) - TTV Bus 1-4 voltage
####Leak Sensing
- L1 (addr: 41) - Leak sensor input
- D2 (addr: 46) - External Leak GPIO input Note: not implemented for lab testing

####Fan Speed
- Fan_rpm1 -Fan_rpm8 (addr: 47-54) - Fan speed (tach) from fans 1 -8
####Misc Inputs
- A1 (addr: 40) - Pot 1 input
- D1 (addr: 45) - Toggle switch input

###Info Registers
These registers give other system information.
- Version (addr: 16) - the current software version (for this system = 4)
- Monitor_temp (addr: 70) - the aggregated group temperature for the monitor group indicated in thermal_manager.json
- Inlet_temp (addr: 71) - the aggregated group temperature for the inlet group indicated in thermal_manager.json
- Outlet_temp (addr: 72) - the aggregated group temperature for the outlet group indicated in thermal_manager.json

**A note about aggregated temperature:**
The settings in thermal_manager.json indicate which sensors are aggregated and how many samples are used.  For each sample, each sensor value in the group is grouped together in an average, then the value is added to an array sized to the sample qty to return a mean value.  

For example, if a group has the two sensors T1, T2:
	When the sensor values are sampled/measured the value becomes:
    
    Tsample[n] = (T1 + T2) / 2
    Taggregated = SUM(Tsamples[i]) / sample_size

##Software Description
The software is written in python and runs on python version 3.7+.  The location of all relevant software and utilities are installed in the /home/pi/control_software folder.  You can download the software from the github repository https://github.com/rchavira/ltr_control_software
###Installation
I recommend writing the latest ltr_raspi_v{v}.img to an sd card as a base.  This has all software dependencies installed.  You can then copy over the github repository files to the /home/pi/control_software directory.

####Future Implementation: 
Run the following from the raspi terminal 

    wget “https://raw.githubusercontent.com/rchavira/ltr_control_software/main/install.sh”
    sudo chmod +x ./install.sh
    sudo ./install.sh

###Service Scripts
The following are scripts that install or remove the software to run as a service.  Once the service is installed, the software will run on startup.  By default the service is installed and enabled.  

- /home/pi/control_software/
  - control_software.service
  - install_service.sh
  - uninstall_service.sh

####control_software.service
This file describes the settings and behaviors for the service.  
####install_service.sh (run with sudo)
This script will copy the control_software.service file to /lib/systemd/system/ folder, install the script (symlink to system service folder), reload the service daemon and start the service.

    sudo ./install_service.sh

####uninstall_service.sh (run with sudo)
This script will stop and remove the service.

    sudo ./uninstall_service.sh

###devices (directory)
This directory is a python module that contains device managers and specific device drivers.  To add a new device, follow the prototype in that device type sub-modules’ __init__.py and create a new child module.  This allows for the loading of a specific driver by settings in a config JSON file.
Specific device types in this directory include analog to digital converters, communication, digital i/o, fan controllers, i2c, spi, mux (encoders/decoders), pwm, and thermocouple amplifiers.  In order to ease development, emulation drivers were written to test control systems and behaviors.  The data used to emulate device inputs is stored in the /home/pi/control_software/devices/emulation_data directory.
###system_control (directory)
This director has all of the server, system, management logic.  The system hierarchy is as follows:
####system_manager.py - main system controller
####modbus_server.py - runs the modbus server
####thermal_management.py - monitors thermal inputs to control the fans / ttvs
####sensor_manager.py - collects sensor information from all devices
###tests (directory)
Contains test logic, to load and test a specific driver / manager.  These routines are called by the main test script.  Each testable device is loaded as a python module.

####main.py (python script)
This is the main software loader script.  This script is executed by the service.  This can also be run from the command line with the following command line arguments.  

    optional arguments:
      -h, --help           show this help message and exit
      --service            Run Controller as a Service
      --emulate            Emulate all hardware on the system.
      --loglevel LOGLEVEL  Log level [DEBUG (1-5) CRITICAL]
      --config CONFIG  The name of the config file to load

If you run from the command line, be sure to stop the service first.  

Run from the command line:

    sudo python main.py [options]

By default all system messages are logged to the terminal, running using the --service argument will log all messages to system.log file.

By default, the application loads ./config/system_config.json, passing the --emulate argument loads the ./config/emulation/emulate_config.json

You can load a custom config file by passing the --config [custom_config.json] argument and file name.  The custom config file must be located in the config directory.  

You can change the log level by passing --loglevel [LOGLEVEL] argument and log level value 1 - 5.  With the values of 1 being all debug messages and 5 being critical messages only.

When running from the command line, pressing ctrl+c will initiate the shutdown of the application.
####system.log
This is the logged output.  If the file grows too large, you can delete this file or consider adding the --loglevel argument to the service call in control_software.service.  Uninstall, and reinstall the service.
####test.py (python script)
This is the main testing script.  Be sure to stop the control_software service before running.  This script has the following arguments.

    optional arguments:
      -h, --help           show this help message and exit
      --loglevel LOGLEVEL  Log level [DEBUG (1-5) CRITICAL]
      --test TEST          What to test. DIO, ADC, FANS, TC, SENSORS, THERMAL, ALL

Run from the command line:

	sudo python test.py [options]

By default the script will run all of the tests, if you pass the --test [TEST] argument, you can select which tests to run.  For example, --test ADC will only test the adc management (all analog input signals).  While --test DIO,TC will test both digital I/O and thermocouple readings.

The log level argument works the same as in main.py

##Configuration

###emulation (directory)
This contains all JSON configurations for emulated mode.  In order to load from this directory, the file name must contain the word “emulate”.  This directory is also a python module, you can import the read_config function from it to read a config file by just passing its name (no path).

###System Config File
The system config file is the main configuration file used to run the system.  There are two built in system config files, one for normal operation and one for emulation mode.  

You can specify which device configurations to load when running in emulation mode by modifying this file.  For example, if you want to actually read thermocouples but emulate everything else, you would specify the thermocouple_config.json file.

Note: any config file with the word “emulate” in the title should be placed in the ./config/emulation/ directory.

If a custom file is used, it is required to have the following contents

    {
     "version": [Version of this file],
     "date": "[Date of this file (in yyyy.mm.dd format)]",
     "adc_config": "[adc_config file name]",
     "chip_select_config": "[chip_select_config file name]",
     "dio_config": "[dio_config file name]",
     "driver_config": "[driver_config file name]",
     "fan_speed_device_config": "[fan_speed_device_config file name]",
     "i2c_config": "[i2c_config file name]",
     "modbus_config": "[modbus_config file name]",
     "sensor_manager": "[sensor_manager file name]",
     "spi_config": "[spi_config file name]",
     "system_config": "[system_config file name]",
     "thermal_manager": "[thermal_manager file name]",
     "thermocouple_config": "[thermocouple_config file name]",
     "controller_type": "[Controller type1]",
     "fan_dev_type": "[Fan device type2]",
     "power_on_target": [target power (Watts) to output3],
     "max_power_target": [Max power target (Watts)4]
    }

**Notes**:
Controller Type must be in the enum system_control.ControllerDeviceTypes As of this date, the only options are raspi and emulated
Fan Device Type must be in the enum devices.fan_controller_devices.FanDevType As of this date, the only options are fan_control_board and emulated
Target power will be ramped up if there is a heating curve applied in driver configuration.  
Max power is used to derive the initial duty cycle % of the driver controller.  This is used as the divisor of the power target.


###ADC Configuration

The LTR board has two 8 channel ADC converters to read in various analog signals.  The converter type is ‘max1168’, and the device type must be defined in the enum devices.adc_devices.AdcDeviceTypes.  For each device, the members of that group receives a device id (ie.  “i1” or “t11”) that can be used in thermal_manager.json or sensor_manager.json.

    {
       "update_interval": 0.1,
       "devices": {
           "adc1": {
               "device_type": "max1168",
               "chip_select": 10,
               "devices": {
                   "i1": {"channel": 0, "min_val": 0, "max_val": 2500},
                   "i2": {"channel": 1, "min_val": 0, "max_val": 2500},
                   "i3": {"channel": 2, "min_val": 0, "max_val": 2500},
                   "i4": {"channel": 3, "min_val": 0, "max_val": 2500},
                   "v1": {"channel": 4, "min_val": 0, "max_val": 6000},
                   "v2": {"channel": 5, "min_val": 0, "max_val": 6000},
                   "v3": {"channel": 6, "min_val": 0, "max_val": 6000},
                   "v4": {"channel": 7, "min_val": 0, "max_val": 6000}
               }
           },
           "adc2": {
               "device_type": "max1168",
               "chip_select": 11,
               "devices": {
                   "t11": {"channel": 0, "min_val": 0, "max_val": 325},
                   "t12": {"channel": 1, "min_val": 0, "max_val": 325},
                   "a1": {"channel": 2, "min_val": 0, "max_val": 1024},
                   "l1": {"channel": 3, "min_val": 0, "max_val": 65535},
                   "t13": {"channel": 4, "min_val": 0, "max_val": 32},
                   "t14": {"channel": 5, "min_val": 0, "max_val": 32},
                   "i5": {"channel": 6, "min_val": 0, "max_val": 20}
               }
           }
       }
    }

###Chip Select Configuration
The chip select has settings for the cd4515 chip in the configuration file “chip_select_config.json”.  This specifies the GPIO pins used to interact with the encoder chip, in LTR.  Each pin must be in the outputs group of the dio_config.json

    {
       "version": 1,
       "date": "2022.03.09",
       "device_type": "cd451x",
       "cs_reset": 15,
       "config": {
           "pinA": 17,
           "pinB": 27,
           "pinC": 22,
           "pinD": 5,
           "strobe": 23,
           "strobe_delay": 0.5
       }
    }

###Digital IO Configuration
The config file “dio_config.json” contains the pin configuration for inputs and outputs for the raspberry pi.  
    {
       "version": 1,
       "date": "2022.03.09",
       "input_pins": [6, 16],
       "output_pins": [5, 17, 22, 23, 26, 27]
    }

###Driver Configuration
There are two main groups that are declared as devices (even if there is only one device on the system.  This allows for the drivers in the groups to be controlled separately, with different settings.  For example, the fans do not require a ramp_up to get to full power.  The name in drivers can be used in thermal_manager.json to include in the control group.  The device_type must is defined in the enum devices.pwm_devices.DriverTypes.
    {
       "version": 1,
       "date": "2022.03.09",
       "update_interval": 1,
       "devices": {
           "ttv_group": {
               "device_type": "pca9685",
               "config": {
                   "ramp_up_dc_step": 2,
                   "ramp_up_delay_seconds": 2,
                   "frequency": 60,
                   "i2c_addr": 68,
                   "drivers": {
                       "ttv1": {
                           "channel": 0,
                           "offset": 0,
                           "resolution": 65535
                       },
                       "ttv2": {
                           "channel": 1,
                           "offset": 0,
                           "resolution": 65535
                       },
                       "ttv3": {
                           "channel": 2,
                           "offset": 0,
                           "resolution": 65535
                       },
                       "ttv4": {
                           "channel": 3,
                           "offset": 0,
                           "resolution": 65535
                       }
    
                   }
               }
           },
           "fan_group": {
               "device_type": "pca9685",
               "config": {
                   "ramp_up_dc_step": 0,
                   "ramp_up_delay_seconds": 0,
                   "frequency": 60,
                   "i2c_addr": 68,
                   "drivers": {
                       "fan1": {
                           "channel": 4,
                           "offset": 0,
                           "resolution": 65535
                       },
                       "fan2": {
                           "channel": 5,
                           "offset": 0,
                           "resolution": 65535
                       }
    
                   }
               }
           }
       }
    }

###Fan Speed Device Configuration
This is the configuration for the fan speed device.  The port /dev/ttyUSB0 is the default address when plugging in an arduino nano.  Note: For testing on a windows machine, this should be the com port.
    {
       "version": 1,
       "date": "2022.03.09",
       "port": "/dev/ttyUSB0",
       "baudrate": 115200,
       "timeout": 0.5,
       "channel_count": 8
    }

###I2C Bus Configuration
This configuration is reserved for future use.
    {
     "version": 1,
     "date": "2022.03.09"
    }

###SPC Bus Configuration
This configuration is reserved for future use.
    {
     "version": 1,
     "date": "2022.03.09"
    }

###Thermocouple Configuration
You can specify what thermocouples are in the system, the type must be defined in the enum devices.thermocouples.ThermoTypes.

    {
       "version": 1,
       "date": "2022.03.09",
       "update_interval": 0.1,
       "temp_decimals": 2,
       "devices": {
           "t9": {"device_type": "max31855", "cs": 9},
           "t10": {"device_type": "max31855", "cs": 8},
           "t1": {"device_type": "mcp960x", "i2c_addr": 96},
           "t2": {"device_type": "mcp960x", "i2c_addr": 97},
           "t3": {"device_type": "mcp960x", "i2c_addr": 98},
           "t4": {"device_type": "mcp960x", "i2c_addr": 99},
           "t5": {"device_type": "mcp960x", "i2c_addr": 100},
           "t6": {"device_type": "mcp960x", "i2c_addr": 101},
           "t7": {"device_type": "mcp960x", "i2c_addr": 102},
           "t8": {"device_type": "mcp960x", "i2c_addr": 103}
       }
    }

###Sensors Manager Configuration
You can specify the behavior of the leak detection through this configuration.  The internal_leak_dev_id must be declared in adc_config.json.  The fan_speed_device_type must be defined in the enum devices.fan_controller_devices.FanDevType
    {
       "version": 1,
       "date": "2022.03.09",
       "fan_speed_device_type": "fan_control_board",
       "internal_leak_dev_id": "l1",
       "leak_detection_mode": "threshold",
       "leak_detection_value": 2000,
       "external_leak_pin": 1,
       "leak_report_out_pin": 2,
       "leak_report_active": 0,
       "leak_report_inactive": 1,
       "leak_sample_rate": 1
    }

###Thermal Manager Configuration
You can specify the groups to control, and to monitor, as well as thermal thresholds and fan control behavior through this configuration file.  The device id’s in fan_group, driver_group must be declared in driver_config.json.  The values for inlet_group, outlet_group and monitor_group must be declared in adc_config.json or thermocouple_config.json.
    {
       "version": 1,
       "date": "2022.03.09",
       "fan_group": ["fan1", "fan2"],
       "driver_group": ["ttv1", "ttv2", "ttv3", "ttv4"],
       "inlet_group": ["t9", "t10"],
       "outlet_group": ["tFCB"],
       "monitor_group": ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"],
       "monitor_threshold_temp": 75,
       "outlet_threshold_temp": 45,
       "inlet_threshold_temp": 45,
       "fan_table": [
               [45, 60],
               [44, 45],
               [42, 30],
               [40, 20]
       ],
       "default_fan_value": 70,
       "sample_size": 10,
       "fan_run_mode": "fan_table"
    }

###Modbus Server Configuration
You can modify the address registers or add sensor registers through this file.  At the moment each other register group is fixed (besides the addresses).
    {
       "version": 1,
       "date": "2022.03.09",
       "address": "localhost",
       "port": 502,
       "max_registers": {
           "di": 20,
           "co": 20,
           "hr": 160,
           "ir": 160
       },
       "control_registers": {
           "run": 0,
           "shutdown": 1,
           "power": 10
       },
       "system_registers": {
           "running_ttv": 0,
           "system_stop": 1,
           "leak_detected": 2,
           "thermal_fault": 3,
           "sensor_fault": 4,
           "current_power": 5,
           "run_time": 6,
           "target_power": 7,
           "driver_state_register": 10
       },
       "flag_registers": {
           "t1": 100,
           "t2": 101,
           "t3": 102,
           "t4": 103,
           "t5": 104,
           "t6": 105,
           "t7": 106,
           "t8": 107,
           "t9": 108,
           "t10": 109,
           "t11": 110,
           "t12": 111,
           "t13": 112,
           "t14": 113,
           "l1": 114
       },
       "sensor_registers": {
           "t1": {"address": 20, "decimal_places": 2},
           "t2": {"address": 21, "decimal_places": 2},
           "t3": {"address": 22, "decimal_places": 2},
           "t4": {"address": 23, "decimal_places": 2},
           "t5": {"address": 24, "decimal_places": 2},
           "t6": {"address": 25, "decimal_places": 2},
           "t7": {"address": 26, "decimal_places": 2},
           "t8": {"address": 27, "decimal_places": 2},
           "t9": {"address": 28, "decimal_places": 2},
           "t10": {"address": 29, "decimal_places": 2},
           "i1": {"address": 30, "decimal_places": 2},
           "i2": {"address": 31, "decimal_places": 2},
           "i3": {"address": 32, "decimal_places": 2},
           "i4": {"address": 33, "decimal_places": 2},
           "v1": {"address": 34, "decimal_places": 2},
           "v2": {"address": 35, "decimal_places": 2},
           "v3": {"address": 36, "decimal_places": 2},
           "v4": {"address": 37, "decimal_places": 2},
           "t11": {"address": 38, "decimal_places": 1},
           "t12": {"address": 39, "decimal_places": 1},
           "a1": {"address": 40, "decimal_places": 0},
           "l1": {"address": 41, "decimal_places": 0},
           "t13": {"address": 42, "decimal_places": 2},
           "t14": {"address": 43, "decimal_places": 2},
           "i5": {"address": 44, "decimal_places": 1},
           "d1": {"address": 45, "decimal_places": 0},
           "d2": {"address": 46, "decimal_places": 0},
           "fan_rpm1": {"address": 47, "decimal_places": 0},
           "fan_rpm2": {"address": 48, "decimal_places": 0},
           "fan_rpm3": {"address": 49, "decimal_places": 0},
           "fan_rpm4": {"address": 50, "decimal_places": 0},
           "fan_rpm5": {"address": 51, "decimal_places": 0},
           "fan_rpm6": {"address": 52, "decimal_places": 0},
           "fan_rpm7": {"address": 53, "decimal_places": 0},
           "fan_rpm8": {"address": 54, "decimal_places": 0},
           "tFCB": {"address": 55, "decimal_places": 2}
       },
       "info_registers": {
           "version": 16,
           "monitor_temp": 70,
           "inlet_temp": 71,
           "outlet_temp": 72
       }
    }

##Libraries
The libraries directory holds all of the custom built libraries for the application.  For this build of the LTR Chassis, a custom library was forked from the mcp9600 to add the functionality of the mcp9601 chip.  When this diff lands, it should be available in pypi repo, and installed using pip. 

	mcp9600-0.0.5-py2.py3-none-any.whl

##Fan Control Board
This folder contains the current version of the arduino sketch used on the fan controller board.  
    /home/pi/control_software/fan_controller_boardv1.2/fan_controller_boardv1.2.ino

##IP Configuration
The IP address that is used during boot is located in this file.  It is assigned as a static IP.  It is placed in the /boot directory so that you can access it from the sd card if it is accessed by another computer.

    /boot/network/dhcpcd.conf

##Supported Hardware
This software currently supports the following hardware, however drivers can be written and added to the devices module to add other device hardware.

- Controllers / Digital IO / SPI / I2C / UART
  - Raspberry Pi v4
- PWM devices 
  - PCA9685
- Analog to Digital Converters 
  - MAX1168
- MUX Encoders 
  - CD4514
  - CD4515 
- Thermocouple Amplifiers
  - MAX31855
  - MAX31856
  - MCP9600
  - MCP9601
- Fan Control
  - Fan Control Board v1 (fan speed measurement)





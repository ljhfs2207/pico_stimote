### add path to import custom modules
import sys, os
os.chdir('/home/ddlabpi/pico/dac_control/')
sys.path.append('/home/ddlabpi/pico/dac_control/')

### import modules
import time
import pyvisa
import pickle
import csv
import pandas as pd
import RPi.GPIO as gpio
#from ThorlabsPM
from pymeasure.instruments.keithley import Keithley2400
### Jungho custom
from pico import Pico
from gen_inst import *

#################### Main parameters
### GPIO
gpio_pi_pin_stream_monitor = 4

### Pico setting
#pico_port = '/dev/ttyACM0'
pico_port = '/dev/serial0'
#baud = 115201
baud = 921600
pico_sm_freq = 100e3

### DAC setting 
log_annotation = 'isc'
sel_vout = 'VOUTB'
vrefh = 5 #V
vrefl = 0 #V
vh = 4 #V, high V=small light=CMP 0 on chip
vl = 3 #V

### GOC 
fname = '221117_leg.bin'
leg = {'fl': 0, 'fr': 0, 'rl': 0, 'rr': 0} # 0 or 1
t_period = 1/3 #sec
t_start = 15 #sec

### Chip behavior
chip_turn_off_first = True
chip_force_vdd = False
chip_vdd = 0.7

### Sourcemeter
sourcemeter_port = "GPIB::15"
####################

#################### Core behavior
### Connect PICO
pico = Pico(pico_port, baud, log_annotation)
log = pico.log

### Connect Keithley2400
sourcemeter = Keithley2400(sourcemeter_port)
sourcemeter.apply_voltage()
sourcemeter.measure_voltage()
sourcemeter.compliance_current = 10e-3
sourcemeter.source_voltage = 0 # V, turn off
sourcemeter.current_range = 10e-6
sourcemeter.enable_source()
sourcemeter.write(':SYST:LOC') # make visible through front panel of sourcemeter
time.sleep(1)
log.info('sourcemeter succesfully set up - vsrc=0')

### PICO - DAC init
pico.dac_set_frequency(pico_sm_freq)
pico.dac_set_vref(vrefl, vrefh)
pico.dac_set_vchannel(sel_vout)
pico.dac_set_vlevel(vl, vh)
pico.dac_int_ref_powerdown()
pico.dac_int_ref_powerdown()
pico.dac_set_voltage(vrefl)

### Measure isc
#while True:
#    print(sourcemeter.current)
#    time.sleep(0.1)
####################


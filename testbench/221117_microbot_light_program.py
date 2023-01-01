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
log_annotation = 'chip_program'
sel_vout = 'VOUTB'
vrefh = 5 #V
vrefl = 0 #V
vh = 3.8 #V, high V=small light=CMP 0 on chip
vl = 2.5 #V

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
### GPIO
gpio.setmode(gpio.BCM)
gpio.setup(gpio_pi_pin_stream_monitor, gpio.OUT)

### Connect PICO
pico = Pico(pico_port, baud, log_annotation)
log = pico.log

### Connect Keithley2400
sourcemeter = Keithley2400(sourcemeter_port)
if chip_turn_off_first:
    sourcemeter.apply_voltage()
    sourcemeter.measure_voltage()
    sourcemeter.compliance_current = 10e-3
    sourcemeter.source_voltage = 0 # V, turn off
    sourcemeter.current_range = 10e-6
    sourcemeter.enable_source()
    time.sleep(1)
    log.info('sourcemeter succesfully set up - turn off first')

### GOC program file
leg_pickle = 'microbot/leg.pickle'
binfile = 'microbot/' + fname + '_bit.bin'
csvfile = 'microbot/' + fname + '.csv'
picklefile = 'microbot/' + fname+'_command.pickle'

### Generate/Update instruction timeseries csv
write_new = True
if os.path.exists(leg_pickle):
    with open(leg_pickle, 'wb') as fp:
        leg_compare = pickle.load(fp)
        write_new = leg != leg_compare # if equal, don't write
if write_new:
    gen_inst_bin(leg=leg, fname=binfile)
    bin_string = bin_full_command(binfile)
    d = bin_to_manchester_transition(bin_string, t_period=t_period,t_start=t_start,reverse_bit=True)
    timeseries_to_csv(d, csvfile)
    log.info('file written - {}'.format(csvfile))

### PICO - DAC init
pico.dac_set_frequency(pico_sm_freq)
pico.dac_set_vref(vrefl, vrefh)
pico.dac_set_vlevel(vl, vh)

### Chip initialization
if chip_force_vdd:
    sourcemeter.apply_voltage()
    sourcemeter.compliance_current = 100e-3
    sourcemeter.source_voltage = chip_vdd
    log.info('sourcemeter succesfully set up - vsrc=0.7')
else:
    sourcemeter.apply_current()
    sourcemeter.measure_voltage()
    sourcemeter.source_current = 0
    sourcemeter.compliance_voltage = 1.5
    log.info('sourcemeter - free running')
sourcemeter.enable_source()
sourcemeter.write(':SYST:LOC') # make visible through front panel of sourcemeter

### Standby
time.sleep(1)
with open(csvfile) as fp:
    log.info('timeseries - len = {}'.format(sum(1 for row in fp)))
pico.logger_off()

### Chip programming
try:
    with open(csvfile) as fp:
        init_time = time.time()
        reader = csv.reader(fp)
        for row in reader:
            target_time = float(row[0]) # sec
            target_value = int(row[1]) # 0 or 1
            while time.time() - init_time <= target_time:
                time.sleep(0.0001) # s
            if target_value == 0:
                gpio.output(gpio_pi_pin_stream_monitor, gpio.LOW)
                pico.dac_set_voltage(vl)
            elif target_value == 1:
                gpio.output(gpio_pi_pin_stream_monitor, gpio.HIGH)
                pico.dac_set_voltage(vh)
    gpio.cleanup()
except KeyboardInterrupt:
    gpio.cleanup()
####################


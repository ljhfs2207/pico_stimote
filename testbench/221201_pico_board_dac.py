### add path to import custom modules
import sys
import os
import time
os.chdir('/home/ddlabpi/pico/dac_control/')
sys.path.append('/home/ddlabpi/pico/dac_control/')

### import modules
from pico import Pico

#################### Main parameters
### Pico setting
#pico_port = '/dev/ttyACM0'
pico_port = '/dev/serial0'
#baud = 115201
baud = 921600
pico_sm_freq = 100e3

### DAC setting 
log_annotation = 'pico_board_dac'
####################

#################### Core behavior
### Connect PICO
pico = Pico(pico_port, baud, log_annotation)
log = pico.log

### PICO - DAC init
pico.dac_set_frequency(pico_sm_freq)
pico.dac_set_voltage(4)
for i in range(100):
    v = 5/100*i
    pico.dac_set_voltage(v)
    time.sleep(1e-2)
####################


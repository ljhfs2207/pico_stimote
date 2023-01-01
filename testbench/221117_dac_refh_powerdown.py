### add path to import custom modules
import sys, os
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
log_annotation = 'powerdown'
####################

#################### Core behavior
### Connect PICO
pico = Pico(pico_port, baud, log_annotation)
log = pico.log

### PICO - DAC init
pico.dac_int_ref_powerdown()
pico.dac_int_ref_powerdown()
####################


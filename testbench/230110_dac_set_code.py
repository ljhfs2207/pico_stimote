### add path to import custom modules
import sys
import os
import time
import optparse

### import modules
os.chdir('/home/ddlabpi/pico/stimote/')
sys.path.append('/home/ddlabpi/pico/stimote/')
from pico import pico

########## Parameters ##########
parser = optparse.OptionParser()
parser.add_option('-c', '--code', dest='code', type='int',
                  help='specify code to program dac (12b)')
(options, args) = parser.parse_args()
code = options.code

#################### Main parameters
### Pico setting
pico_port = '/dev/ttyACM0'
#pico_port = '/dev/serial0'
#baud = 115201
baud = 9600 # 921600
pico_sm_freq = 100e3

### DAC setting 
log_annotation = 'pico_board_dac'
####################

#################### Core behavior
### Connect PICO
pico = pico(pico_port, baud, log_annotation)
pico.logger_off()
log = pico.log
pico.dac_set_code(code)
#pico._serial.write(b'\x10\x10\n')
#print(pico._serial.read_all())
####################


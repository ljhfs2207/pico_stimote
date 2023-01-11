### add path to import custom modules
import sys
import os
import time
import optparse

### import modules
os.chdir('/home/ddlabpi/pico/stimote/')
sys.path.append('/home/ddlabpi/pico/stimote/')
from pico import pico

baud = 921600
pico_port = '/dev/ttyACM0'
#baud = 9600
pico = pico(pico_port, baud, 'test')

pico._serial.write(b"dac_command\n")
time.sleep(1)
print(pico._serial.read_all())


import sys
sys.path.append('/home/ddlabpi/pico/stimote')

from pico import Pico
import RPi.GPIO as gpio
import time

### Pico setting
#pico_port = '/dev/ttyACM0'
pico_port = '/dev/serial0'
#baud = 115201
baud = 921600

#gpio.setmode(gpio.BCM)
#gpio.setup(4, gpio.OUT)
pico = Pico(pico_port, baud, 'test')

### Frequency change test
pico.clk_ext_set_frequency(2e6)
pico.clk_ext_set_frequency(1e6)
pico.clk_ext_set_frequency(0.5e6)

#### Test examples
#pico.dac_set_vref(0, 5)
#pico.dac_set_vchannel('voutb')
#pico.dac_set_vlevel(0, 5)
#pico.dac_int_ref_powerdown()
#pico.dac_int_ref_powerdown()
#pico.dac_set_voltage(4.00)
##pico.stream_idle(True)
##pico.stream_str_to_byte('01010101'*127)
##pico.stream_str_to_byte('11111111'*127)
##time.sleep(1)
##pico.stream_write()
##pico.stream_idle(False)
##time.sleep(1)
##pico.stream_idle(True)
##time.sleep(1)
##pico.stream_idle(False)

#gpio.cleanup()

import sys
import RPi.GPIO as gpio
import time

sys.path.append('/home/ddlabpi/pico/stimote/')
from pico import pico
from stimote_inst import manc_enc_str_byte

########## Parameters ##########
### Pi setting
#gpio.setmode(gpio.BCM)
#gpio.setup(4, gpio.OUT)

### Pico setting
pico_port = '/dev/serial0' # '/dev/ttyACM0'
baud = 921600 # 115201
pico = pico(pico_port, baud, 'stimq_sweep')
log = pico.log

### Frequency
freq_clk_ext = 150e3
# manchester 1 code: 256 cycles = 20 ms e.g. 1
# manchester 1 bit: 512 bits = 20 ms e.g. 1 = 01
freq_cmp_ext = 512/20e-3
########################################

########## Core behavior ##########
### CLK_EXT
pico.clk_ext_set_frequency(freq_clk_ext)

### CMP_EXT
pico.stream_set_mode('digital')
#pico.stream_idle(True)
for stim_q in range(1,8):
    #pico.stream_str_to_byte(manc_enc_str[stim_q-1])
    pico.stream_byte = manc_enc_str_byte[stim_q]
    log.info('stim_q sweep - {}'.format(stim_q))
    pico.stream_write(freq_cmp_ext)

### Pi GPIO
#gpio.cleanup()


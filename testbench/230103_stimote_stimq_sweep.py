import sys
import time
import optparse

sys.path.append('/home/ddlabpi/pico/stimote/')
from pico import pico
from stimote_inst import manc_enc_str_moncap_stimq_byte

########## Parameters ##########
parser = optparse.OptionParser()
parser.add_option('-q', dest='stim_q', type='int',
                  help='specify stimulation charge parameter 1-7 (3b)')
parser.add_option('-m', dest='mon_cap', type='int',
                  help='specify P2 monitoring cap trim 1-7 (3b)')
(options, args) = parser.parse_args()
stim_q = options.stim_q
mon_cap = options.mon_cap

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
#pico.clk_ext_set_frequency(freq_clk_ext)

### CMP_EXT
pico.stream_set_mode('digital')
#pico.stream_idle(True)

#pico.stream_str_to_byte(manc_enc_str[stim_q-1])
pico.stream_byte = manc_enc_str_moncap_stimq_byte[mon_cap][stim_q]
log.info('mon_cap - {}, stim_q - {}'.format(mon_cap, stim_q))
pico.stream_write(freq_cmp_ext)



import sys
import os
import time
import optparse

sys.path.append('/home/ddlabpi/pico/stimote/')
from pico_scan import pico_scan
os.chdir('/home/ddlabpi/pico/stimote/')

########## Parameters ##########
parser = optparse.OptionParser()
parser.add_option('--t_stim_comp', dest='t_stim_comp', type='string',
                  help='specify t_stim_comp parameter value 0-3 (2b)')
parser.add_option('--print', dest='print_db', default=0, 
                  help='specify t_stim_comp parameter value 0-3 (2b)')
(options, args) = parser.parse_args()
t_stim_comp = options.t_stim_comp
print_db = options.print_db

########## Scan control ##########
pico_port = '/dev/serial0'
baud = 921600
pico = pico_scan(pico_port, baud, 'test')
pico.logger_off()
pico.scan_load_db()
pico.scan_change_db('CMP_SELEXT', '1')
pico.scan_change_db('TIB_STIM_COMP_EXT', t_stim_comp)
pico.scan_change_db('T_SELEXT', '1')
pico.scan_write()
pico.scan_read()
if print_db:
    pico.scan_print_db()

### add path to import custom modules
import sys
import os
import time
import numpy as np
import pandas as pd
from pymeasure.instruments.keithley import Keithley2400

### import custom modules
os.chdir('/home/ddlabpi/pico/dac_control/')
sys.path.append('/home/ddlabpi/pico/dac_control/')
from pico import Pico

#################### Main parameters
### Pico setting
#pico_port = '/dev/ttyACM0'
pico_port = '/dev/serial0'
#baud = 115201
baud = 921600
pico_sm_freq = 100e3

### DAC setting 
log_annotation = 'dac_characterization'
####################

#################### Core behavior
### Connect PICO
pico = Pico(pico_port, baud, log_annotation)
log = pico.log

### PICO - DAC init
pico.dac_set_frequency(pico_sm_freq)
pico.dac_set_voltage(2.5)

csvname = '221206_dac_2p5.csv'

try:
    ### Connect Keithley2400
    sourcemeter = Keithley2400("GPIB::15")
    sourcemeter.apply_current()
    sourcemeter.measure_voltage()
    sourcemeter.compliance_voltage = 10
    sourcemeter.source_current = 0
    sourcemeter.voltage_range = 5
    sourcemeter.enable_source()

    d = {}
    d['isource (A)'] = np.arange(-100, 101, 1)*1e-3 # mA
    d['vldo (V)'] = np.zeros(d['isource (A)'].shape)

    for idx, i in enumerate(d['isource (A)']):
        sourcemeter.source_current = i
        time.sleep(1e-3)
        d['vldo (V)'][idx] = sourcemeter.voltage

    ### Shutdown
    #sourcemeter.write(':SYST:LOC')
    sourcemeter.disable_source()
    sourcemeter.shutdown()

    df = pd.DataFrame(d)
    df.to_csv(csvname, index=False)
    plot(csvname)
except KeyboardInterrupt:
    sourcemeter.disable_source()
    sourcemeter.shutdown()
####################


# Author: Jungho Lee
# Description: 
# History:
#   220826: start writting
#   220828: first version complete
#   220930: 
#       ftdi_stream_make renamed to command_stream_all
#       removed gui, etc, and organized
#       added command_save, command_load
# Methods:
#
# Class dac7565():
#   set: set parameters and load_db
#   set_vref: update reference voltage from (-2.5,0) for accurate calculation of code
#   open: open the FT2232H channel
#   close: close the FT2232H channel
#   command_*: generate a bus output in 8b int and add it to command
#   seq_*: generate 24b bit sequence for dac7565 control in list 
#   ftdi_write_seq: write the generated seq to dac
#   ftdi_set_voltage: write voltage setting sequence to dac using ftdi_write_seq
#   ftdi_int_ref_power_down: (unused) tried to REFH powerdown before boot, but failed
#
# DAC7565 control waveform from datasheet
# ENB    ---\________________________________________
# SCLK   ______/--\__/--\__/- ... _/--\__/--\________
# SYNCB  ----\_______________ ... _____________/-----
# DIN    ------X--23-X--22-X- ... -X--01-X--00-------


# Modules
import os, time, importlib, csv, pickle
import numpy as np
import tkinter as tk
from tkinter import ttk
from jungho_ftdi import ftdi_search, ftdi_gpio_setup, T_SLEEP, ftdi_gpio_bus_address
from jungho_log import logger
#from gen_inst import *

# Pin Configuration
# FTDT 1 (CN2)

# FTDT 2 (CN3)

DAC_SYNCB= 0x40 # D6: OUT
DAC_SCLK = 0x20 # D5: OUT
DAC_DIN  = 0x10 # D4: OUT
DAC_LDAC = 0x08 # D3: OUT
DAC_ENB  = 0x04 # D2: OUT
DAC_RSTS = 0x02 # D1: OUT
DAC_RSTB = 0x01 # D0: OUT

DAC_SCLK = DAC_SCLK + 0x80 # D7: Monitor

class dac7565():
    # Reference voltage
    # Currently setup uses internal reference
    vrefl = -2.5 # Volt
    #vrefh = 2.5 # Volt
    vrefh = 0 # Volt

    # db file
    csvname = 'dac7565.csv'

    # ftdi control
    ftdi = None
    ftdi_sn = 'FT61VY4N'
    ftdi_interface = 2 # 1 or 2
    ftdi_frequency = 1e6 # Hz
    ftdi_dir = DAC_SYNCB+DAC_SCLK+DAC_DIN+DAC_LDAC+DAC_ENB+DAC_RSTS+DAC_RSTB
    ftdi_init = 0x00 | DAC_SYNCB | DAC_ENB | DAC_RSTB
    ftdi_status = 0x00
    command = []

    # Stream
    bit_stream_file = 'bit_stream.txt'
    bit_stream = None
    vstream_zero = vrefl
    vstream_one = vrefh

    # Initial setup
    def set (self, bus, address, frequency):
        self.ftdi_bus = bus
        self.ftdi_address = address
        self.ftdi_frequency = frequency
    def set_vref (self, vrefl, vrefh):
        self.vrefl = vrefl
        self.vrefh = vrefh
    def set_vstream (self, vl, vh):
        self.vstream_zero = vl
        self.vstream_one = vh

    # Device Open/Close
    def open (self):
        log.info('open - {}-h{:02x}, {}Hz, dir=0x{:02x}, init=0x{:02x}'.format(
            self.ftdi_bus, self.ftdi_address, self.ftdi_frequency, 
            self.ftdi_dir, self.ftdi_init))
        self.ftdi = ftdi_gpio_bus_address(
            bus = self.ftdi_bus,
            address = self.ftdi_address,
            freq = self.ftdi_frequency, 
            direction = self.ftdi_dir,
            init = self.ftdi_init
        )
    def close (self):
        log.info('close - {}-h{:02x}, {}Hz, dir=0x{:02x}'.format(
            self.ftdi_bus, self.ftdi_address, self.ftdi_frequency, self.ftdi_dir))
        self.ftdi.close()

    # Methods for generating commands
    def command_init (self):
        self.ftdi_status = 1*DAC_SYNCB + 0*DAC_SCLK + 0*DAC_DIN + 0*DAC_LDAC + 1*DAC_ENB + 0*DAC_RSTS + 1*DAC_RSTB
        self.command.append(self.ftdi_status)
    def command_enable(self):
        self.ftdi_status = self.ftdi_status & (~DAC_ENB)
        self.command.append(self.ftdi_status)
    def command_sync(self):
        self.ftdi_status = self.ftdi_status & (~DAC_SYNCB)
        self.command.append(self.ftdi_status)
    def command_din(self, din):
        self.ftdi_status = (self.ftdi_status & (~DAC_DIN)) | (din*DAC_DIN)
        self.ftdi_status = self.ftdi_status | DAC_SCLK
        self.command.append(self.ftdi_status)
    def command_sclk_negedge(self):
        self.ftdi_status = self.ftdi_status & (~DAC_SCLK)
        self.command.append(self.ftdi_status)
    def command_sync_end(self):
        self.ftdi_status = self.ftdi_status | DAC_SYNCB
        self.command.append(self.ftdi_status)
    def command_disable(self):
        self.ftdi_status = self.ftdi_status | DAC_ENB
        self.command.append(self.ftdi_status)
    def command_ldac(self):
        self.ftdi_status = self.ftdi_status | DAC_LDAC
        self.command.append(self.ftdi_status)
        self.ftdi_status = self.ftdi_status & (~DAC_LDAC)
        self.command.append(self.ftdi_status)
    def command_print(self):
        for index, line in enumerate(self.command):
            print('{:2}: {:08b}'.format(index, line))
    def command_seq(self, seq):
        self.command_sync()
        for din in seq:
            self.command_din(din)
            self.command_sclk_negedge()
        self.command_sync_end()
    def command_stream(self, sel_vout):
        bit_stream_int_list = [int(char) for char in self.bit_stream] # 0/1 list
        for bit in bit_stream_int_list:
            if bit == 0:
                self.command_seq(self.seq_set_voltage(sel_vout, self.vstream_zero))
            elif bit == 1:
                self.command_seq(self.seq_set_voltage(sel_vout, self.vstream_one))
    def command_stream_all(self, sel_vout):
        self.command_init()
        self.command_enable()
        self.command_stream(sel_vout)
    def command_reset(self):
        self.command = []
    def command_save(self, picklename):
        with open(picklename, 'wb') as fp:
            pickle.dump(self.command, fp)
    def command_load(self, picklename):
        with open(picklename, 'rb') as fp:
            self.command = pickle.load(fp)

    # Voltage control
    def seq_v_to_u12b (self, v):
        if v > self.vrefh:
            log.error('v_to_u12b - v is higher than vrefh')
        elif v < self.vrefl:
            log.error('v_to_u12b - v is lower than vrefl')
        else:
            code = round((v-self.vrefl)/(self.vrefh-self.vrefl)*4095)
            return [int(char) for char in '{:012b}'.format(code)]
    def seq_sequential_control (self, sel_vout):
        sel_vout = sel_vout.upper()
        seq = [0, 0, 0, 1, 0] # DB23-DB19: 0, 0, LD1, LD0, 0
        if sel_vout == 'VOUTA':
            seq.extend([0, 0])
        elif sel_vout == 'VOUTB':
            seq.extend([0, 1])
        elif sel_vout == 'VOUTC':
            seq.extend([1, 0])
        elif sel_vout == 'VOUTD':
            seq.extend([1, 1])
        seq.extend([0]) # 0=normal, 1=powerdown
        return seq
    def seq_set_voltage(self, sel_vout, v):
        seq = self.seq_sequential_control(sel_vout)
        seq.extend(self.seq_v_to_u12b(v))
        seq.extend([0,0,0,0]) # don't-care bits
        return seq
    def ftdi_write_seq(self, seq, verbose=False):
        ### Generate command series
        self.command_init()
        self.command_enable()
        self.command_seq(seq)
        # self.command_ldac()
        # self.command_disable()

        ### Monitor
        if verbose:
            self.command_print()
        
        ### Write command
        self.ftdi.write(self.command)
        time.sleep(T_SLEEP)

        ### Return to initial state
        self.command = []
    def ftdi_set_voltage(self, sel_vout, v, verbose=False):
        seq = self.seq_set_voltage(sel_vout, v)
        self.ftdi_write_seq(seq, verbose)
        # Log
        seq_str = ''.join([str(bit) for bit in seq])
        #log.info('ftdi_set_voltage - {} {:4.2f} V. seq: {}_{}_{}'.format(
        #sel_vout.upper(), v, seq_str[:8], seq_str[8:8+12], seq_str[8+12:]))
    def ftdi_int_ref_power_down(self, verbose=False):
        seq = [int(char) for char in '{:024b}'.format(0x012000)]
        self.ftdi_write_seq(seq, verbose)
        # Log
        seq_str = ''.join([str(bit) for bit in seq])
        log.info('ftdi_int_ref_power_down - seq: {}_{}_{}'.format(
            seq_str[:8], seq_str[8:8+12], seq_str[8+12:]))
    def ftdi_write(self, verbose=False):
        if verbose:
            self.command_print()
        log.info('ftdi_write - start: len = {}'.format(len(self.command)))
        self.ftdi.write(self.command)
        time.sleep(T_SLEEP)
        log.info('ftdi_write - end: len = {}'.format(len(self.command)))

    ### Streaming
    def stream_load(self, db=bit_stream_file):
        self.bit_stream_file = db
        with open(db, 'r') as fp:
            self.bit_stream = fp.readline()[:-1] # without \n
        log.info('stream_load - {}'.format(db))
    def ftdi_stream(self, sel_vout, verbose=False, return_init=True):
        ### Generate command series
        self.command_stream_all(sel_vout)
        ### Monitor
        if verbose:
            self.command_print()
        ### Write command
        self.ftdi.write(self.command)
        time.sleep(T_SLEEP)
        ### Return to initial state
        if return_init:
            self.command = []
        ### Log
        log.info('ftdi_write_stream - channel = {}, length = {}'
                .format(sel_vout, len(self.bit_stream)))

    # Others for test purpose
    def write_test(self):
        self.ftdi.write(0x10)
        time.sleep(T_SLEEP)
        self.ftdi.write(0x00)


if __name__ == '__main__':
    ### Main parameters
    func = 5
    ''' func
    0: Disable external reference of DAC7565
    1: set_voltage
    2: sweep dac voltage and measure power
    3: sweep dac voltage and measure chip VDD
    4: program chip when vdd=0.7V
    5: program chip when using light
    '''
    sel_vout = 'VOUTB'
    vrefh = 5 #V
    vrefl = 0 #V
    vl = 3.95 #V
    vh = 3.98 #V
    f_ftdi=1e6
    # GOC parameter
    fname = '221105_leg.bin'
    leg = {'fl': 0, 'fr': 0, 'rl': 0, 'rr': 0} # 0 or 1
    t_period = 1/3 #sec
    t_start = 15 #sec

    # Control DAC using FTDI
    dac = dac7565()
    #dac.set(bus=0, address=0xfe, frequency=f_ftdi) # laptop
    dac.set(bus=0, address=0x02, frequency=f_ftdi) # vlsilab-26
    dac.set_vref(vrefl=vrefl, vrefh=vrefh)
    dac.set_vstream(vl=vl, vh=vh)

    if func == 0:
        log = logger('_func0')
        dac.open()
        dac.ftdi_int_ref_power_down()
    elif func == 1:
        log = logger('_func1')
        dac.open()
        dac.ftdi_set_voltage(sel_vout,vrefh)
        time.sleep(5)
        dac.ftdi_set_voltage(sel_vout,vh)
    elif func == 1.1:
        log = logger('_amb_test')
        dac.open()
        while True:
            vtest = input('V TEST: ')
            log.info('testing - {} V'.format(vtest))
            dac.ftdi_set_voltage(sel_vout,vrefh)
            time.sleep(1)
            dac.ftdi_set_voltage(sel_vout, float(vtest))
    elif func == 2:
        log = logger('_optical_power_meas')
        dac.open()
        dac.ftdi_int_ref_power_down()
        csvname = '221026_meas.csv'
        import pyvisa
        import pandas as pd
        from math import pi
        from ThorlabsPM100 import ThorlabsPM100
        rm = pyvisa.ResourceManager()
        inst = rm.open_resource('USB0::0x1313::0x8078::P0005898::INSTR')
        power_meter = ThorlabsPM100(inst=inst)

        v_list = np.arange(0, 5.01, 0.1)
        p_list = np.zeros(v_list.shape) # power in watt
        pi_list = np.zeros(v_list.shape) # power in watt/m2
        for idx, v in enumerate(v_list):
            dac.ftdi_set_voltage(sel_vout, v)
            time.sleep(0.1)
            p_list[idx] = power_meter.read # [W], Sensor Diameter = 9.5 mm
            pi_list[idx] = p_list[idx] / (pi * 9.5e-3**2 / 4)
        df = pd.DataFrame({'voltage (V)':v_list, 'power (W)':p_list, 'power intensity (W/m2)': pi_list})
        df.to_csv(csvname, index=False)
    elif func == 3:
        log = logger('_vdd_meas')
        import pyvisa
        import pandas as pd
        from ThorlabsPM100 import ThorlabsPM100
        from pymeasure.instruments.keithley import Keithley2400
        csvname = '2211104_meas_vdd.csv'

        ### Connect DAC
        dac.open()
        dac.ftdi_int_ref_power_down()

        ### Connect Keithley2400
        #sourcemeter = Keithley2400("GPIB::24") # laptop
        sourcemeter = Keithley2400("GPIB::12") # vlsilab-24
        # sourcemeter.reset()
        # sourcemeter.use_front_terminals()
        sourcemeter.apply_current()
        sourcemeter.measure_voltage()
        sourcemeter.compliance_voltage = 10
        sourcemeter.source_current = 0 # A
        sourcemeter.enable_source()
        #sourcemeter.ramp_to_current(5e-3)
        log.info('sourcemeter succesfully set up')

        log.info('sweeping light intensity')
        vdac_list = np.arange(0, 5.01, 0.1)
        vdd_list = np.zeros_like(vdac_list)
        vdd_rest_list = np.zeros_like(vdac_list)
        for idx, v in enumerate(vdac_list):
            dac.ftdi_set_voltage(sel_vout, v)
            time.sleep(0.1)
            vdd_list[idx] = sourcemeter.voltage
            dac.ftdi_set_voltage(sel_vout, vrefh) # 5V = LED off
            vdd_rest_list[idx] = sourcemeter.voltage
        df = pd.DataFrame({'vdac (V)':vdac_list, 'vdd (V)':vdd_list, 'vdd_rest (V)':vdd_rest_list})
        df.to_csv(csvname, index=False)
        log.info('vdd measured - exported {}'.format(csvname))
        sourcemeter.shutdown()
    elif func == 4:
        from gen_inst import *
        import pyvisa
        import pandas as pd
        from ThorlabsPM100 import ThorlabsPM100
        from pymeasure.instruments.keithley import Keithley2400
        log = logger('_chip_program')

        ### Connect Keithley2400
        sourcemeter = Keithley2400("GPIB::12")
        sourcemeter.apply_voltage()
        sourcemeter.measure_voltage()
        sourcemeter.compliance_current = 10e-3
        sourcemeter.source_voltage = 0 # V, turn off
        sourcemeter.current_range = 10e-6
        sourcemeter.enable_source()
        #sourcemeter.ramp_to_current(5e-3)
        log.info('sourcemeter succesfully set up - vsrc=0')

        ### Connect DAC
        dac.open()
        dac.ftdi_int_ref_power_down()

        ### Parameters
        # calculation
        binfile = fname + '_bit.bin'
        csvfile = fname + '.csv'
        picklefile = fname+'_command.pickle'

        ### Generate instruction timeseries csv - comment out if not needed
        gen_inst_bin(leg=leg, fname=binfile)
        bin_string = bin_full_command(binfile)
        #bin_string = '1'*50 + ('00001'+'0010'+ '1'*50)*100
        #bin_string = ''
        ##bin_string = bin_string + bin_goc_activate() #+ bin_goc_send_header() + '1'*50
        #for i in range(10):
        #    bin_string += bin_goc_activate()
        d = bin_to_manchester_transition(bin_string, t_period=t_period, t_start=t_start, reverse_bit=True)
        timeseries_to_csv(d, csvfile)
        log.info('file written - {}'.format(csvfile))

        ### Chip initialization
        dac.ftdi_set_voltage(sel_vout, vrefh)
        #sourcemeter.apply_current()
        #sourcemeter.source_current = 0 # A, turn on
        #sourcemeter.compliance_voltage = 10 # V
        #sourcemeter.enable_source()
        #log.info('sourcemeter succesfully set up - isrc=0')
        sourcemeter.source_voltage = 0.7
        log.info('sourcemeter succesfully set up - vsrc=0.7')
        sourcemeter.write(':SYST:LOC')
        time.sleep(1)

        ### Chip programming
        init_time = time.time()
        with open(csvfile) as fp:
            log.info('ftdi write timeseries - len = {}'.format(sum(1 for row in fp)))
        with open(csvfile) as fp:
            reader = csv.reader(fp)
            for row in reader:
                target_time = float(row[0]) # sec
                target_value = int(row[1]) # 0 or 1
                cur_time = time.time() - init_time
                while cur_time <= target_time:
                    time.sleep(0.0001) # s
                    cur_time = time.time() - init_time
                if target_value == 0:
                    dac.ftdi_set_voltage(sel_vout, vl)
                elif target_value == 1:
                    dac.ftdi_set_voltage(sel_vout, vh)
    elif func == 5:
        from gen_inst import *
        import pyvisa
        import pandas as pd
        from ThorlabsPM100 import ThorlabsPM100
        from pymeasure.instruments.keithley import Keithley2400
        log = logger('_chip_program_light')
        log.info('vl={:.2f}, vh={:.2f}'.format(vl, vh))

        ### Connect Keithley2400
        sourcemeter = Keithley2400("GPIB::12")
        sourcemeter.apply_current()
        sourcemeter.measure_voltage()
        sourcemeter.compliance_voltage = 10
        sourcemeter.source_current = 0 # V, turn off
        sourcemeter.enable_source()
        #sourcemeter.ramp_to_current(5e-3)
        log.info('sourcemeter succesfully set up - isrc=0')

        ### Connect DAC
        dac.open()
        dac.ftdi_int_ref_power_down()

        ### Parameters
        # calculation
        binfile = fname + '_bit.bin'
        csvfile = fname + '.csv'
        picklefile = fname+'_command.pickle'

        ### Generate instruction timeseries csv - comment out if not needed
        gen_inst_bin(leg=leg, fname=binfile)
        bin_string = bin_full_command(binfile)
        d = bin_to_manchester_transition(bin_string, t_period=t_period, t_start=t_start, reverse_bit=True)
        timeseries_to_csv(d, csvfile)
        log.info('file written - {}'.format(csvfile))

        ### Turn off
        dac.ftdi_set_voltage(sel_vout, vrefh)
        sourcemeter.write(':SYST:LOC')
        time.sleep(5)

        ### Initialize
        dac.ftdi_set_voltage(sel_vout, vh)
        time.sleep(10)
        init_time = time.time()
        with open(csvfile) as fp:
            log.info('ftdi write timeseries - len = {}'.format(sum(1 for row in fp)))
        with open(csvfile) as fp:
            reader = csv.reader(fp)
            for row in reader:
                target_time = float(row[0]) # sec
                target_value = int(row[1]) # 0 or 1
                cur_time = time.time() - init_time
                while cur_time <= target_time:
                    time.sleep(0.001) # 10us
                    cur_time = time.time() - init_time
                if target_value == 0:
                    dac.ftdi_set_voltage(sel_vout, vl)
                elif target_value == 1:
                    dac.ftdi_set_voltage(sel_vout, vh)

    # dac.close() 
    ## Don't close: Unless waiting until all the streaming ends, output will just end by this.


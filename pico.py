# Author: Jungho Lee
# Description: Raspberry Pi Pico Handler
# History:
#   221116 v0.1: initial commit with idle state implementation
#   221117: added stream_monitor
#   221201: Changed for DAC121S101 // 16bit command
#   230101: changed command from character to string
#   230101: added clk_ext/cmp_ext
#   230111: Modified for USB version

import os
import sys
import serial
import time
import threading

class pico():
    ### Parameters
    vrefl = 0
    vrefh = 5
    vlow = 0
    vhigh = 5
    
    command_freq = 'freq\n'
    command_vlevel = 'vlowhigh'
    command_dac_sequence = 'dac_command'
    command_dac_stream = 'dac_stream\n'
    command_stream_idle = 'dac_idle_onoff\n'
    command_clk_ext = 'clk_ext\n'
    command_cmp_ext = 'cmp_ext\n'

    dac_prefix = [0, 0, 0, 0] # 2 don't care terms, 0 0 for normal operation (powerdown)
    dac_sm_cycles = 50 # SYNCB, SCLK, DIN totol state machine cycles for 12b DAC programming
    stream_digital = 0
    stream_analog = 1
    stream_mode = stream_digital

    ### Generic methods
    def __init__(self, port, baud, comment='dac_control'):
        self._serial = serial.Serial(port, baud)
        self.logger_init(comment)
    def logger_init (self, comment):
        import logging
        from datetime import datetime
        log = logging.getLogger('jungho_logger')
        log.setLevel(level=logging.DEBUG)
        formatter = logging.Formatter("[%(asctime)s %(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")
        ## File Handler
        logname = 'logs/'+datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_{}.log".format(comment)
        fh = logging.FileHandler(logname)
        fh.setLevel(level=logging.DEBUG)
        fh.setFormatter(formatter)
        log.addHandler(fh)
        ## Stream Handler
        ch = logging.StreamHandler()
        ch.setLevel(level=logging.DEBUG)
        ch.setFormatter(formatter)
        log.addHandler(ch)
        self.log = log
    def logger_off (self):
        self.log.disabled = True
    def logger_on (self):
        self.log.disabled = False

    ### Serial communication helper
    def write_line(self, command):
        if type(command) == bytes:
            self._serial.write(command + b'\n')
        elif type(command) == str:
            self._serial.write(bytes((command+'\n').encode('utf-8')))

    def read_line(self):
        while self._serial.inWaiting() == 0:
            pass
        return self._serial.readline().rstrip()
        #try:
        #    return self._serial.readline().rstrip().decode('utf-8')
        #except UnicodeDecodeError:
        #    return self._serial.readline().rstrip()

    def write_raw(self, command):
        self._serial.write(command)
    def read_raw(self):
        while self._serial.inWaiting() == 0:
            pass
        return self._serial.read_all()
    def write_newline(self):
        self.write_raw(bytes('\n'.encode('ascii')))

    ### DAC control
    def dac_set_vref(self, vrefl, vrefh):
        self.vrefl = vrefl
        self.vrefh = vrefh

    def dac_set_vlevel(self, vlow=vlow, vhigh=vhigh):
        if (vlow < self.vrefl) and logger_on:
            self.log.error('Error: vlow < vrefl')
        else:
            self.vlow = vlow
        if (vhigh > self.vrefh) and logger_on:
            self.log.error('Error: vhigh > vrefh')
        else:
            self.vhigh = vhigh
        code_low = self._dac_v_to_code(vlow)
        code_high = self._dac_v_to_code(vhigh)
        # serial communication
        self.log.info('dac_set_vlevel - write = {} {} {}'.format(self.command_vlevel, code_low, code_high))
        self.write_line(self.command_vlevel)
        self.write_line(self._dac_code_to_str(code_low))
        self.write_line(self._dac_code_to_str(code_high))
        self.log.info('dac_set_vlevel - echoed = {}'.format(self.read_line()))

    def dac_set_code(self, code):
        if code < 0:
            self.log.error('Error: v < min_code 0')
        elif code > 4095:
            self.log.error('Error: v > max_code 4095')
        # serial communication
        self.log.info('dac_set_code - write = {} {}'.format(self.command_dac_sequence, code))
        self.write_line(self.command_dac_sequence)
        self.write_line(self._dac_code_to_str(code))
        self.log.info('dac_set_code - echoed = {}'.format(self.read_line()))

    def dac_set_voltage(self, v):
        if v < self.vrefl:
            self.log.error('Error: v < vrefl')
        elif v > self.vrefh:
            self.log.error('Error: v > vrefh')
        code = self._dac_v_to_code(v)
        # serial communication
        self.log.info('dac_set_voltage - write = {} {}'.format(self.command_dac_sequence, code))
        self.write_line(self.command_dac_sequence)
        self.write_line(self._dac_code_to_str(code))
        self.log.info('dac_set_voltage - echoed = {}'.format(self.read_line()))

    def dac_set_frequency(self, freq):
        if freq < 2e3 or freq > 125e6:
            self.log.error('dac_set_frequency - {:.0f} not supported (2k-125M)'.format(freq))
        else:
            command = self.command_freq
            command += '{:f}'.format(freq)
            self.log.info('dac_set_frequency - write = {}'.format(command.replace('\n',' ')))
            self.write_line(command)
            self.log.info('dac_set_frequency - echoed = {}'.format(self.read_line()))

    def _dac_v_to_code(self, v):
        return round((v-self.vrefl)/(self.vrefh-self.vrefl)*4095)
    def _dac_code_to_str(self, code):
        return '{}'.format(code)
    ### Stream control
    def stream_str_to_byte(self, string):
        stream_chunks = [string[pos:pos+8] for pos in range(0, len(string), 8)]
        stream_bytes_values = [int(chunk[::-1], 2) for chunk in stream_chunks] # Reversed
        self.stream_byte = bytes(stream_bytes_values)

    def stream_read_from_file(self, filename):
        # support comment, arbitrary number of lines
        with open(filename, 'r') as fp:
            lines = fp.readlines()
        self.stream_str = ''.join(line.split('#')[0].rstrip() for line in lines)
        self.stream_str_to_byte(self.stream_str)
    def stream_set_mode(self, mode):
        if mode == 'analog':
            self.stream_mode = self.stream_analog
            self.log.info('stream_set_mode - analog')
        elif mode == 'digital':
            self.stream_mode = self.stream_digital
            self.log.info('stream_set_mode - digital')

    def stream_write(self, freq):
        # Send frequency
        if freq < 2e3 or freq > 125e6:
            self.log.error('stream_write - {:.0f} not supported (2k-125M)'.format(freq))
        else:
            if self.stream_mode == self.stream_analog:
                command = self.command_dac_stream
                self.log.info('stream_write - mode analog')
                command += '{:f}'.format(freq * self.dac_sm_cycles)
            elif self.stream_mode == self.stream_digital:
                command = self.command_cmp_ext
                self.log.info('stream_write - mode digital')
                command += '{:f}'.format(freq)
            self.log.info('stream_write - write = {} Hz'.format(command.replace('\n',' ')))
            self.write_line(command)
            self.log.info('stream_write - echoed = {}'.format(self.read_line()))
        # Send data
        command = bytes(self.stream_byte)
        command += '\n'.encode('ascii')
        self.log.info('stream_write - length = {} byte (max=128k from uf2)'.format(len(command)-2))
        self.write_raw(command)
        self.log.info('stream_write - echoed = {} byte'.format(self.read_line()))
    def stream_idle(self, is_on):
        command = self.command_stream_idle
        if is_on:
            command += 'on'
        else:
            command += 'off'
        self.log.info('stream_idle - write = {}'.format(command.replace('\n',' ')))
        self.write_line(command)
        self.log.info('stream_idle - echoed = {}'.format(self.read_line()))

    ### CLK_EXT
    def clk_ext_set_frequency(self, freq):
        if freq < 1e3 or freq > 62.5e6: # system clock = 2k-125M (133M)
            self.log.error('clk_ext_set_frequency - {:.0f} not supported (1k-62.5M)'.format(freq))
        else:
            command = self.command_clk_ext
            command += '{:f}'.format(freq)
            self.log.info('clk_ext_set_frequency - write = {} Hz'.format(command.replace('\n',' ')))
            self.write_line(command)
            self.log.info('clk_ext_set_frequency - echoed = {}'.format(self.read_line()))



if __name__ == '__main__':
    #pico_port = '/dev/ttyACM0' # '/dev/serial0'
    pico_port = 'COM8'
    #baud = 115201
    #baud = 921600
    baud = 9600

    pico = pico(pico_port, baud, 'all_test')

    # CLK_EXT
    pico.clk_ext_set_frequency(100e3)
    input('Next')
    pico.clk_ext_set_frequency(10e3)
    input('Next')

    pico.dac_set_vref(vrefl=0, vrefh=5)
    pico.dac_set_vlevel(vlow=1, vhigh=4)
    pico.dac_set_code(2048)
    input('Next')
    pico.dac_set_voltage(1)
    input('Next')
    #pico.dac_set_frequency(10e3) # useless
    #input('Next')

    pico.stream_str_to_byte('01'*100)
    #pico.stream_read_from_file

    pico.stream_set_mode('analog')
    pico.stream_write(2e3)
    input('Next')

    pico.stream_set_mode('digital')
    pico.stream_write(150e3)
    input('Next')

    pico.stream_idle(True)
    pico.stream_set_mode('digital')
    pico.stream_write(150e3)
    pico.stream_idle(False)
    input('Next')

    pico.stream_idle(True)
    pico.stream_set_mode('analog')
    pico.stream_write(20e3)
    pico.stream_idle(False)
    input('Next')


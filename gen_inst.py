# Author: Jungho Lee
# Description: Generate simple instructions to overwrite FREQ and PHA parameters
# Included methods:
#   # dec-to-bin methods
#   bin_low (dec)
#   bin_high (dec)
#   #
#   gen_inst_bin (leg, fname='', goc_clk_sel='100', onchip_clk_seln='0')
#   bin_goc_activate (id='')
#   bin_goc_send_header
#   bin_goc_send_memaddr
#   bin_import_inst (fname)
#   bin_checksum (fname)
#   bin_keep_send_clk
#   bin_to_manchester_transition
# Data I/O:
#   transition_to_sample
#   timeseries_to_csv
# History: 
#   220713 - First commit
#   220721 - Reverse bit order
#   220725 - Added bin_full_command
#   220731 - Deleted pandas, matplotlib, scipy library for RPi
#   220930 - Added bin_to_manchester

# #%% Modules
import numpy as np
import os, sys
from math import *
from translate import *

### dec to bin methods
def bin_low3 (dec):
    return '{:03b}'.format(dec % (2**3))
def bin_low2 (dec):
    return '{:02b}'.format(dec % (2**2))
def bin_low1 (dec):
    return '{:01b}'.format(dec % (2**1))
def bin_low (dec, num_bin):
    form = '{:0'+'{}'.format(num_bin)+'b}'
    return form.format(dec % (2**num_bin))
def bin_high (dec, num_total, num_bin):
    form = '{:0'+'{}'.format(num_total)+'b}'
    return form.format(dec)[:num_bin]

#%% Main
def gen_inst_bin(leg, fname='', goc_clk_sel='100', onchip_clk_seln='0', print_line=False):
    '''
    Generate a machine-language instruction file which overwrite the leg on/off states
    as in the dict leg. Exported file example is below.
    
    0000_11_00000 // mov stop d_infinite
    1001_10_1_0000 // wti r0 upper d_0
    1100_10_0_0000 // add r0 d_0
    ...
    Parameters
    ----------
    leg : dictionary
        Example : {'fl': 1, 'fr': 1, 'rl': 0, 'rr': 0} # 0 or 1
    fname : string, optional
        Machine-language instructions are exported to fname. 
        Doesn't write the output in file if fname is ''.
        The default is ''.
    goc_clk_sel : string, optional
        Clock selection parameter bits in the chip. The default is '100'.
        Recoommend not touch this value.
    onchip_clk_seln : string, optional
        Onchip clock selection aprameter bit in the chip. Select onchip clock when 0.
        The default is '0'. Recommend not to touch this value.
    print_line : bool, optional
        If True, it prints all processed lines.
    Returns
    -------
    None.
    '''
    ### Local parameter
    PHASE_UP = 16
    #goc_clk_sel = '100'
    #onchip_clk_seln = '0' # default is '1', should be set to 0 after GOC programming

    ### Initialization
    mrf = ['0'*8]*5 # We overwrite only MEM[0] - MEM[4]
    # freq = np.zeros(4, dtype=int) # 3b, should be < 8, 0 uses clk_count[1:0] (fastest), 4567 are equivalent
    freq = {'fl': 0, 'fr': 0, 'rl': 0, 'rr': 0} 
    # pha = np.zeros(4, dtype=int) # 6b, should be < 64
    pha = {'fl': 0, 'fr': 0, 'rl': 0, 'rr': 0} 
    with open(fname, 'w') as fp:
        fp.write('')
    
    # Assign binarized phase parameter
    for key in pha.keys():
        if leg[key] is 0:
            pha[key] = PHASE_UP
        elif leg[key] is 1:
            pha[key] = 0
    
    ## MRF Hierarchy
    # MRF[0] = 011 / 011 / 01 = freq1-3
    # MRF[1] = 1 / 011 / 0000 = freq3-4, pha1
    # MRF[2] = 00 / 000000    = pha1-2
    # MRF[3] = 010000 / 01    = pha3-4
    # MRF[4] = 0000 / 100 / 1 = pha4, goc_clk_sel, onchip_clk_seln
    
    # Create MRF
    mrf [0] = bin_low(freq['fl'],3) + bin_low(freq['fr'],3) + bin_high(freq['rl'],3,2)
    mrf [1] = bin_low(freq['rl'],1) + bin_low(freq['rr'],3) + bin_high(pha['fl'], 6,4)
    mrf [2] = bin_low(pha['fl'], 2) + bin_low(pha['fr'], 6)
    mrf [3] = bin_low(pha['rl'], 6) + bin_high(pha['rr'],6, 2)
    mrf [4] = bin_low(pha['rr'], 4) + goc_clk_sel + onchip_clk_seln
    
    # Write instructions
    num_line = 0
    
    mov('stop', 'infinite', fname=fname, print_line=print_line) # Stop first
    num_line = num_line + 1
    
    for i in range(5):
        wti('r0', 'upper', int(mrf[i][:4], 2), fname=fname, print_line=print_line) # write imm upper R0
        add('r0', int(mrf[i][4:8], 2), fname=fname, print_line=print_line) # add imm to lower R0
        stor('r0', i, fname=fname, print_line=print_line) # store R0 to mem_addr i
        num_line = num_line + 3
    
    mov('forward', 15, fname=fname, print_line=print_line) # move forward for 15 times (LEG_ON=1111)
    num_line = num_line + 1
    
    b(num_line-1, fname=fname, print_line=print_line) # branch to the previous line (infinitely move)
    num_line = num_line + 1
    
    for i in range(32-num_line):
        mov('stop', 'infinite', fname=fname, print_line=print_line) # default behavior
        num_line = num_line + 1

    if fname is not '':
        print('[Info] File "{}" is written.'.format(fname))

def bin_goc_activate (id=''):
    '''
    This part outputs bit serial for GOC activation. It contains training bit '1's and passcode.
    This version doesn't support ID_CODE yet.
    '''
    #`define GOC_PASSCODE_LIGHT    16'h1994
    # dec2bin(hex2dec('1994')) = '0001_1001_1001_0100'
    bin_string = '1'*50 + '1010' # 66 times of '1'. This number of occurence is matched with the testbench.
    bin_string = bin_string + '0010100110011000' # passcode in reverse order
    return bin_string
    
def bin_goc_send_header ():
    '''
    In header part, GOC sends the length of the task, which is 31.
    It makes
    > length=`EP_PROG_NUM_BYTES1-1;
    Then it sends
    > goc_send_base(task_length, $bits(task_length));
    '''
    return '11111'

def bin_goc_send_memaddr ():
    # `define EP_PROG_START_ADDR1 5'h0
    # task_mem_addr = `EP_PROG_START_ADDR1;
    # goc_send_base(task_mem_addr, $bits(task_mem_addr));
    return '00000'

def bin_import_inst (fname):
    '''
    Import inst_bin file "fname" which contains underscores(_) and comments(//).
    This method elminates those parts and make a single string of series of 0/1s.
    For example, Input with
    > 0000_11_00000 // mov stop d_infinite
    > ...
    will give
    > '00001100000...'
    Parameters
    ----------
    fname : string
        Example : 'something.bin'
    Returns
    -------
    bin_string : string
        '0000110000....'
    '''
    bin_string = ''
    with open(fname, 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            line = line.split(" //")[0].replace('_','')[::-1]
            bin_string = bin_string + line
    return bin_string

def bin_checksum (fname):
    checksum = 0
    with open(fname, 'r') as fp:
        lines = fp.readlines()
        for line in lines:
            checksum = checksum + int(line.split(" //")[0].replace('_',''), 2) # bin to dec
    return bin_low(checksum,8)[::-1]

def bin_keep_send_clk ():
    return '1'*11*700 # Matched with testbench

def bin_full_command (fname):
    bin_string = ''
    bin_string = bin_string + bin_goc_activate()
    bin_string = bin_string + bin_goc_send_header()
    bin_string = bin_string + bin_goc_send_memaddr()
    bin_string = bin_string + bin_import_inst(fname)
    bin_string = bin_string + bin_checksum(fname)
    bin_string = bin_string + bin_keep_send_clk()
    return bin_string

def bin_to_manchester (bin_string, reverse_bit=True):
    '''
    Generate time-value table for bin_string.

    Parameters
    ----------
    bin_string : string

    Returns
    -------
    d : dictionary
        d['value'] = [0, 1, 0, 1, ...]
    '''
    if reverse_bit:
        bin_string = bin_string.replace('0','2').replace('1','0').replace('2','1')

    bits_arr = np.array([int(bin_char) for bin_char in list(bin_string)])
    one_mask = bits_arr == 1
    zero_mask = bits_arr == 0

    d0 = one_mask*0 + zero_mask*1
    d1 = one_mask*1 + zero_mask*0
    d_transition = np.hstack([d_start, np.vstack([d0, d1]).T.reshape(-1)])

    d = dict()
    d['value'] = d_transition
    return d

def bin_to_manchester_transition (bin_string, t_period, t_start=0, d_start=1, reverse_bit=True):
    '''
    Generate time-value table for bin_string.
    Parameters
    ----------
    bin_string : string
    t_period : float
        Value in second.
    t_start : float
        Value in second. Default is 0.
    d_start : int
        Binary value. Default is 0.
    Returns
    -------
    d : dictionary
        d['time'] = [0, 2e-3, 4e-3, ...]
        d['value'] = [0, 1, 0, 1, ...]
    '''
    if reverse_bit:
        bin_string = bin_string.replace('0','2').replace('1','0').replace('2','1')

    t0 = np.arange(len(bin_string))*t_period # time step
    t1 = t0 + t_period/2 # half-cycle delay

    bits_arr = np.array([int(bin_char) for bin_char in list(bin_string)])
    one_mask = bits_arr == 1
    zero_mask = bits_arr == 0

    d0 = one_mask*0 + zero_mask*1
    d1 = one_mask*1 + zero_mask*0

    t_transition = np.hstack([0, np.vstack([t0, t1]).T.reshape(-1) +t_start])
    d_transition = np.hstack([d_start, np.vstack([d0, d1]).T.reshape(-1)])

    d = dict()
    d['time'] = t_transition
    d['value'] = d_transition
    return d

def transition_to_sample (dict_transition, t_start, t_stop, t_step):
    '''
    Generate sampled time-value data pairs from transition data dict_transiiton.
    Parameters
    ----------
    dict_transition : dictionary
        dict_transition['time'] = [0, 2e-3, 4e-3, ...]
        dict_transition['value'] = [0, 1, 0, 1, ...]
    t_start : float
        Start time. Value in second.
    t_stop : float
        Stop time. Value in second.
    t_step : float
        Time step for sampling. Value in second.
    Returns
    -------
    d : dictionary
        d['time'] = [0, 2e-3, 4e-3, ...]
        d['value'] = [0, 1, 0, 1, ...]
    '''
    t = dict_transition['time']
    v = dict_transition['value']
    f = interpolate.interp1d(t, v, kind='zero')
    
    d = dict()
    d['time'] = np.arange(t_start, t_stop, t_step)
    d['value'] = f(d['time'])
    return d


def timeseries_to_csv (dict_timeseries, csvname):
    '''
    Export data in dict_timeseries to a csv-format text file.
    dict_timeseries = {'time': [...], 'value': [...]}
    
    Example:     timeseries_to_csv(d, 'csvtest.csv')
    '''
    t = dict_timeseries['time']
    v = dict_timeseries['value']
    with open(csvname, 'w') as fp:
        for time, value in zip(t, v):
            fp.write('{:.6f},{}\n'.format(time, value))
        print('[Info] File "{}" is written.'.format(csvname))


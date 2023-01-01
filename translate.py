# Author: Jungho Lee
# Description: Methods to translate assembly language to machine language
# History: 
#   220717 - Implemented MOV, WTI, ADD, STOR, B

#%% Modules
import numpy as np
import os

#%% Definitions
# ISA states
MOV = '0000'
WAV = '0001'
TS = '0010'
ES = '0011'
CMP = '0100'
B = '0101'
BC = '0110'
STR = '0111'
LDR = '1000'
WTU = '1001'
WTR = '1010'
LS = '1011'
ADD = '1100'
SUB = '1101'
ANOR = '1110'
COT = '1111'

# //mem addr
# `define LEG_DIRE_ADDR   4'd9

# //opcode_cond
# `define OP_EQ       2'd0
# `define OP_NE       2'd1
# `define OP_LT       2'd2
# `define OP_GT       2'd3


# //write_from_sel
# `define WFROM_REG   2'd0
# `define WFROM_MEM   2'd1
# `define WFROM_IMM   2'd2

# //alu_sel
# `define ALU_ADD     2'd0
# `define ALU_SUB     2'd1
# `define ALU_AND     2'd2
# `define ALU_OR      2'd3

#%% ISA implementation
def mov(direction, imm, fname='', print_line=True):
    """
    Move legs.
    
    Parameters
    ----------
    direction : string
        'forward', 'left', 'right', or 'stop'.
    imm : string or int
        'infinite', 'rd', 'rs', 'r0', 'r1', or int below 16.
    fname : string
        File name to write the line. Don't write to file if not given.
    print_line: bool
        Print the line if True
    Returns
    -------
    binary number of length 11 in string type
    
    Example
    -------
    mov('forward', 13)
    > '0000_00_11101 // mov forward d13
'
    """
    dir_dict = {
      'forward': '00', 'left': '01', 'right': '10', 'stop': '11'}
    if direction in dir_dict.keys():
        inst65 = dir_dict[direction]
    else:
        raise ValueError('Wrong value')
    imm_dict = {
      'infinite': '00000', 'rd': '01100', 'rs': '01101', 'r0': '01110', 'r1': '01111'}
    if imm in imm_dict.keys():
        inst40 = imm_dict[imm]
    else:
        if type(imm) == int and imm < 16:
            inst40 = '1' + '{:04b}'.format(imm)
        else:
            raise ValueError('Wrong value')
    comment = ' // mov ' + direction + ' ' + 'd_{}\n'.format(imm)
    line = MOV + '_' + inst65 + '_' + inst40 + comment
    if print_line:
        print(line)
    if fname != '':
        with open(fname, 'a') as fp:
            fp.write(line)
    return line


def wti(dest_reg, loc, imm, fname='', print_line=True):
    """
    Write the immediate value to the target register.
    
    Parameters
    ----------
    dest_reg : string
        'rd', 'rs', 'r0', or 'r1'.
    loc : string
        'upper' or 'lower' to choose which part of the register will be written.
    imm : int
        int below 16.
    fname : string
        File name to write the line. Don't write to file if not given.
    print_line: bool
        Print the line if True
    Returns
    -------
    binary number of length 11 in string type
    
    Example
    -------
    wti('r1', 'upper', 13)
    > '1001_11_1_1101 // wti r1 upper d13'
    """
    reg_dict = {
      'rd': '00', 'rs': '01', 'r0': '10', 'r1': '11'}
    if dest_reg in reg_dict.keys():
        inst65 = reg_dict[dest_reg]
    else:
        raise ValueError('Wrong value')
    loc_dict = {'upper':'1', 
     'lower':'0'}
    if loc in loc_dict.keys():
        inst4 = loc_dict[loc]
    else:
        raise ValueError('Wrong value')
    if type(imm) == int and imm < 16:
        inst30 = '{:04b}'.format(imm)
    else:
        raise ValueError('Wrong value')
    comment = ' // wti ' + dest_reg + ' ' + loc + ' ' + 'd_{}\n'.format(imm)
    line = WTU + '_' + inst65 + '_' + inst4 + '_' + inst30 + comment
    if print_line:
        print(line)
    if fname != '':
        with open(fname, 'a') as fp:
            fp.write(line)
    return line


def add(dest_reg, rega_imm, regb='', fname='', print_line=True):
    """
    dest_reg = rega + regb
    or
    dest_reg = dest_reg + imm
    
    Parameters
    ----------
    dest_reg : string
        Destination register. 'rd', 'rs', 'r0', or 'r1'.
    rega_imm : string or int
        1st operand. 'rd', 'rs', 'r0', 'r1', or int below 16.
    regb : string or int
        2nd operand. 'rd', 'rs', 'r0', or 'r1'.
        Used only when rega_imm is register.
    fname : string
        File name to write the line. Don't write to file if not given.
    print_line: bool
        Print the line if True
    Returns
    -------
    binary number of length 11 in string type
    
    Example
    -------
    add('r0', 'r1', 'r0')
    > '1100_10_1_11_10 // add r0 r1 r0
'
    add('r0', 13)
    > '1100_10_0_1101 // add r0 d13
'
    """
    reg_dict = {
      'rd': '00', 'rs': '01', 'r0': '10', 'r1': '11'}
    if dest_reg in reg_dict.keys():
        inst65 = reg_dict[dest_reg]
    else:
        raise ValueError('Wrong value')
    if rega_imm in reg_dict.keys():
        if regb in reg_dict.keys():
            inst40 = '1_' + reg_dict[rega_imm] + '_' + reg_dict[regb]
            comment = ' // add ' + dest_reg + ' ' + rega_imm + ' ' + regb + '\n'
        else:
            raise ValueError('Wrong value')
    else:
        if type(rega_imm) == int and rega_imm < 16:
            if regb != '':
                raise ValueError('Wrong value')
            else:
                inst40 = '0_' + '{:04b}'.format(rega_imm)
                comment = ' // add ' + dest_reg + ' ' + 'd_{}\n'.format(rega_imm)
        else:
            raise ValueError('Wrong value')
    line = ADD + '_' + inst65 + '_' + inst40 + comment
    if print_line:
        print(line)
    if fname != '':
        with open(fname, 'a') as fp:
            fp.write(line)
    return line


def stor(src_reg, dest_mem, fname='', print_line=True):
    """
    Store value of register src_reg to memory dest_mem
    
    Parameters
    ----------
    src_reg : string
        Source register. 'rd', 'rs', 'r0', or 'r1'.
    dest_mem : int
        Destination memory address. Int below 16
    fname : string
        File name to write the line. Don't write to file if not given.
    print_line: bool
        Print the line if True
    Returns
    -------
    binary number of length 11 in string type
    
    Example
    -------
    add('r0', 'r1', 'r0')
    > '1100_10_1_11_10 // add r0 r1 r0
'
    add('r0', 13)
    > '1100_10_0_1101 // add r0 d13
'
    """
    reg_dict = {
      'rd': '00', 'rs': '01', 'r0': '10', 'r1': '11'}
    if src_reg in reg_dict.keys():
        inst65 = reg_dict[src_reg]
    else:
        raise ValueError('Wrong value')
    if type(dest_mem) == int and dest_mem < 16:
        inst40 = '0_' + '{:04b}'.format(dest_mem)
    else:
        raise ValueError('Wrong value')
    comment = ' // stor ' + src_reg + ' ' + 'd_{}\n'.format(dest_mem)
    line = STR + '_' + inst65 + '_' + inst40 + comment
    if print_line:
        print(line)
    if fname != '':
        with open(fname, 'a') as fp:
            fp.write(line)
    return line


def b(dest_inst, fname='', print_line=True):
    """
    Jump to the indicated destination address dest_inst
    
    Parameters
    ----------
    dest_inst : int
        Destination memory address. Int below 32
    Returns
    -------
    binary number of length 11 in string type
    
    Example
    -------
    b(13)
    > '0101_11_01101 // b d_13
'
    """
    if type(dest_inst) == int and dest_inst < 32:
        inst60 = '11_' + '{:05b}'.format(dest_inst)
    else:
        raise ValueError('Wrong value')
    comment = ' // b ' + 'd_{}\n'.format(dest_inst)
    line = B + '_' + inst60 + comment
    if print_line:
        print(line)
    if fname != '':
        with open(fname, 'a') as fp:
            fp.write(line)
    return line


if __name__ == '__main__':
    mov('forward', 13)
    wti('r1', 'upper', 13)
    add('r0', 13)
    stor('r0', 13)
    b(13)

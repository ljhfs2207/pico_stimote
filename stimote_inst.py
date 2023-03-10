import sys
import os
import numpy as np
import pickle

sys.path.append('/home/ddlabpi/pico/stimote/')
from pico import pico

root = './stimote_inst'
#check_filetime = 'moncap0_stimq1.pickle'

#gen_new = False
#if not os.path.exists(os.path.join(root, check_filetime)):
#    gen_new = True
#else:
#    pickle_time = os.path.getmtime(os.path.join(root, check_filetime))
#    py_time = os.path.getmtime(__file__)
#    gen_new = py_time > pickle_time


#if gen_new:
if True:
    program_all = '0000'
    program_0 = '0001'
    led_all = '0010'
    led_0 = '0100'
    led_1 = '0101'
    led_2 = '0110'
    led_3 = '0111'
    tdma_0 = '0011'
    stim_on = '1001'
    stim_off = '1000'

    sync = '0101100101' # 10b
    puf = '0101101001011010' # 16b
    wrong_puf = '1101101001011010' # 16b
    puf_chip = [
            '1100001100001010'[::-1] # Chip1 0xC30A
            ]
    # Chip1 = b: 1100001100001010 h: C30A

    d4 = [""] * 16;
    for i in range(16):
        d4[i] = "{:04b}".format(i)
    d4_all = ""
    for s in d4:
        d4_all = d4_all + s;
        
    d3 = [""] * 8;
    for i in range(8):
        d3[i] = "{:03b}".format(i)
    d3_all = "" # len(d3_all) = 3*8 = 24
    for s in d3:
        d3_all = d3_all + s;
    d3_100slot = d3[3] + d3[4] + d3_all * 12 + d3[0] + d3[1];
    d3_40slot = d3_100slot[:3*40]
    d3_625slot = d3_100slot * 6 + d3_100slot[:25*3]
    d3_1024slot = d3[2] + d3_100slot * 10 + d3_100slot[:23*3]

    slot = [""] * 1024;
    for i in range(1024):
        slot[i] = "{:010b}".format(i)

    slot_dec = 10

    d3_40slot_d10 = [""]*8
    for stim_q in range(8):
        d3_40slot_d10[stim_q] = d3_40slot[:3*slot_dec] + '{:03b}'.format(stim_q) + d3_40slot[3*slot_dec+3:]

    d3_mon_cap = []
    for mon_cap in range(8):
        d3_mon_cap.append('{:03b}'.format(mon_cap))

    n_pulse = 200
    manc_enc_str_moncap_stimq = []

    ### Fake Pico setting
    pico_port = '/dev/serial0' # '/dev/ttyACM0'
    baud = 921600 # 115201
    pico = pico(pico_port, baud, 'gen_inst')
    log = pico.log
    
    for mon_cap in range(8):
        manc_enc_str_stimq = []
        for stim_q in range(8):
            bits = ""
            bits = bits + '1'*100
            #bits = bits + sync + program_0 + puf_chip[0] + slot[10]
            bits = bits + sync + program_all + slot[10] + d3_mon_cap[mon_cap]
            bits = bits + '1'*10
            bits = bits + sync + tdma_0 + d3_40slot_d10[stim_q] + sync # stim_q = 4
            bits = bits + sync + stim_on
            bits = bits + '1'*256*n_pulse
            bits = bits + sync + stim_off
            bits = bits + '1'*10

            bits_arr = np.array([int(bit) for bit in list(bits)])
            one_mask = bits_arr == 1
            zero_mask = bits_arr == 0
            d0 = one_mask*0 +  zero_mask*1
            d1 = one_mask*1 +  zero_mask*0
            manc_enc = np.vstack([d0, d1]).T.reshape(-1)
            #manc_enc_str_stimq.append(''.join([str(bit) for bit in manc_enc]))

            manc_enc_str= ''.join([str(bit) for bit in manc_enc])
            pico.stream_str_to_byte(manc_enc_str)
            with open(os.path.join(root, 'moncap{}_stimq{}.pickle'.format(mon_cap, stim_q)), 'wb') as fp:
                pickle.dump(pico.stream_byte, fp)
    #    manc_enc_str_moncap_stimq.append(manc_enc_str_stimq)


    #manc_enc_str_moncap_stimq_byte = []
    #for mon_cap in range(8):
    #    manc_enc_str_stimq_byte = []
    #    for stim_q in range(8):
    #        pico.stream_str_to_byte(manc_enc_str_moncap_stimq[mon_cap][stim_q])
    #        manc_enc_str_stimq_byte.append(pico.stream_byte)
    #    manc_enc_str_moncap_stimq_byte.append(manc_enc_str_stimq_byte)

    #d = {}
    ##d['manc_enc_str'] = manc_enc_str
    ##d['manc_enc_str_moncap_stimq_byte'] = manc_enc_str_moncap_stimq_byte

    #with open(os.path.join(root, pickle_stimote_inst), 'wb') as fp:
    #    pickle.dump(d, fp)

#else:
#    with open(os.path.join(root, pickle_stimote_inst), 'rb') as fp:
#        d = pickle.load(fp)
#        #manc_enc_str = d['manc_enc_str']
#        manc_enc_str_moncap_stimq_byte = d['manc_enc_str_moncap_stimq_byte']


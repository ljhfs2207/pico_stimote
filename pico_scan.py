# Author: Jungho Lee
# Description: Scan chain hanlder using Raspberry Pi Pico
# History:
#   230103: initial version mixed from FT2232H version and Pico class 

import os
import sys
import serial
import time
import csv
import tkinter as tk

class pico_scan():
    ### Parameters
    csvname = 'scan.csv'
    command_scan_read = 'scan_read'
    command_scan_write = 'scan_write'

    ### Generic methods
    def __init__(self, port, baud, comment='scan'):
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
        self._serial.write(bytes((command+'\n').encode('utf-8')))

    def read_line(self):
        while self._serial.inWaiting() == 0:
            pass
        try:
            return self._serial.readline().rstrip().decode('utf-8')
        except UnicodeDecodeError:
            return self._serial.readline().rstrip()

    def write_raw(self, command):
        self._serial.write(command)
    def read_raw(self):
        while self._serial.inWaiting() == 0:
            pass
        return self._serial.read_all()

    ### DB handler
    def scan_load_db(self, csvname=csvname):
        self.csvname = csvname
        with open(csvname, 'r') as fp:
            reader = csv.DictReader(fp)
            self.csvfields = reader.fieldnames
            self.db = list(reader)
            self.num_scan = 0
            for item in self.db:
                self.num_scan += int(item['Width'])
        # {'No': '7', 'Name': 'TIB_AMBIENT_EXT', 'Direction': 'IN', 'Width': '2', 
        # 'Write': '2', 'Read': '3', 'Default': '1'}
    def scan_print_db(self):
        formatter = '{:3}{:20}{:5}{:7}{:7}{:7}'
        line = '-'*(3+20+5+5+7+7)
        header = formatter.format('No', 'Name', 'Dir', 'Width','Write', 'Read')
        print(header)
        print(line)
        for item in self.db:
            print(formatter.format(item['No'], item['Name'], item['Direction'], 
                item['Width'], item['Write'], item['Read'] ))
    def scan_change_db(self, key, value_str):
        for item in self.db:
            if item['Name'] == key:
                w = int(item['Width'])
                v = int(value_str)
                if (v < 2**w) and (v >= 0):
                    item['Write'] = str(value_str)
                    self.log.info('scan_change_db - target value changed.')
                else:
                    self.log.error('scan_change_db -  not allowed value.')
    def scan_save_db(self):
        with open(self.csvname, 'w', newline='\n') as fp:
            writer = csv.DictWriter(fp, self.csvfields)
            writer.writeheader()
            writer.writerows(self.db)
        self.log.info('save_db - Saved DB to {}'.format(self.csvname))

    ### Communication with chip
    def scan_read(self):
        '''Read db and change db'''
        # Send command
        self.write_line(self.command_scan_read)
        self.write_line('{}'.format(self.num_scan))
        read_result = self.read_line()
        self.log.info('scan_read - write = {}'.format(self.num_scan))
        self.log.info('scan_read - echoed = {}'.format(read_result))
        # Process data
        for item in self.db:
            width = int(item['Width'])
            item['Read'] = '{}'.format(int(read_result[:width], 2))
            read_result = read_result[width:]
    def scan_write(self):
        '''Write db to scan chain'''
        # Prepare data
        write_str = ''
        for item in self.db:
            formatter = '{:0' + item['Width'] + 'b}'
            write_str += formatter.format(int(item['Write']))
        # Send command
        self.write_line(self.command_scan_write)
        self.write_line('{}'.format(self.num_scan))
        self.write_line(write_str)
        write_result = self.read_line()
        self.log.info('scan_write - write = {} {}'.format(self.num_scan, write_str))
        self.log.info('scan_write - echoed = {}'.format(write_result))

    ### GUI
    def gui(self):
        # Parameter setting
        param_name = {'font': 'Arial 12', 'width': 20, 'anchor': 'w'}
        param_width = {'font': 'Arial 12', 'width': 5, 'anchor': 'w'} 
        param_write = {'font': 'Arial 12', 'width': 5,}
        param_read = {'font': 'Arial 12', 'width': 7, 'anchor': 'w'}
        param_button = {'font':'Arial 12', 'width':15, 'bg':'white', 'activebackground':'yellow'}

        # Initialization
        win = tk.Tk()
        win.title("Scan Chain")
        row_offset = 0
        #win.geometry('300x200') # w x h

        # Header
        tk.Label(win, text='Name', bg='grey', **param_name).grid(row=row_offset, column=0)
        tk.Label(win, text='Width', bg='grey', **param_width).grid(row=row_offset, column=1)
        tk.Label(win, text='Default', bg='grey', **param_write).grid(row=row_offset, column=2)
        tk.Label(win, text='Write', bg='grey', **param_write).grid(row=row_offset, column=3)
        tk.Label(win, text='Read', bg='grey', **param_read).grid(row=row_offset, column=4)        
        row_offset += 1

        # Main value table
        handle = {}
        for index, item in enumerate(self.db):
            n = item['Name']
            if item['Direction'] == 'IN':
                bg = 'snow'
            elif item['Direction'] == 'OUT':
                bg = 'bisque'
            handle[(n, 'name')] = tk.Label(win, text=item['Name'], **param_name, bg=bg)
            handle[(n, 'name')].grid(row=row_offset+index, column=0)

            handle[(n, 'width')] = tk.Label(win, text=item['Width'], **param_width, bg=bg)
            handle[(n, 'width')].grid(row=row_offset+index, column=1)

            handle[(n, 'def_lbl')] = tk.Label(win, text=item['Default'], **param_write, bg=bg)
            handle[(n, 'def_lbl')].grid(row=row_offset+index, column=2)

            handle[(n, 'write_str')] = tk.StringVar()
            handle[(n, 'write_str')].set(item['Write'])
            handle[(n, 'write_etr')] = tk.Entry(win, textvariable=handle[(n, 'write_str')], **param_write, bg=bg)
            handle[(n, 'write_etr')].grid(row=row_offset+index, column=3)

            handle[(n, 'read_str')] = tk.StringVar()
            handle[(n, 'read_str')].set(item['Read'])
            handle[(n, 'read_lbl')] = tk.Label(win, textvariable=handle[(n, 'read_str')], **param_read, bg=bg)
            handle[(n, 'read_lbl')].grid(row=row_offset+index, column=4)            
        row_offset += index+1
        
        # Callbacks
        def write_button():
            for item in self.db:
                val = handle[(item['Name'], 'write_str')].get()
                if val is not item['Write']:
                    self.log.info('gui - {} changed from {} to {}.'.format(item['Name'], item['Write'], val))
                    self.scan_change_db(item['Name'], val)
            self.log.info('gui - New values are WRITTEN to the scan chain.')
            self.scan_write()

        def read_button():
            self.scan_read()
            for item in self.db:
                handle[(item['Name'], 'read_str')].set(item['Read'])
            self.log.info('gui - New values are READ from the scan chain.')

        # Buttons
        tk.Button(win, text='Write', **param_button, command=write_button).grid(row=row_offset)
        row_offset += 1
        tk.Button(win, text='Read', **param_button, command=read_button).grid(row=row_offset)
        row_offset += 1
        tk.Button(win, text='Save DB to CSV', **param_button, command=self.scan_save_db).grid(row=row_offset)
        row_offset += 1
        tk.Button(win, text='Close', **param_button, command=lambda:[win.destroy()]).grid(row=row_offset)
        row_offset += 1

        win.mainloop()


if __name__=='__main__':
    pico_port = '/dev/serial0'
    baud = 921600
    pico = pico_scan(pico_port, baud, 'test')
    pico.scan_load_db()
    #print(pico.db)
    #pico.scan_print_db()
    #print(pico.num_scan)

    #pico.scan_read()
    #pico.scan_write()

    pico.gui()






from pico_scan import pico_scan
pico_port = '/dev/serial0'
baud = 921600
pico = pico_scan(pico_port, baud, 'test')
pico.scan_load_db()
print(pico.db)
pico.scan_print_db()
print(pico.num_scan)
pico.scan_read()
pico.scan_write()


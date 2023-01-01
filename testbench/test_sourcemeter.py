from pymeasure.instruments.keithley import Keithley2400
#log = logger('_chip_program_light')
#log.info('vl={:.2f}, vh={:.2f}'.format(vl, vh))

### Connect Keithley2400
sourcemeter = Keithley2400("GPIB::15")
sourcemeter.apply_current()
sourcemeter.measure_voltage()
sourcemeter.compliance_voltage = 10
sourcemeter.source_current = 0 # V, turn off
sourcemeter.enable_source()
print(sourcemeter.voltage)
#sourcemeter.ramp_to_current(5e-3)
#log.info('sourcemeter succesfully set up - isrc=0')

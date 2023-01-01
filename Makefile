

#all:
#	cd build && cmake .. && make

# ~/Setting/.bash_colors
Color_Off=\033[0m
Red=\033[0;31m

all:

%.uf2:
	@make build_dir
	@make build_cmake
	@cd build && make -j4 $*
	@echo "${Red}Load program to PICO${Color_Off}"
	pico_load build/$*
# pico_bootsel_mode = PI gpio27=PICO BOOTSEL gpio22=RUN

build_dir: build
	@mkdir -p build

build_cmake: build/Makefile
	cd build && cmake ..

gpib:
	sudo gpib_config
	sudo ldconfig
	sudo python3 testbench/test_gpib.py

reboot:
	@pico_bootsel_mode
	@sleep 1
	@sudo picotool reboot

clean:
	rm -rf build/*

microbot: FORCE
	raspi-gpio set 4 ip pd
	sudo python3 testbench/221117_microbot_light_program.py

isc: FORCE
	sudo python3 testbench/221117_microbot_isc.py

refh_powerdown: FORCE
	sudo python3 testbench/221117_dac_refh_powerdown.py

pico_board_dac: FORCE
	sudo python3 testbench/221201_pico_board_dac.py

dac_characteristic: FORCE
	sudo python3 testbench/221206_dac_characterization.py

FORCE: ;

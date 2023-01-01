# Functions

## Serial communication protocol
* `f`: Set freuqency. Followed by `float` frequency number. Prints out a message if succeed.
   
    * scanf `freq`, calculate divider and set clock divider with `pio_sm_set_clkdiv`
    * Temporarily disable and enable the state machine while setting divider
    * Echo back `freq` to inform that the function worked
    * Example: `command = f10000\n` and `echo = 10000\n` sets the state machine clock to 10 kHz
    
* `v`: Set the word value for DAC modulation low and high.
    * `v` followed by 6 bytes, no CR/LF
    * According DAC command bits are stored at word [23:8] at the MSB side because we are shifting out from the right.
    * PC sends those 24 bits in 3 consecutive bytes, we add them to initialized `uint` variable. For example for `word_0`,
        ```c
        // receive word_0
        dac_command = 0;
        command = uart_getc(uart0);
        dac_command += (uint)command << 24u;
        command = uart_getc(uart0);
        dac_command += (uint)command << 16u;
        command = uart_getc(uart0);
        dac_command += (uint)command << 8u;
        word_0 = dac_command;
        ```
    * Example: `command = b'v\x12\x00\x00\x12\xff\xf0'` and `echo = '120000 12fff0\n'`

* `d`: Send a single dac command
    * No CR/LF
    * Example: `b'd\x12\x80\x00'` and `x'128000'`

* `s`: Control dac according to the bit value 0/1 in received character
    * First read all stdin until '\n' and save it in char list `bitstream`
    * Now `bitstream` has the size of 131072 = 128 kB, noting that RP2040 has 264 kB SRAM
    * When the block stars stream, send `CORE1_MANCHESTER_IDLE_FALSE` to core1 FIFO to stop sending idle 1s for manchester encoding
    * Repeatedly take 1 byte and mask its bit value from the LSB and send `word_0` or `word_1` to the state machine FIFO
    * Stream ends when it meats null character ('\0')
    * When it succesfully ends, it echo the number of processed bytes, send `CORE1_MANCHESTER_IDLE_TRUE`
    * Could be interrupted using GPIO pin -> not tested yet
    * Example: command `s\xaa\xaa....\xaa\n` echo `3\n`

* `i`: Control the idle playing from core1
    * `ioff\n` to turn off the idle play, `ioff\n` to turn on the idle play
    
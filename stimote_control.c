#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h" // stdio, time, gpio, uart
#include "pico/multicore.h"
#include "hardware/clocks.h"
#include "hardware/sync.h"
#include "hardware/pio.h"
// Our assembled program:
#include "dac121s101.pio.h"
#include "stream_monitor.pio.h"

//const uint pin_test = 3;
//PICO_DEFAULT_LED_PIN

#define CORE1_MANCHESTER_IDLE_FALSE 0
#define CORE1_MANCHESTER_IDLE_TRUE 1
#define CORE1_UPDATE_VLEVEL 2

void measure_freqs(void){
    uint f_pll_sys = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_PLL_SYS_CLKSRC_PRIMARY);
    uint f_pll_usb = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_PLL_USB_CLKSRC_PRIMARY);
    uint f_rosc = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_ROSC_CLKSRC);
    uint f_clk_sys = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_SYS);
    uint f_clk_peri = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_PERI);
    uint f_clk_usb = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_USB);
    uint f_clk_adc = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_ADC);
    uint f_clk_rtc = frequency_count_khz(CLOCKS_FC0_SRC_VALUE_CLK_RTC);

    printf("pll_sys = %dkHz\n", f_pll_sys);
    printf("pll_usb = %dkHz\n", f_pll_usb);
    printf("rosc = %dkHz\n", f_rosc);
    printf("clk_sys = %dkHz\n", f_clk_sys);
    printf("clk_peri = %dkHz\n", f_clk_peri);
    printf("clk_usb = %dkHz\n", f_clk_usb);
    printf("clk_adc = %dkHz\n", f_clk_adc);
    printf("clk_rtc = %dkHz\n", f_clk_rtc); 
}

void core1_entry() {
    PIO pio = pio0;
    uint sm = (uint) multicore_fifo_pop_blocking();
    uint word_0, word_1;
    uint from_core0 = 0;
    uint status = CORE1_MANCHESTER_IDLE_FALSE;
    while(true){
        if(multicore_fifo_rvalid()){
            from_core0 = multicore_fifo_pop_blocking();
            if (from_core0 == CORE1_MANCHESTER_IDLE_TRUE) 
                status = CORE1_MANCHESTER_IDLE_TRUE;
            else if (from_core0 == CORE1_MANCHESTER_IDLE_FALSE) 
                status = CORE1_MANCHESTER_IDLE_FALSE;
            else if (from_core0 == CORE1_UPDATE_VLEVEL){
                word_0 = multicore_fifo_pop_blocking();
                word_1 = multicore_fifo_pop_blocking();
            }
        }
        if (status == CORE1_MANCHESTER_IDLE_TRUE){
            pio_sm_put_blocking(pio, sm, word_0);
            pio_sm_put_blocking(pio, sm, word_1);
        }
    }
}


int main() {
    /* GPIO Pin map
    00 UART TX
    01 UART RX (input)
    02 DAC SYNCB
    03 DAC SCLK
    04 DAC DIN
    05 DAC LDAC
    06 DAC ENB (H)
    07 DAC RSTS
    08 DAC RSTB (H)
    09 INTERRUPT (input)
    10 STREAM_EN
    11 STREAM_MONITOR
    */
    int i;
    stdio_init_all();

    // Initialize state machine
    PIO pio = pio0; // pio0, pio1
    uint offset = pio_add_program(pio, &dac121s101_program);
    uint sm = pio_claim_unused_sm(pio, true);
    control_program_init(pio, sm, offset);
    // another state machien for stream_monitor
    uint offset_monitor = pio_add_program(pio, &stream_monitor_program);
    uint sm_monitor = pio_claim_unused_sm(pio, true);
    stream_monitor_program_init(pio, sm_monitor, offset_monitor);

    // Initialize core1 - multicore for idle state
    multicore_launch_core1(core1_entry);
    multicore_fifo_push_blocking(sm);

    // UART setting - GP0=TX, GP1=RX by default
    int baud = 921600;
    int baud_result;
    baud_result = uart_init(uart0, baud); 

    /* GPIO setting for interupting stream */
    // output pins for DAC control
    for (i=5; i<9; i++){
        gpio_init(i);
        gpio_set_dir(i, GPIO_OUT);
    }
    gpio_put(5, 0);
    gpio_put(6, 0); // always enabled
    gpio_put(7, 0);
    gpio_put(8, 1);

    // interrupt pin while streaming -- not completed function
    int gpio_pin_interrupt = 9;
    gpio_init(gpio_pin_interrupt);
    gpio_set_dir(gpio_pin_interrupt, GPIO_IN);
    gpio_pull_down(gpio_pin_interrupt);

    // output pin for notifying stream enabled
    int gpio_pin_stream_en = 10;
    gpio_init(gpio_pin_stream_en);
    gpio_set_dir(gpio_pin_stream_en, GPIO_OUT);

    // Variables for appropriate command execution
    char command;
    char bitstream[131072]; // 128kB among rp2040=264kB 
    char idle[4]; // "on" or "off"
    float freq, div;
    uint word_0, word_1; // low, high
    uint dac_command;
    int byte_count;
    uint current_idle_state = CORE1_MANCHESTER_IDLE_FALSE;

    while (true) {
        if(uart_is_readable(uart0)){
            command = uart_getc(uart0);
            if(command == 'f'){ // set state machine frequency
                scanf("%f", &freq);
                // calculate divider value (float)
                div = clock_get_hz(clk_sys) / freq;
                // stop pio, set div, resume pio
                pio_sm_set_enabled(pio, sm, false);
                pio_sm_set_enabled(pio, sm_monitor, false);
                pio_sm_set_clkdiv(pio, sm, div);
                pio_sm_set_clkdiv(pio, sm_monitor, div);
                pio_sm_set_enabled(pio, sm, true);
                pio_sm_set_enabled(pio, sm_monitor, true);
                // print to host
                printf("%f\n", freq);
            }
            else if (command == 'v'){ // set dac seqeuence for low / high levels
                // receive word_0
                dac_command = 0;
                command = uart_getc(uart0);
                dac_command += (uint)command << 24u;
                command = uart_getc(uart0);
                dac_command += (uint)command << 16u;
                word_0 = dac_command;
                // receive word_1
                dac_command = 0;
                command = uart_getc(uart0);
                dac_command += (uint)command << 24u;
                command = uart_getc(uart0);
                dac_command += (uint)command << 16u;
                word_1 = dac_command;
                // share with core 1
                multicore_fifo_push_blocking(CORE1_UPDATE_VLEVEL);
                multicore_fifo_push_blocking(word_0);
                multicore_fifo_push_blocking(word_1);
                // echo
                printf("%x %x\n", word_0 >> 16u, word_1 >> 16u);
            }
            else if (command == 'd'){ // single dac command
                dac_command = 0;
                command = uart_getc(uart0);
                dac_command += (uint)command << 24u;
                command = uart_getc(uart0);
                dac_command += (uint)command << 16u;
                pio_sm_put_blocking(pio, sm, dac_command);
                printf("x'%04x'\n", dac_command >> 16u);
            }
            else if (command == 's'){ // stream data
                scanf("%s", bitstream);
                // disable should be done "after" scanf because it takes some time
                multicore_fifo_push_blocking(CORE1_MANCHESTER_IDLE_FALSE); 
                byte_count = 0;
                gpio_put(gpio_pin_stream_en, 1);
                while (true){
                    //command = uart_getc(uart0);
                    command = bitstream[byte_count];
                    if(command == '\0'){ // normal termination
                        multicore_fifo_push_blocking(current_idle_state);
                        printf("%d\n", byte_count);
                        gpio_put(gpio_pin_stream_en, 0);
                        break; 
                    }
                    else if (gpio_get(gpio_pin_interrupt)){ // interrupted termination
                        printf("interrupted\n");
                        stdio_flush();
                        break;
                    }
                    else { // normal loop
                        for(i=0; i < 8; i++)
                            if ((command >> i) & 1) {
                                pio_sm_put_blocking(pio, sm, word_1);
                                pio_sm_put_blocking(pio, sm_monitor, 1);
                            }
                            else {
                                pio_sm_put_blocking(pio, sm, word_0);
                                pio_sm_put_blocking(pio, sm_monitor, 0);
                            }
                        byte_count++;
                    }
                }
            }
            else if (command == 'i'){
                scanf("%s", idle);
                if (strcmp(idle, "off")==0)
                    current_idle_state = CORE1_MANCHESTER_IDLE_FALSE;
                else if (strcmp(idle, "on")==0)
                    current_idle_state = CORE1_MANCHESTER_IDLE_TRUE;
                multicore_fifo_push_blocking(current_idle_state);
                printf("%s\n", idle);
            }
        }
        //else if(
    }
    return 0;
}

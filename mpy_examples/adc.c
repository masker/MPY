

#include <msp430.h>
#include "msp430g2452.h"
#include "c:\mpy\mpy_editor\mpy\mpy_functions.c"

int v7 ; 

                        
void main (void) { 

    WDTCTL = WDTPW + WDTHOLD; // Stop WDT
    BCSCTL1 = CALBC1_1MHZ;    // Set range
    DCOCTL  = CALDCO_1MHZ;    // SMCLK = DCO = 1MHz

    // set all pins to pulldown inputs
    P1DIR = 0;
    P1REN = 0xFF;
    P1OUT = 0;
    P2DIR = 0;
    P2REN = 0xFF;
    P2OUT = 0;
   



ADC10CTL0 &= ~ ENC ; ADC10CTL0 = ( ( ( ( ADC10SHT_2 | ADC10ON ) | REFON ) | REF2_5V ) | SREF_1 ) ; 
      while ( 1 ) { 
          v7 = adc ( 23 ) ; 
          print_value ( "ADC value on p1_7" , v7 ) ; 
          wait ( 500 ) ; } } 

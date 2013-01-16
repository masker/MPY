// &C:\MPY\mpy_examples\adc.mpy&-1

#include <msp430.h>
#include "msp430g2231.h"
#include "c:\mpy\mpy_editor\mpy\mpy_functions.c"

int v7 ; 
// &C:\MPY\mpy_examples\adc.mpy&18

                        
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
   


ADC10CTL0 &= ~ ENC ; ADC10CTL0 = ( ( ( ( ADC10SHT_2 | ADC10ON ) | REFON ) | REF2_5V ) | SREF_1 ) ; // &C:\MPY\mpy_examples\adc.mpy&12
      while ( 1 ) { // &C:\MPY\mpy_examples\adc.mpy&14
          v7 = adc ( 23 ) ; // &C:\MPY\mpy_examples\adc.mpy&16
          print__mpy__ ( "sds" , "ADC value on pin p1_7" , v7 , "\n" ) ; // &C:\MPY\mpy_examples\adc.mpy&17
          wait ( 500 ) ; } } // &C:\MPY\mpy_examples\adc.mpy&18


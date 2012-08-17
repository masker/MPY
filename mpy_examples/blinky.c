// &C:\MPY\mpy_examples\blinky.mpy&-1

#include <msp430.h>
#include "msp430g2553.h"
#include "c:\mpy\mpy_editor\mpy\mpy_functions.c"



                        
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
   


// &C:\MPY\mpy_examples\blinky.mpy&17
if ( 16 < 32 ) { P1DIR |= ( 1 << ( 16 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 16 & 15 ) ) ; P1REN &= ~ ( 1 << ( 16 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 16 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 16 & 15 ) ) ; P2REN &= ~ ( 1 << ( 16 & 15 ) ) ; } ; // &C:\MPY\mpy_examples\blinky.mpy&11
      while ( 1 ) { // &C:\MPY\mpy_examples\blinky.mpy&14
          if ( 1 ) { if ( 16 < 32 ) { P1OUT |= ( 1 << ( 16 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 16 & 15 ) ) ; } ; } else { if ( 16 < 32 ) { P1OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } ; } ; // &C:\MPY\mpy_examples\blinky.mpy&15
          wait ( 100 ) ; // &C:\MPY\mpy_examples\blinky.mpy&16
          if ( 0 ) { if ( 16 < 32 ) { P1OUT |= ( 1 << ( 16 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 16 & 15 ) ) ; } ; } else { if ( 16 < 32 ) { P1OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } ; } ; // &C:\MPY\mpy_examples\blinky.mpy&17
          wait ( 100 ) ; } } // &C:\MPY\mpy_examples\blinky.mpy&18


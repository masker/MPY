
      
#include <msp430.h>
#include "msp430g2231.h"
#include "C:\MPY\mpy_editor\mpy\mpy_functions.c"

                        
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
   



      
      P1DIR |= BIT0 ; P1SEL &= ~ BIT0 ; P1REN &= ~ BIT0 ; 
      while ( 1 ) { 
          if ( 1 ) { P1OUT |= BIT0 ; } else { P1OUT &= ~ BIT0 ; } ; 
          wait ( 100 ) ; 
          if ( 0 ) { P1OUT |= BIT0 ; } else { P1OUT &= ~ BIT0 ; } ; 
          wait ( 100 ) ; } } 

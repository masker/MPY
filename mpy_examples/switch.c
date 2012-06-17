
      
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
   
int sw ; 


      
      P1DIR |= BIT6 ; P1SEL &= ~ BIT6 ; P1REN &= ~ BIT6 ; 
      P1DIR |= BIT0 ; P1SEL &= ~ BIT0 ; P1REN &= ~ BIT0 ; 
      P1DIR &= ~ BIT3 ; P1REN |= BIT3 ; P1OUT |= BIT3 ; 
      while ( 1 ) { 
          sw = ( ( P1IN & BIT3 ) >> 3 ) ; 
          if ( sw == 1 ) { 
              if ( 1 ) { P1OUT |= BIT6 ; } else { P1OUT &= ~ BIT6 ; } ; 
              wait ( 500 ) ; 
              if ( 0 ) { P1OUT |= BIT6 ; } else { P1OUT &= ~ BIT6 ; } ; 
              wait ( 500 ) ; } else { 
              if ( 1 ) { P1OUT |= BIT0 ; } else { P1OUT &= ~ BIT0 ; } ; 
              wait ( 500 ) ; 
              if ( 0 ) { P1OUT |= BIT0 ; } else { P1OUT &= ~ BIT0 ; } ; 
              wait ( 500 ) ; } } } 

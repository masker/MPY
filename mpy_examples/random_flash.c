
      
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
   
int dly_big ; int dly ; 


      
      P1DIR |= BIT6 ; P1SEL &= ~ BIT6 ; P1REN &= ~ BIT6 ; 
      P1DIR |= BIT0 ; P1SEL &= ~ BIT0 ; P1REN &= ~ BIT0 ; 
      dly_big = 0 ; 
      while ( 1 ) { 
          dly_big = random ( dly_big ) ; 
          dly = ( dly_big / 30 ) ; 
          if ( dly > 0 ) { 
              P1OUT |= BIT6 ; 
              wait ( dly ) ; 
              P1OUT &= ~ BIT6 ; 
              wait ( dly ) ; } else { 
              P1OUT |= BIT0 ; 
              wait ( dly ) ; 
              P1OUT &= ~ BIT0 ; 
              wait ( dly ) ; } } } 


      
#include <msp430.h>
#include "msp430g2231.h"
#include "c:\mpy\mpy_editor\mpy\mpy_functions.c"

int dly_big ; int dly ; 

                        
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
   



      
      if ( 22 < 32 ) { P1DIR |= ( 1 << ( 22 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 22 & 15 ) ) ; P1REN &= ~ ( 1 << ( 22 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 22 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 22 & 15 ) ) ; P2REN &= ~ ( 1 << ( 22 & 15 ) ) ; } ; 
      if ( 16 < 32 ) { P1DIR |= ( 1 << ( 16 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 16 & 15 ) ) ; P1REN &= ~ ( 1 << ( 16 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 16 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 16 & 15 ) ) ; P2REN &= ~ ( 1 << ( 16 & 15 ) ) ; } ; 
      dly_big = 0 ; 
      while ( 1 ) { 
          dly_big = random ( dly_big ) ; 
          dly = ( dly_big / 30 ) ; 
          print_value ( "dly_big=" , dly_big ) ; 
          if ( dly > 0 ) { 
              if ( 22 < 32 ) { P1OUT |= ( 1 << ( 22 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 22 & 15 ) ) ; } ; 
              wait ( dly ) ; 
              if ( 22 < 32 ) { P1OUT &= ~ ( 1 << ( 22 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 22 & 15 ) ) ; } ; 
              wait ( dly ) ; } else { 
              if ( 16 < 32 ) { P1OUT |= ( 1 << ( 16 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 16 & 15 ) ) ; } ; 
              wait ( dly ) ; 
              if ( 16 < 32 ) { P1OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } ; 
              wait ( dly ) ; } } } 

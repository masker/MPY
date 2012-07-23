
      
#include <msp430.h>
#include "msp430g2231.h"
#include "c:\mpy\mpy_editor\mpy\mpy_functions.c"

int last_sw ; int sw ; 

                        
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
      if ( 19 < 32 ) { P1DIR &= ~ ( 1 << ( 19 & 15 ) ) ; P1REN |= ( 1 << ( 19 & 15 ) ) ; P1OUT |= ( 1 << ( 19 & 15 ) ) ; } else { P2DIR &= ~ ( 1 << ( 19 & 15 ) ) ; P2REN |= ( 1 << ( 19 & 15 ) ) ; P2OUT |= ( 1 << ( 19 & 15 ) ) ; } ; 
      last_sw = 0 ; 
      while ( 1 ) { 
          if ( 22 < 32 ) { P1OUT |= ( 1 << ( 22 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 22 & 15 ) ) ; } ; 
          if ( 16 < 32 ) { P1OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } ; 
          wait ( 50 ) ; 
          if ( 22 < 32 ) { P1OUT &= ~ ( 1 << ( 22 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 22 & 15 ) ) ; } ; 
          if ( 16 < 32 ) { P1OUT |= ( 1 << ( 16 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 16 & 15 ) ) ; } ; 
          wait ( 50 ) ; 
          sw = ( ( ( ( 19 & 16 ) >> 4 ) & ( P1IN >> ( 19 & 15 ) ) ) | ( ( ( 19 & 32 ) >> 5 ) & ( P2IN >> ( 19 & 15 ) ) ) ) ; 
          if ( sw != last_sw ) { 
              print_value ( "The switch is :" , sw ) ; } 
          last_sw = sw ; } } 

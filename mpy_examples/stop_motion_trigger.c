
      
#include <msp430.h>
#include "msp430g2452.h"
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
   
int delay ; int scale ; 


      
      if ( 22 < 32 ) { P1DIR |= ( 1 << ( 22 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 22 & 15 ) ) ; P1REN &= ~ ( 1 << ( 22 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 22 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 22 & 15 ) ) ; P2REN &= ~ ( 1 << ( 22 & 15 ) ) ; } ; 
      if ( 21 < 32 ) { P1DIR |= ( 1 << ( 21 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 21 & 15 ) ) ; P1REN &= ~ ( 1 << ( 21 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 21 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 21 & 15 ) ) ; P2REN &= ~ ( 1 << ( 21 & 15 ) ) ; } ; 
      if ( 32 < 32 ) { P1DIR &= ~ ( 1 << ( 32 & 15 ) ) ; P1REN |= ( 1 << ( 32 & 15 ) ) ; P1OUT &= ~ ( 1 << ( 32 & 15 ) ) ; } else { P2DIR &= ~ ( 1 << ( 32 & 15 ) ) ; P2REN |= ( 1 << ( 32 & 15 ) ) ; P2OUT &= ~ ( 1 << ( 32 & 15 ) ) ; } ; 
      if ( 33 < 32 ) { P1DIR &= ~ ( 1 << ( 33 & 15 ) ) ; P1REN |= ( 1 << ( 33 & 15 ) ) ; P1OUT &= ~ ( 1 << ( 33 & 15 ) ) ; } else { P2DIR &= ~ ( 1 << ( 33 & 15 ) ) ; P2REN |= ( 1 << ( 33 & 15 ) ) ; P2OUT &= ~ ( 1 << ( 33 & 15 ) ) ; } ; 
      if ( 34 < 32 ) { P1DIR &= ~ ( 1 << ( 34 & 15 ) ) ; P1REN |= ( 1 << ( 34 & 15 ) ) ; P1OUT &= ~ ( 1 << ( 34 & 15 ) ) ; } else { P2DIR &= ~ ( 1 << ( 34 & 15 ) ) ; P2REN |= ( 1 << ( 34 & 15 ) ) ; P2OUT &= ~ ( 1 << ( 34 & 15 ) ) ; } ; 
      if ( 35 < 32 ) { P1DIR &= ~ ( 1 << ( 35 & 15 ) ) ; P1REN |= ( 1 << ( 35 & 15 ) ) ; P1OUT &= ~ ( 1 << ( 35 & 15 ) ) ; } else { P2DIR &= ~ ( 1 << ( 35 & 15 ) ) ; P2REN |= ( 1 << ( 35 & 15 ) ) ; P2OUT &= ~ ( 1 << ( 35 & 15 ) ) ; } ; 
      print ( "\n P2OUT = " ) ; 
      print_hex ( P2OUT ) ; 
      print ( "     P2DIR = " ) ; 
      print_hex ( P2DIR ) ; 
      print ( "\n P2REN = " ) ; 
      print_hex ( P2REN ) ; 
      print ( "     P2IN = " ) ; 
      print_hex ( P2IN ) ; 
      print ( "\n P2SEL = " ) ; 
      print_hex ( P2SEL ) ; 
      print ( "     P2SEL2 = " ) ; 
      print_hex ( P2SEL2 ) ; 
      print ( "\n" ) ; 
      scale = 1000 ; 
      while ( 1 ) { 
          delay = ( 1700 + ( scale * ( P2IN & 31 ) ) ) ; 
          if ( 22 < 32 ) { P1OUT |= ( 1 << ( 22 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 22 & 15 ) ) ; } ; 
          if ( 21 < 32 ) { P1OUT |= ( 1 << ( 21 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 21 & 15 ) ) ; } ; 
          wait ( 1300 ) ; 
          if ( 22 < 32 ) { P1OUT &= ~ ( 1 << ( 22 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 22 & 15 ) ) ; } ; 
          if ( 21 < 32 ) { P1OUT &= ~ ( 1 << ( 21 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 21 & 15 ) ) ; } ; 
          wait ( delay ) ; } } 

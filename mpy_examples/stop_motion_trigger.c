
      
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


      
      P1DIR |= BIT6 ; P1SEL &= ~ BIT6 ; P1REN &= ~ BIT6 ; 
      P1DIR |= BIT5 ; P1SEL &= ~ BIT5 ; P1REN &= ~ BIT5 ; 
      P2DIR &= ~ BIT0 ; P2REN |= BIT0 ; P2OUT &= ~ BIT0 ; 
      P2DIR &= ~ BIT1 ; P2REN |= BIT1 ; P2OUT &= ~ BIT1 ; 
      P2DIR &= ~ BIT2 ; P2REN |= BIT2 ; P2OUT &= ~ BIT2 ; 
      P2DIR &= ~ BIT3 ; P2REN |= BIT3 ; P2OUT &= ~ BIT3 ; 
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
          P1OUT |= BIT6 ; 
          P1OUT |= BIT5 ; 
          wait ( 1300 ) ; 
          P1OUT &= ~ BIT6 ; 
          P1OUT &= ~ BIT5 ; 
          wait ( delay ) ; } } 

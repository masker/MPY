
      
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
   
int i ; int r ; 


      
      P1DIR |= BIT6 ; P1SEL &= ~ BIT6 ; P1REN &= ~ BIT6 ; 
      P1DIR |= BIT0 ; P1SEL &= ~ BIT0 ; P1REN &= ~ BIT0 ; 
      P1DIR &= ~ BIT3 ; P1REN |= BIT3 ; P1OUT |= BIT3 ; 
      P1DIR |= BIT2 ; P1SEL |= BIT2 ; P1REN &= ~ BIT2 ; 
      TA0CCR1 = 1000 ; 
      TA0CCR0 = 10000 ; 
      P1OUT |= BIT6 ; wait ( 100 ) ; P1OUT &= ~ BIT6 ; wait ( 100 ) ; 
      for ( i = 0 ; i < 10 ; i = i + 1 ) { 
          P1OUT |= BIT0 ; wait ( 100 ) ; P1OUT &= ~ BIT0 ; wait ( 100 ) ; } 
      while ( 1 ) { 
          r = random ( r ) ; 
          print_value ( "delay =" , r ) ; 
          wait ( ( r / 8 ) ) ; 
          if ( ( ( P1IN & BIT3 ) >> 3 ) == 1 ) { 
              if ( r > 0 ) { 
                  P1OUT |= BIT6 ; wait ( 100 ) ; P1OUT &= ~ BIT6 ; wait ( 100 ) ; } else { 
                  P1OUT |= BIT0 ; wait ( 100 ) ; P1OUT &= ~ BIT0 ; wait ( 100 ) ; } 
              wait ( 200 ) ; 
              if ( ( ( P1IN & BIT3 ) >> 3 ) == 0 ) { 
                  wait ( 1000 ) ; 
                  for ( i = 0 ; i < 10 ; i = i + 1 ) { 
                      P1OUT |= BIT6 ; wait ( 100 ) ; P1OUT &= ~ BIT6 ; wait ( 100 ) ; 
                      P1OUT |= BIT0 ; wait ( 100 ) ; P1OUT &= ~ BIT0 ; wait ( 100 ) ; } } else { 
                  wait ( 1000 ) ; 
                  for ( i = 0 ; i < 3 ; i = i + 1 ) { 
                      P1OUT |= BIT0 ; wait ( 100 ) ; P1OUT &= ~ BIT0 ; wait ( 100 ) ; } } 
              wait ( 1000 ) ; } } } 


      
#include <msp430.h>
#include "msp430g2553.h"
#include "C:\Python27\MPY\mpy\mpy\mpy_functions.c"

                        
void main (void) { 

    WDTCTL = WDTPW + WDTHOLD; // Stop WDT
    BCSCTL1 = CALBC1_1MHZ;    // Set range
    DCOCTL  = CALDCO_1MHZ;    // SMCLK = DCO = 1MHz
   
int last_sw ; int sw ; 


      
      P1DIR |= BIT6 ; P1SEL &= ~ BIT6 ; P1REN &= ~ BIT6 ; 
      P1DIR |= BIT0 ; P1SEL &= ~ BIT0 ; P1REN &= ~ BIT0 ; 
      P1DIR &= ~ BIT3 ; P1REN |= BIT3 ; P1OUT |= BIT3 ; P1SEL &= ~ BIT3 ; 
      last_sw = 0 ; 
      while ( 1 ) { 
          P1OUT |= BIT6 ; 
          P1OUT &= ~ BIT0 ; 
          wait ( 50 ) ; 
          P1OUT &= ~ BIT6 ; 
          P1OUT |= BIT0 ; 
          wait ( 50 ) ; 
          sw = ( ( P1IN & BIT3 ) >> 3 ) ; 
          if ( sw != last_sw ) { 
              print_value ( "The switch is :" , sw ) ; } 
          last_sw = sw ; } } 

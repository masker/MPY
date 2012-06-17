
      
#include <msp430.h>
#include "msp430g2553.h"
#include "C:\Python27\MPY\mpy\mpy\mpy_functions.c"

                        
void main (void) { 

    WDTCTL = WDTPW + WDTHOLD; // Stop WDT
    BCSCTL1 = CALBC1_1MHZ;    // Set range
    DCOCTL  = CALDCO_1MHZ;    // SMCLK = DCO = 1MHz
   
int count ; 


      
      P1DIR |= BIT6 ; P1SEL &= ~ BIT6 ; P1REN &= ~ BIT6 ; 
      P1DIR |= BIT0 ; P1SEL &= ~ BIT0 ; P1REN &= ~ BIT0 ; 
      P1OUT |= BIT6 ; 
      wait ( 1000 ) ; 
      P1OUT &= ~ BIT6 ; 
      wait ( 1000 ) ; 
      P1OUT |= BIT0 ; 
      wait ( 1000 ) ; 
      P1OUT &= ~ BIT0 ; 
      print_string ( "LP started, green led flash\n" ) ; 
      count = 0 ; 
      while ( 1 ) { 
          wait ( 500 ) ; 
          print_value ( "mikey : " , count ) ; 
          count += 1 ; } } 

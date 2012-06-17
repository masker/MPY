
      
#include <msp430.h>
#include "msp430g2553.h"
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
   



      
      TA0CTL = ( TASSEL_2 + MC_1 ) ; TA0CCTL1 = OUTMOD_7 ; TA0CCTL2 = OUTMOD_7 ; TA0CCR0 = 20000 ; TA1CTL = ( TASSEL_2 + MC_1 ) ; TA1CCTL1 = OUTMOD_7 ; TA1CCTL2 = OUTMOD_7 ; TA1CCR0 = 20000 ; 
      P1DIR |= BIT2 ; P1SEL |= BIT2 ; P1REN &= ~ BIT2 ; 
      P1DIR |= BIT6 ; P1SEL |= BIT6 ; P1REN &= ~ BIT6 ; 
      P2DIR |= BIT1 ; P2SEL |= BIT1 ; P2REN &= ~ BIT1 ; 
      P2DIR |= BIT2 ; P2SEL |= BIT2 ; P2REN &= ~ BIT2 ; 
      P2DIR |= BIT4 ; P2SEL |= BIT4 ; P2REN &= ~ BIT4 ; 
      P2DIR |= BIT5 ; P2SEL |= BIT5 ; P2REN &= ~ BIT5 ; 
      TA0CCR1 = 1000 ; 
      TA1CCR1 = 2000 ; 
      TA1CCR2 = 3000 ; 
      halt ( ) ; } 

// &C:\MPY\mpy_examples\input_switch.mpy&-1

#include <msp430.h>
#include "msp430g2231.h"
#include "c:\mpy\mpy_editor\mpy\mpy_functions.c"

int last_sw ; int sw ; 
// &C:\MPY\mpy_examples\input_switch.mpy&29

                        
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
   


if ( 22 < 32 ) { P1DIR |= ( 1 << ( 22 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 22 & 15 ) ) ; P1REN &= ~ ( 1 << ( 22 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 22 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 22 & 15 ) ) ; P2REN &= ~ ( 1 << ( 22 & 15 ) ) ; } ; // &C:\MPY\mpy_examples\input_switch.mpy&11
      if ( 16 < 32 ) { P1DIR |= ( 1 << ( 16 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 16 & 15 ) ) ; P1REN &= ~ ( 1 << ( 16 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 16 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 16 & 15 ) ) ; P2REN &= ~ ( 1 << ( 16 & 15 ) ) ; } ; // &C:\MPY\mpy_examples\input_switch.mpy&12
      if ( 19 < 32 ) { P1DIR &= ~ ( 1 << ( 19 & 15 ) ) ; P1REN |= ( 1 << ( 19 & 15 ) ) ; P1OUT |= ( 1 << ( 19 & 15 ) ) ; } else { P2DIR &= ~ ( 1 << ( 19 & 15 ) ) ; P2REN |= ( 1 << ( 19 & 15 ) ) ; P2OUT |= ( 1 << ( 19 & 15 ) ) ; } ; // &C:\MPY\mpy_examples\input_switch.mpy&13
      last_sw = 0 ; // &C:\MPY\mpy_examples\input_switch.mpy&15
      while ( 1 ) { // &C:\MPY\mpy_examples\input_switch.mpy&17
          if ( 22 < 32 ) { P1OUT |= ( 1 << ( 22 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 22 & 15 ) ) ; } ; // &C:\MPY\mpy_examples\input_switch.mpy&19
          if ( 16 < 32 ) { P1OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 16 & 15 ) ) ; } ; // &C:\MPY\mpy_examples\input_switch.mpy&20
          wait ( 50 ) ; // &C:\MPY\mpy_examples\input_switch.mpy&21
          if ( 22 < 32 ) { P1OUT &= ~ ( 1 << ( 22 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 22 & 15 ) ) ; } ; // &C:\MPY\mpy_examples\input_switch.mpy&22
          if ( 16 < 32 ) { P1OUT |= ( 1 << ( 16 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 16 & 15 ) ) ; } ; // &C:\MPY\mpy_examples\input_switch.mpy&23
          wait ( 50 ) ; // &C:\MPY\mpy_examples\input_switch.mpy&24
          sw = ( ( ( ( 19 & 16 ) >> 4 ) & ( P1IN >> ( 19 & 15 ) ) ) | ( ( ( 19 & 32 ) >> 5 ) & ( P2IN >> ( 19 & 15 ) ) ) ) ; // &C:\MPY\mpy_examples\input_switch.mpy&26
          if ( sw != last_sw ) { // &C:\MPY\mpy_examples\input_switch.mpy&27
              print__mpy__ ( __mpy_write_uart_TxByte , "sds" , "The switch is :" , sw , "\n" ) ; } // &C:\MPY\mpy_examples\input_switch.mpy&28
          last_sw = sw ; } } // &C:\MPY\mpy_examples\input_switch.mpy&29


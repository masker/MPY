
      
#include <msp430.h>
#include "msp430g2231.h"
#include "C:\MPY\mpy_editor\mpy\mpy_functions.c"

      rand ( int  S ) { 
          S = ( ( S * 181 ) + 359 ) ; 
          return S ; } 
                        
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
   
int MASK1023 ; int j ; int MASK2047 ; int led7 ; int led6 ; int k ; int rval ; int pwm_sum ; int S ; int pwm ; int pwm_random ; int MASK8 ; 


      if ( 1 ) { 
          MASK2047 = ( ( 1 << 11 ) - 1 ) ; 
          MASK1023 = ( ( 1 << 10 ) - 1 ) ; 
          MASK8 = ( 1 << 8 ) ; 
          pwm = 2000 ; 
          S = 1000 ; 
          k = 0 ; 
          pwm_random = 0 ; 
          WDTCTL = ( WDTPW | WDTHOLD ) ; 
          P1DIR = 0 ; 
          P1DIR |= BIT2 ; 
          P1DIR |= BIT0 ; 
          P1DIR |= BIT6 ; 
          P1DIR |= BIT7 ; 
          P1SEL = 0 ; 
          P1SEL |= BIT2 ; 
          P1REN = 0 ; 
          P1REN |= BIT1 ; 
          P1REN |= BIT5 ; 
          P1OUT = ( BIT1 + BIT5 ) ; 
          CCR0 = ( 10000 - 1 ) ; 
          CCTL1 = OUTMOD_7 ; 
          CCR1 = pwm ; 
          TACTL = ( TASSEL_2 + MC_1 ) ; 
          rval = 0 ; 
          while ( 1 ) { 
              k += 1 ; 
              if ( ( k % 30 ) == 0 ) { 
                  S = rand ( S ) ; 
                  rval = ( S & MASK1023 ) ; 
                  rval = ( rval - 1000 ) ; } 
              if ( ( rval - pwm_random ) > 100 ) { 
                  pwm_random = ( pwm_random + 100 ) ; } 
              if ( ( rval - pwm_random ) < -100 ) { 
                  pwm_random = ( pwm_random - 100 ) ; } 
              for ( j = 0 ; j < 500 ; j = j + 1 ) { 
                  if ( ( 1 && ( j % 50 ) == 0 ) ) { 
                      S = rand ( S ) ; 
                      if ( ( S | MASK8 ) > 0 ) { 
                          led7 = BIT7 ; 
                          led6 = BIT6 ; } else { 
                          led7 = 0 ; 
                          led6 = 0 ; } } } 
              if ( ( P1IN & BIT1 ) ) { 
                  pwm = ( pwm + 100 ) ; } 
              if ( ( P1IN & BIT5 ) ) { 
                  pwm = ( pwm - 100 ) ; } 
              P1OUT = ( ( ( BIT1 + BIT5 ) + led6 ) + led7 ) ; 
              pwm_sum = ( pwm + pwm_random ) ; 
              if ( pwm_sum > 3200 ) { pwm_sum = 3200 ; } 
              if ( pwm_sum < 400 ) { pwm_sum = 400 ; } 
              CCR1 = pwm_sum ; } } } 

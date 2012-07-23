
      
#include <msp430.h>
#include "msp430g2553.h"
#include "c:\mpy\mpy_editor\mpy\mpy_functions.c"

int dist ; 

      ConfigureUserGPIO ( ) { 
          "setup the ios" ; 
          P2SEL = 0 ; 
          P2SEL2 = 0 ; 
          P1SEL = 0 ; 
          P1SEL2 = 0 ; 
          P2SEL = 0 ; 
          P2DIR = BIT6 ; 
          CACTL1 = 0 ; 
          CACTL2 = 0 ; } 
      ConfigureFAN8200 ( ) { 
          P1DIR |= ( ( BIT3 | BIT2 ) | BIT4 ) ; 
          P1OUT = 0 ; 
          P2DIR |= BIT2 ; 
          P2OUT = 0 ; 
          if ( 21 < 32 ) { P1DIR |= ( 1 << ( 21 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 21 & 15 ) ) ; P1REN &= ~ ( 1 << ( 21 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 21 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 21 & 15 ) ) ; P2REN &= ~ ( 1 << ( 21 & 15 ) ) ; } ; } 
      ConfigurePWM ( ) { 
          "Setup the Timer TA1 to control a servo. The PWM period is 20ms and\n    the pulse varies between 700us to 2200us to give a 180 deg rotation of the servo" ; 
          if ( 36 < 32 ) { P1DIR &= ~ ( 1 << ( 36 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 36 & 15 ) ) ; P1REN &= ~ ( 1 << ( 36 & 15 ) ) ; } else { P2DIR &= ~ ( 1 << ( 36 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 36 & 15 ) ) ; P2REN &= ~ ( 1 << ( 36 & 15 ) ) ; } ; 
          TA1CCR0 = 20000 ; 
          TA1CCTL2 = OUTMOD_7 ; 
          TA1CCR2 = 1300 ; 
          TA1CTL = ( TASSEL_2 + MC_1 ) ; } 
      arm_move ( int  pulse_duration ) { 
          TA1CCR2 = pulse_duration ; } 
      arm_onoff ( int  onoff ) { 
          if ( onoff == 1 ) { 
              if ( 36 < 32 ) { P1DIR |= ( 1 << ( 36 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 36 & 15 ) ) ; P1REN &= ~ ( 1 << ( 36 & 15 ) ) ; } else { P2DIR |= ( 1 << ( 36 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 36 & 15 ) ) ; P2REN &= ~ ( 1 << ( 36 & 15 ) ) ; } ; 
              if ( 36 < 32 ) { P1SEL |= ( 1 << ( 36 & 15 ) ) ; } else { P2SEL |= ( 1 << ( 36 & 15 ) ) ; } ; 
              print ( "      ARM 1\n" ) ; } else { 
              if ( 36 < 32 ) { P1DIR &= ~ ( 1 << ( 36 & 15 ) ) ; P1SEL &= ~ ( 1 << ( 36 & 15 ) ) ; P1REN &= ~ ( 1 << ( 36 & 15 ) ) ; } else { P2DIR &= ~ ( 1 << ( 36 & 15 ) ) ; P2SEL &= ~ ( 1 << ( 36 & 15 ) ) ; P2REN &= ~ ( 1 << ( 36 & 15 ) ) ; } ; 
              print ( "      ARM 0\n" ) ; } } 
      arm_flip ( ) { 
          arm_move ( 1300 ) ; 
          arm_onoff ( 1 ) ; 
          wait ( 1000 ) ; 
          arm_move ( 2000 ) ; 
          wait ( 1000 ) ; 
          arm_move ( 1300 ) ; 
          wait ( 1000 ) ; 
          arm_onoff ( 0 ) ; } 
      stop ( ) { 
          if ( 19 < 32 ) { P1OUT &= ~ ( 1 << ( 19 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 19 & 15 ) ) ; } ; 
          if ( 20 < 32 ) { P1OUT &= ~ ( 1 << ( 20 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 20 & 15 ) ) ; } ; 
          if ( 18 < 32 ) { P1OUT &= ~ ( 1 << ( 18 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 18 & 15 ) ) ; } ; 
          if ( 34 < 32 ) { P1OUT &= ~ ( 1 << ( 34 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 34 & 15 ) ) ; } ; } 
      forward ( ) { 
          print ( "  forward\n" ) ; 
          stop ( ) ; 
          if ( 19 < 32 ) { P1OUT |= ( 1 << ( 19 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 19 & 15 ) ) ; } ; 
          if ( 20 < 32 ) { P1OUT |= ( 1 << ( 20 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 20 & 15 ) ) ; } ; } 
      backward ( ) { 
          print ( "  backward\n" ) ; 
          stop ( ) ; 
          if ( 19 < 32 ) { P1OUT |= ( 1 << ( 19 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 19 & 15 ) ) ; } ; } 
      turn_right ( ) { 
          print ( "  turn_right\n" ) ; 
          stop ( ) ; 
          if ( 18 < 32 ) { P1OUT |= ( 1 << ( 18 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 18 & 15 ) ) ; } ; 
          if ( 34 < 32 ) { P1OUT |= ( 1 << ( 34 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 34 & 15 ) ) ; } ; } 
      turn_left ( ) { 
          print ( "  turn_left\n" ) ; 
          stop ( ) ; 
          if ( 18 < 32 ) { P1OUT |= ( 1 << ( 18 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 18 & 15 ) ) ; } ; } 
      ir_led_on ( int  user_pin ) { 
          if ( user_pin == 4 ) { 
              P2OUT |= BIT3 ; } else 
              if ( user_pin == 5 ) { 
                  P2OUT |= BIT5 ; } else 
                  if ( user_pin == 6 ) { 
                      P2OUT |= BIT6 ; } else 
                      if ( user_pin == 7 ) { 
                          P2OUT |= BIT7 ; } } 
      ir_led_off ( int  user_pin ) { 
          if ( user_pin == 4 ) { 
              P2OUT &= ~ BIT3 ; } else 
              if ( user_pin == 5 ) { 
                  P2OUT &= ~ BIT5 ; } else 
                  if ( user_pin == 6 ) { 
                      P2OUT &= ~ BIT6 ; } else 
                      if ( user_pin == 7 ) { 
                          P2OUT &= ~ BIT7 ; } } 
      Read_IR ( int  analog_pin , int  led_pin ) { int min ; int max ; int diff ; 
          if ( 38 < 32 ) { P1OUT |= ( 1 << ( 38 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 38 & 15 ) ) ; } ; 
          wait ( 2 ) ; 
          if ( 36 < 32 ) { P1OUT |= ( 1 << ( 36 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 36 & 15 ) ) ; } ; 
          min = adc ( 23 ) ; 
          if ( 36 < 32 ) { P1OUT &= ~ ( 1 << ( 36 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 36 & 15 ) ) ; } ; 
          if ( 38 < 32 ) { P1OUT &= ~ ( 1 << ( 38 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 38 & 15 ) ) ; } ; 
          wait ( 2 ) ; 
          if ( 36 < 32 ) { P1OUT |= ( 1 << ( 36 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 36 & 15 ) ) ; } ; 
          max = adc ( 23 ) ; 
          if ( 36 < 32 ) { P1OUT &= ~ ( 1 << ( 36 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 36 & 15 ) ) ; } ; 
          diff = ( ( ( max - min ) * 3 ) / 2 ) ; 
          if ( max > min ) { 
              dist = ( ( max * 30 ) / diff ) ; 
              dist = ( ( dist * 30 ) / 10 ) ; } else { 
              dist = 31000 ; } 
          print ( "the IR sensor value is" ) ; 
          print_num ( dist ) ; 
          print_num ( min ) ; 
          print_num ( max ) ; 
          print ( "\n" ) ; 
          if ( dist > 900 ) { 
              if ( 21 < 32 ) { P1OUT |= ( 1 << ( 21 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 21 & 15 ) ) ; } ; } else 
              if ( dist > 400 ) { 
                  if ( 21 < 32 ) { P1OUT &= ~ ( 1 << ( 21 & 15 ) ) ; } else { P2OUT &= ~ ( 1 << ( 21 & 15 ) ) ; } ; } else { 
                  if ( 21 < 32 ) { P1OUT |= ( 1 << ( 21 & 15 ) ) ; } else { P2OUT |= ( 1 << ( 21 & 15 ) ) ; } ; } 
          return dist ; } 
      turn_towards_object ( ) { int obj_distance ; int angle ; int obj_angle ; 
          "Turn round 360deg in 30deg steps and look for the direction which has the\n    has the least distance" ; 
          obj_distance = 30000 ; 
          obj_angle = 0 ; 
          for ( angle = 0 ; angle < 12 ; angle = angle + 1 ) { 
              dist = Read_IR ( 23 , 38 ) ; 
              if ( dist < obj_distance ) { 
                  obj_distance = dist ; 
                  obj_angle = angle ; } 
              turn_right ( ) ; 
              wait ( 300 ) ; 
              stop ( ) ; } 
          print_value ( "min distance detected = " , obj_distance ) ; 
          print_value ( "direction =" , obj_angle ) ; 
          wait ( 1000 ) ; 
          for ( angle = 0 ; angle < obj_angle ; angle = angle + 1 ) { 
              dist = Read_IR ( 23 , 38 ) ; 
              if ( dist < obj_distance ) { 
                  obj_distance = dist ; 
                  obj_angle = angle ; } 
              turn_right ( ) ; 
              wait ( 300 ) ; 
              stop ( ) ; } } 
                        
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
   



      print ( "hexbug1 has started\n" ) ; 
      BCSCTL1 = CALBC1_1MHZ ; 
      DCOCTL = CALDCO_1MHZ ; 
      BCSCTL2 &= ~ DIVS_3 ; 
      ConfigureUserGPIO ( ) ; 
      ConfigureFAN8200 ( ) ; 
      ConfigurePWM ( ) ; 
      wait ( 3000 ) ; 
      print ( "hexbug1 has started 7\n" ) ; 
      if ( 0 ) { 
          wait ( 2000 ) ; 
          forward ( ) ; 
          wait ( 500 ) ; 
          turn_right ( ) ; 
          wait ( 500 ) ; 
          backward ( ) ; 
          wait ( 500 ) ; 
          turn_left ( ) ; 
          wait ( 500 ) ; 
          stop ( ) ; } 
      while ( 1 ) { 
          print ( "hexbug1 while 1\n" ) ; 
          dist = Read_IR ( 23 , 38 ) ; 
          print ( "hexbug1 while 2\n" ) ; 
          if ( dist < 300 ) { 
              arm_flip ( ) ; 
              backward ( ) ; } else 
              if ( dist < 400 ) { 
                  stop ( ) ; } else 
                  if ( dist < 1000 ) { 
                      forward ( ) ; } else { 
                      turn_towards_object ( ) ; 
                      wait ( 2000 ) ; 
                      forward ( ) ; } 
          wait ( 2000 ) ; 
          arm_onoff ( 0 ) ; } } 

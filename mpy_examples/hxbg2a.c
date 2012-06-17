
      
#include <msp430.h>
#include "msp430g2553.h"
#include "C:\MPY\mpy_editor\mpy\mpy_functions.c"

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
          P1DIR |= BIT5 ; P1SEL &= ~ BIT5 ; P1REN &= ~ BIT5 ; } 
      ConfigurePWM ( ) { 
          "Setup the Timer TA1 to control a servo. The PWM period is 20ms and\n    the pulse varies between 700us to 2200us to give a 180 deg rotation of the servo" ; 
          P2DIR &= ~ BIT4 ; P2SEL &= ~ BIT4 ; P2REN &= ~ BIT4 ; 
          TA1CCR0 = 20000 ; 
          TA1CCTL2 = OUTMOD_7 ; 
          TA1CCR2 = 1300 ; 
          TA1CTL = ( TASSEL_2 + MC_1 ) ; } 
      arm_move ( int  pulse_duration ) { 
          TA1CCR2 = pulse_duration ; } 
      arm_onoff ( int  onoff ) { 
          if ( onoff == 1 ) { 
              P2DIR |= BIT4 ; P2SEL &= ~ BIT4 ; P2REN &= ~ BIT4 ; 
              P2SEL |= BIT4 ; 
              print ( "      ARM 1\n" ) ; } else { 
              P2DIR &= ~ BIT4 ; P2SEL &= ~ BIT4 ; P2REN &= ~ BIT4 ; 
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
      ConfigureADC10 ( int  user_pin ) { 
          ADC10CTL0 &= ~ ENC ; 
          ADC10CTL0 = ( ADC10SHT_2 + ADC10ON ) ; 
          if ( user_pin == 0 ) { 
              ADC10CTL1 = INCH_0 ; 
              ADC10AE0 |= 1 ; } else 
              if ( user_pin == 1 ) { 
                  ADC10CTL1 = INCH_1 ; 
                  ADC10AE0 |= 2 ; } else 
                  if ( user_pin == 2 ) { 
                      ADC10CTL1 = INCH_6 ; 
                      ADC10AE0 |= 64 ; } else 
                      if ( user_pin == 3 ) { 
                          ADC10CTL1 = INCH_7 ; 
                          ADC10AE0 |= 128 ; } } 
      stop ( ) { 
          P1OUT &= ~ BIT3 ; 
          P1OUT &= ~ BIT4 ; 
          P1OUT &= ~ BIT2 ; 
          P2OUT &= ~ BIT2 ; } 
      forward ( ) { 
          print ( "  forward\n" ) ; 
          stop ( ) ; 
          P1OUT |= BIT3 ; 
          P1OUT |= BIT4 ; } 
      backward ( ) { 
          print ( "  backward\n" ) ; 
          stop ( ) ; 
          P1OUT |= BIT3 ; } 
      turn_right ( ) { 
          print ( "  turn_right\n" ) ; 
          stop ( ) ; 
          P1OUT |= BIT2 ; 
          P2OUT |= BIT2 ; } 
      turn_left ( ) { 
          print ( "  turn_left\n" ) ; 
          stop ( ) ; 
          P1OUT |= BIT2 ; } 
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
      Read_IR ( int  analog_pin , int  led_pin ) { int dist ; int min ; int max ; int diff ; 
          ADC10CTL0 &= ~ ENC ; ADC10CTL0 = ( ADC10SHT_2 + ADC10ON ) ; 
          ir_led_on ( led_pin ) ; 
          wait ( 2 ) ; 
          P2OUT |= BIT4 ; 
          min = adc ( 7 ) ; 
          P2OUT &= ~ BIT4 ; 
          ir_led_off ( led_pin ) ; 
          wait ( 2 ) ; 
          P2OUT |= BIT4 ; 
          max = adc ( 7 ) ; 
          P2OUT &= ~ BIT4 ; 
          diff = ( ( ( max - min ) * 3 ) / 2 ) ; 
          if ( max > min ) { 
              dist = ( ( max * 30 ) / diff ) ; 
              dist = ( ( dist * 30 ) / 30 ) ; } else { 
              dist = 31000 ; } 
          print ( "the IR sensor value is" ) ; 
          print_num ( dist ) ; 
          print_num ( min ) ; 
          print_num ( max ) ; 
          print ( "\n" ) ; 
          if ( dist > 900 ) { 
              P1OUT |= BIT5 ; } else 
              if ( dist > 400 ) { 
                  P1OUT &= ~ BIT5 ; } else { 
                  P1OUT |= BIT5 ; } 
          return dist ; } 
      turn_towards_object ( ) { int dist ; int obj_distance ; int angle ; int obj_angle ; 
          "Turn round 360deg in 30deg steps and look for the direction which has the\n    has the least distance" ; 
          obj_distance = 30000 ; 
          obj_angle = 0 ; 
          for ( angle = 0 ; angle < 12 ; angle = angle + 1 ) { 
              dist = Read_IR ( 3 , 6 ) ; 
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
              dist = Read_IR ( 3 , 6 ) ; 
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
   
int dist ; 


      print ( "hexbug1 has started\n" ) ; 
      BCSCTL1 = CALBC1_1MHZ ; 
      DCOCTL = CALDCO_1MHZ ; 
      BCSCTL2 &= ~ DIVS_3 ; 
      print ( "hexbug1 has started 2\n" ) ; 
      ConfigureUserGPIO ( ) ; 
      ConfigureFAN8200 ( ) ; 
      ConfigurePWM ( ) ; 
      wait ( 3000 ) ; 
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
          dist = Read_IR ( 3 , 6 ) ; 
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


      
#include <msp430.h>
#include "msp430g2553.h"
#include "C:\MPY\mpy_editor\mpy\mpy_functions.c"

      servo ( int  servo_number , int  position ) { int period_min ; int a ; int adiv ; int period_scale ; int period_max ; 
          "moves the position of the servo\n    servo_number = 0 is pwm_a\n    servo_number = 1 is pwm_b\n    position is a number between 0 and 100\n    \n    Servo 0 (pwm_a) and 1 (pwm_b) use a constant duty cycle and varies the period to move the position\n    Servo 2 (pwm_c) varies the duty cycle (pulse width) to move\n    " ; 
          period_min = 6200 ; 
          period_max = 25000 ; 
          period_scale = ( ( period_max - period_min ) / 100 ) ; 
          if ( position < 0 ) { 
              position = - position ; } 
          a = ( period_min + ( position * period_scale ) ) ; 
          adiv = ( a / 10 ) ; 
          if ( servo_number == 0 ) { 
              TA0CCR0 = a ; 
              TA0CCR1 = adiv ; } else 
              if ( servo_number == 1 ) { 
                  TA1CCR0 = a ; 
                  TA1CCR1 = adiv ; } else 
                  if ( servo_number == 2 ) { 
                      TA1CCR2 = adiv ; } } 
      position_increment ( int  pos , int  inc , int  lim_min , int  lim_max ) { 
          "position_increment will increment 'pos' by 'inc'\n    if pos is positive and is greater than lim_max, pos is negated to be -lim_max\n      which means it will start incrementing upwards from -lim_max\n    if pos is negative and is greater than lim_min, pos is negated to be +lim_min\n      which means it will start incrementing upwards from +lim_min\n\n    This function is intended to to create a increasing and then decreasing value\n    The value of pos needs to be made positve when it is used.\n    The sign of pos indicates whether it is incrementing or decrementing.\n    " ; 
          pos += inc ; 
          if ( pos >= 0 ) { 
              if ( pos > lim_max ) { 
                  pos = - lim_max ; } } else 
              if ( pos > - lim_min ) { 
                  pos = lim_min ; } 
          return pos ; } 
      move ( int  servo_number , int  start , int  finish , int  number_of_steps , int  move_time ) { int delay_per_step ; int i ; int pos ; int inc ; 
          "moves the specified servo from start to finish position\n    using the number of steps specified taking the time specified\n    " ; 
          pos = ( start * 100 ) ; 
          inc = ( ( ( finish - start ) * 100 ) / number_of_steps ) ; 
          delay_per_step = ( move_time / number_of_steps ) ; 
          for ( i = 0 ; i < number_of_steps ; i = i + 1 ) { 
              servo ( servo_number , ( pos / 100 ) ) ; 
              wait ( delay_per_step ) ; 
              pos += inc ; } 
          servo ( servo_number , finish ) ; } 
      move2 ( int  servo1_number , int  servo2_number , int  start1 , int  finish1 , int  start2 , int  finish2 , int  number_of_steps , int  move_time ) { int inc1 ; int inc2 ; int delay_per_step ; int i ; int pos2 ; int pos1 ; 
          "moves the specified servo from start to finish position\n    using the number of steps specified taking the time specified\n    " ; 
          pos1 = ( start1 * 100 ) ; 
          inc1 = ( ( ( finish1 - start1 ) * 100 ) / number_of_steps ) ; 
          pos2 = ( start2 * 100 ) ; 
          inc2 = ( ( ( finish2 - start2 ) * 100 ) / number_of_steps ) ; 
          delay_per_step = ( move_time / number_of_steps ) ; 
          for ( i = 0 ; i < number_of_steps ; i = i + 1 ) { 
              servo ( servo1_number , ( pos1 / 100 ) ) ; 
              servo ( servo2_number , ( pos2 / 100 ) ) ; 
              wait ( delay_per_step ) ; 
              pos1 += inc1 ; 
              pos2 += inc2 ; } 
          servo ( servo1_number , finish1 ) ; 
          servo ( servo2_number , finish2 ) ; } 
      do_move_yes ( int  down , int  up , int  num_nods , int  move_time ) { int i ; int step_time ; 
          P2OUT |= BIT5 ; 
          step_time = ( move_time / ( num_nods * 2 ) ) ; 
          for ( i = 0 ; i < num_nods ; i = i + 1 ) { 
              move ( 1 , down , up , 5 , step_time ) ; 
              move ( 1 , up , down , 5 , step_time ) ; } 
          P2OUT &= ~ BIT5 ; } 
      do_move_no ( int  left , int  right , int  num_nods , int  move_time ) { int i ; int step_time ; 
          step_time = ( move_time / ( num_nods * 2 ) ) ; 
          for ( i = 0 ; i < num_nods ; i = i + 1 ) { 
              move ( 2 , left , right , 5 , step_time ) ; 
              move ( 2 , right , left , 5 , step_time ) ; } } 
      do_move_look_sideways ( int  sway , int  turn , int  move_time ) { int step_time ; 
          step_time = ( move_time / 2 ) ; 
          move2 ( 0 , 2 , 59 , sway , 50 , turn , 10 , step_time ) ; 
          move2 ( 0 , 2 , sway , 59 , turn , 50 , 10 , step_time ) ; } 
      do_move_circle ( int  clockwise , int  number_of_rotations , int  time_per_rotation ) { int amin ; int bstart ; int i ; int num_steps_total ; int num_steps ; int binc ; int bpos ; int bmin ; int time_per_step ; int ainc ; int bmax ; int amax ; int apos ; 
          "Move the lamp in a circular pattern\n    " ; 
          amin = 30 ; 
          amax = 70 ; 
          bmin = 0 ; 
          bmax = 100 ; 
          num_steps = 20 ; 
          time_per_step = ( time_per_rotation / ( num_steps * 2 ) ) ; 
          ainc = ( ( amax - amin ) / num_steps ) ; 
          binc = ( ( bmax - bmin ) / num_steps ) ; 
          amax = ( amin + ( num_steps * ainc ) ) ; 
          bmax = ( bmin + ( num_steps * binc ) ) ; 
          bstart = ( bmin + ( ( num_steps * binc ) / 2 ) ) ; 
          if ( clockwise ) { 
              apos = amax ; 
              bpos = bstart ; } else { 
              apos = amax ; 
              bpos = - bstart ; } 
          num_steps_total = ( ( num_steps * 2 ) * number_of_rotations ) ; 
          for ( i = 0 ; i < num_steps_total ; i = i + 1 ) { 
              apos = position_increment ( apos , ainc , amin , amax ) ; 
              bpos = position_increment ( bpos , binc , bmin , bmax ) ; 
              servo ( 0 , apos ) ; 
              servo ( 1 , bpos ) ; 
              wait ( time_per_step ) ; } } 
      do_jig ( ) { int count ; int tim ; int do_loop ; 
          tim = 500 ; 
          print ( "do_jig entering loop\n" ) ; 
          do_loop = 1 ; 
          while ( do_loop == 1 ) { 
              count = 5 ; 
              while ( ( do_loop == 1 && count > 0 ) ) { 
                  if ( ( ( P1IN & BIT4 ) >> 4 ) == 1 ) { 
                      tim += 100 ; } 
                  if ( ( ( P1IN & BIT5 ) >> 5 ) == 1 ) { 
                      tim -= 100 ; } 
                  if ( ( ( P1IN & BIT7 ) >> 7 ) == 1 ) { 
                      do_loop = 0 ; } 
                  do_move_yes ( 40 , 60 , 2 , tim ) ; 
                  wait ( ( tim * 2 ) ) ; 
                  count -= 1 ; } 
              count = 5 ; 
              while ( ( do_loop == 1 && count > 0 ) ) { 
                  if ( ( ( P1IN & BIT4 ) >> 4 ) == 1 ) { 
                      tim += 100 ; } 
                  if ( ( ( P1IN & BIT5 ) >> 5 ) == 1 ) { 
                      tim -= 100 ; } 
                  if ( ( ( P1IN & BIT7 ) >> 7 ) == 1 ) { 
                      do_loop = 0 ; } 
                  do_move_no ( 40 , 60 , 2 , tim ) ; 
                  wait ( ( tim * 2 ) ) ; 
                  count -= 1 ; } } 
          print ( "                  OUT of loop\n" ) ; } 
                        
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
   
int bpos ; int cpos ; int apos ; 


      TA0CTL = ( TASSEL_2 + MC_1 ) ; TA0CCTL1 = OUTMOD_7 ; TA0CCTL2 = OUTMOD_7 ; TA0CCR0 = 10000 ; TA1CTL = ( TASSEL_2 + MC_1 ) ; TA1CCTL1 = OUTMOD_7 ; TA1CCTL2 = OUTMOD_7 ; TA1CCR0 = 10000 ; 
      P1DIR |= BIT6 ; P1SEL |= BIT6 ; P1REN &= ~ BIT6 ; 
      P2DIR |= BIT2 ; P2SEL |= BIT2 ; P2REN &= ~ BIT2 ; 
      P2DIR |= BIT4 ; P2SEL |= BIT4 ; P2REN &= ~ BIT4 ; 
      P1DIR &= ~ BIT4 ; P1REN |= BIT4 ; P1OUT &= ~ BIT4 ; 
      P1DIR &= ~ BIT5 ; P1REN |= BIT5 ; P1OUT &= ~ BIT5 ; 
      P1DIR &= ~ BIT7 ; P1REN |= BIT7 ; P1OUT &= ~ BIT7 ; 
      P2DIR &= ~ BIT0 ; P2REN |= BIT0 ; P2OUT &= ~ BIT0 ; 
      P2DIR &= ~ BIT1 ; P2REN |= BIT1 ; P2OUT &= ~ BIT1 ; 
      P1DIR &= ~ BIT3 ; P1REN |= BIT3 ; P1OUT |= BIT3 ; 
      P2DIR |= BIT5 ; P2SEL &= ~ BIT5 ; P2REN &= ~ BIT5 ; 
      apos = 50 ; 
      bpos = 50 ; 
      cpos = 50 ; 
      P1DIR &= ~ BIT2 ; P1REN |= BIT2 ; P1OUT |= BIT2 ; 
      while ( 1 ) { 
          if ( ( ( P1IN & BIT4 ) >> 4 ) == 1 ) { 
              do_move_yes ( 40 , 60 , 4 , 1000 ) ; } 
          if ( ( ( P1IN & BIT5 ) >> 5 ) == 1 ) { 
              do_move_no ( 40 , 60 , 4 , 1000 ) ; } 
          if ( ( ( P1IN & BIT7 ) >> 7 ) == 1 ) { 
              do_move_look_sideways ( 15 , 75 , 1000 ) ; } 
          if ( ( ( P2IN & BIT0 ) >> 0 ) == 1 ) { 
              do_move_look_sideways ( 100 , 0 , 1000 ) ; } 
          if ( ( ( P2IN & BIT1 ) >> 1 ) == 1 ) { 
              do_move_circle ( 1 , 2 , 1000 ) ; } 
          if ( ( ( P1IN & BIT3 ) >> 3 ) == 0 ) { 
              do_move_circle ( 0 , 2 , 1000 ) ; } 
          if ( ( ( P1IN & BIT2 ) >> 2 ) == 0 ) { 
              do_jig ( ) ; } 
          wait ( 50 ) ; } 
      halt ( ) ; } 

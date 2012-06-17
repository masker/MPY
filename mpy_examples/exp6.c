
      
#include <msp430.h>
#include "msp430g2553.h"
#include "C:\Python27\MPY\mpy\mpy\mpy_functions.c"

                        
void main (void) { 

    WDTCTL = WDTPW + WDTHOLD; // Stop WDT
    BCSCTL1 = CALBC1_1MHZ;    // Set range
    DCOCTL  = CALDCO_1MHZ;    // SMCLK = DCO = 1MHz
   
int count ; int x ; 


      
      x = ( P1IN & 1 ) ; 
      count = 0 ; 
      while ( 1 ) { 
          wait ( 500 ) ; 
          print_value ( "mikey : " , count ) ; 
          count += 1 ; } } 

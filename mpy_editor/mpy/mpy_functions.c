// #include <signal.h>
// #include <msp430.h>
// #include "msp430g2553.h"
// #define TXD BIT1 // TXD on P1.1
 
#include  <stdarg.h>

// Function Definitions
void Transmit(unsigned int);
void wait ( int  dly );
void print(char *string); 
void print_hex(unsigned int num);
void print_num(int num);
void print_value(char *string, int num);


int adc(int pin) {
//    if ((pin & 15) > 7) { ADC10CTL0 |= (REFON | REF2_5V); } // turn on the Ref generator for the Temp sensor (shouldn't need to do this!)
    ADC10CTL1 = (pin & 15) << 12;
    ADC10AE0  = (1 << (pin & 15)) & 255;
    ADC10CTL0 |= ENC + ADC10SC;     // Start A/D conversion
    while (ADC10CTL1 & BUSY);       // Wait if ADC10 core is active
//    if ((pin & 15) > 7) { ADC10CTL0 &= ~(REFON | REF2_5V); }  // turn off the reference
    ADC10CTL0 &= ~ENC;
    return ADC10MEM; }              // return the result
    

int   random( int  S ) { 
          S = ( ( (S>>1) * (-18121) ) + 359 ) ; 
          return S ; } 


// wait a dly number of milliseconds, negative dly values are made positive
void  wait( int  dly ) { int i ; int k ; 
          if (dly < 0) { dly = - dly; }
          for ( i = 0 ; i < dly ; i = i + 1 ) { 
              for ( k = 0 ; k < 280 ; k = k + 1 ) { 
                  _NOP ( ) ; } } } 

// enter an infinite loop which 
void  halt(void) { 
          for ( ; ;  ) { 
                  _NOP ( ) ; } }  
                


void print_mpy( const char *fmt, ... )
{
   va_list ap;
   char *p, *sval;
   int ival;
   int x;
   unsigned int TXByte;
  
//   print_num( ap ) ;
   
   va_start(ap, fmt);
   for (p = fmt; *p; p++){
       switch(*p) {
          case 'd':
              ival = va_arg(ap, int);
              print_num( ival );
              break;
          case 'h':
              ival = va_arg(ap, int);
              print_hex( ival );
              break;
          case 's':
              sval = va_arg(ap, char *);
              print(sval);
              break;
       }
   }
   va_end(ap);
}

void print_value(char *string, int num)
{
    print( string );
    print_num( num );
    print( "\n" );
}

void print(char *string)
{
    unsigned int TXByte;
    while (*string) {
        TXByte = *string++;
        Transmit(TXByte);
    }
}


void print_hex(unsigned int num)
{
    unsigned int TXByte;
    char chr, i, hex_dig; 
    for (i=12; i>=0; i=i-4 ) {
        hex_dig =  ((num >> i) & 0xF); 
        if (hex_dig >= 10) hex_dig += 7;
        TXByte = 48 + hex_dig;   
        Transmit(TXByte);
    }
}


void print_num(int num)
{
    unsigned int TXByte;
    char chr, i, first_char;
    int dig;
    int first_num = 0;
    int exp[] = { 10000, 1000, 100, 10 , 1 };  

    // if less than zero print out '-'
    // and invert all the bits and add 1
    if (num < 0) {
        first_char = '-';
        num = num ^ 65535;
        num = num + 1;
    } else {
        first_char = ' ';
    }
    
    for (i=0; i<=4; i=i+1) {
        dig = num / exp[i];
        num = num % exp[i];
        if (dig > 0 || first_num == 1 || i == 4) {
            if(first_num == 0){
                Transmit(first_char);
            }
            first_num = 1;
            TXByte = 48 + dig;   
            Transmit(TXByte);
        } else {
            Transmit(' ');
        }
    }
}




// Function Transmits Character from TXByte
void Transmit(unsigned int TXByte)
{
  unsigned int i, k;
  P1DIR |= BIT1; 
  P1REN &= ~BIT1;          
  TXByte |= 0x100;         // Add stop bit to TXByte (which is logical 1)
  TXByte = TXByte << 1;    // Add start bit (which is logical 0)

//  TXByte = 0x255;
  
  for ( i=0; i<10; i=i+1 ) { 
      if (TXByte & 0x01) {
          P1OUT |=  BIT1;
      } else {
          P1OUT &= ~BIT1;
      }
      for ( k = 0 ; k < 21 ; k = k + 1 ) { 
                  _NOP ( ) ; }
      TXByte = TXByte >> 1;
  }
}
  




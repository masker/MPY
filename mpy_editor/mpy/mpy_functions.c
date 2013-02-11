// #include <signal.h>
// #include <msp430.h>
// #include "msp430g2553.h"
// #define TXD BIT1 // TXD on P1.1
 
#include  <stdarg.h>




// Function Definitions
void __mpy_write_uart_TxByte(unsigned int);
void __mpy_write_lcd_TxByte(unsigned int);
void wait ( int  dly );
void print_str(int (*func)(int), char *string); 
void print_hex(int (*func)(int), unsigned int num);
void print_num(int (*func)(int), int num);
void print_value(char *string, int num);
void __setout(int portpin, int value);


//---------------------------------------------------------------------------------------
// global varaibles used for the LCD interface

int _lcd_DB7;
int _lcd_DB6;
int _lcd_DB5;
int _lcd_DB4;
int _lcd_EN;
int _lcd_RS;
int _lcd_char_count;

//---------------------------------------------------------------------------------------
void __setout(int portpin, int value)
// generic output command, does the same as the 'dirout' and 'out' macro combined
{
  
  if (portpin < 0x20)
  {
      P1DIR |=    1 << (portpin & 15);
      P1SEL &=   ~ (1 << (portpin & 15));
      P1REN &=   ~ (1 << (portpin & 15));
      if (value > 0) { P1OUT |=    1 << (portpin & 15); } else { P1OUT &=   ~ (1 << (portpin & 15)); }
  } else {
      P2DIR |=    1 << (portpin & 15);
      P2SEL &=   ~ (1 << (portpin & 15));
      P2REN &=   ~ (1 << (portpin & 15));
      if (value > 0) { P2OUT |=    1 << (portpin & 15); } else {  P2OUT &=   ~ (1 << (portpin & 15)); }
  }
}

//---------------------------------------------------------------------------------------
void _lcd_4bit_write( int value )
// Writes bits 7-4 to DB7-DB4, only bits 7-4 are used  all other bits are ignored'''
{
    __setout(_lcd_DB7, value & 0x80 );
    __setout(_lcd_DB6, value & 0x40 );
    __setout(_lcd_DB5, value & 0x20 );
    __setout(_lcd_DB4, value & 0x10 );
    
    __setout(_lcd_EN, 1);
    __setout(_lcd_EN, 0);
}


void _lcd_control( int value, int dly )
// Write a control instruction, only bits 7-4 are used
{
    __setout(_lcd_RS, 0);
    _lcd_4bit_write( value );
    wait( dly );
}

void _lcd_clear()
//Clears both lines of LCD, and returns cursor
{
    _lcd_char_count = 0;
    _lcd_control( 0x00, 0 ); _lcd_control( 0x10, 3 );   // Clear Display    
    _lcd_control( 0x00, 0 ); _lcd_control( 0x20, 1 );   // Return Cursor to home position :  0,0,1,0
}    



int lcd_enable( int DB7, int DB6, int DB5, int DB4, int EN, int RS)
// function to enable the 6wire lcd interface
{

  // first save the 6 lcd pins for use in this function and 
  _lcd_DB7 = DB7;
  _lcd_DB6 = DB6;
  _lcd_DB5 = DB5;
  _lcd_DB4 = DB4;
  _lcd_EN  = EN;
  

//  intialize with three 'Function Set' commands
    wait(100);
    _lcd_control( 0x30, 5 );
    _lcd_control( 0x30, 1 );
    _lcd_control( 0x30, 1 );
    
    _lcd_control( 0x20, 1 );                            // Put it into 4bit mode
    _lcd_control( 0x20, 1 ); _lcd_control( 0x80, 1 );   // N=1(2lines), F=0(5x7) , 0,0
    
    _lcd_control( 0x00, 1 ); _lcd_control( 0x80, 1 );   // Enable Disp,Curs :  1, D=0(disp off), C=0(Crs off), B=0(Blnk off)  
    _lcd_control( 0x00, 1 ); _lcd_control( 0xC0, 1 );   // Enable Disp,Curs :  1, D=0(disp off), C=0(Crs off), B=0(Blnk off)  
    _lcd_control( 0x00, 1 ); _lcd_control( 0x60, 1 );   // 'Entry Mode Set' :  0, 1, ID=1(inc curs), S=0(shift dsp off)
    
    _lcd_clear();
  
}



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
                

/* Generic mpy print function 
   The low-level character output write function is passed in a the first argument 'func'
   The second parameter is the format string which determines the number and types of the
   following parameters
*/ 
void print__mpy__( int (*func)(int), char *fmt, ... )
{
   va_list ap;
   char *p, *sval;
   int ival;
   int x;
   unsigned int __mpy_TxByte;
  
//   print_num( ap ) ;
   
   va_start(ap, fmt);
   for (p = fmt; *p; p++){
       switch(*p) {
          case 'd':
              ival = va_arg(ap, int);
              print_num( func, ival );
              break;
          case 'h':
              ival = va_arg(ap, int);
              print_hex( func, ival );
              break;
          case 's':
              sval = va_arg(ap, char *);
              print_str( func, sval);
              break;
       }
   }
   va_end(ap);
}



void print_str( int (*func)(int), char *string)
{
    unsigned int __mpy_TxByte;
    while (*string) {
        __mpy_TxByte = *string++;
        (func)(__mpy_TxByte);
    }
}


void print_hex( int (*func)(int), unsigned int num)
{
    unsigned int __mpy_TxByte;
    char chr, i, hex_dig; 
    for (i=12; i>=0; i=i-4 ) {
        hex_dig =  ((num >> i) & 0xF); 
        if (hex_dig >= 10) hex_dig += 7;
        __mpy_TxByte = 48 + hex_dig;   
        (func)(__mpy_TxByte);
    }
}


void print_num( int (*func)(int), int num)
{
    unsigned int __mpy_TxByte;
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
                (func)(first_char);
            }
            first_num = 1;
            __mpy_TxByte = 48 + dig;   
            (func)(__mpy_TxByte);
        } else {
            (func)(' ');
        }
    }
}




// Function __mpy_Transmits Character from __mpy_TxByte
void __mpy_write_uart_TxByte(unsigned int __mpy_TxByte)
{
  unsigned int i, k;
  P1DIR |= BIT1; 
  P1REN &= ~BIT1;          
  __mpy_TxByte |= 0x100;         // Add stop bit to __mpy_TxByte (which is logical 1)
  __mpy_TxByte = __mpy_TxByte << 1;    // Add start bit (which is logical 0)

//  __mpy_TxByte = 0x255;
  
  for ( i=0; i<10; i=i+1 ) { 
      if (__mpy_TxByte & 0x01) {
          P1OUT |=  BIT1;
      } else {
          P1OUT &= ~BIT1;
      }
      for ( k = 0 ; k < 21 ; k = k + 1 ) { 
                  _NOP ( ) ; }
      __mpy_TxByte = __mpy_TxByte >> 1;
  }
}

//---------------------------------------------------------------------------
void __mpy_write_lcd_TxByte(unsigned int value)
//Writes an 8bit char using two 4bit writes, 4MSBs first then 4LSBs,
//also checks to see if the char is a LF or at the end of the first line
{

    if (_lcd_char_count >= 80) { _lcd_char_count == 0; }
    

    // Clear the display and reset position to 0 when we are doing the first character
    if (_lcd_char_count == 0) { _lcd_clear(); }  
    
    // Move the char position on to 40 if we are at the end of the first 16 char line
    if (_lcd_char_count >= 16 && _lcd_char_count < 64 ) { 
       _lcd_char_count = 64;
       _lcd_control( 0xC0, 1 ); _lcd_control( 0x00, 1 );  
    }
    
    if (value == 10)  // end of line will reset the char count and clear the display the next print
    {
        _lcd_char_count = 0;
    } else {
        __setout(_lcd_RS, 1);
        _lcd_4bit_write( value );        // bits 7-4 are written as is
        _lcd_4bit_write( value << 4 );   // bits 3-0 shifted into bit possitions 7-4, all other bits are ignored
        _lcd_char_count += 1;
    }
}







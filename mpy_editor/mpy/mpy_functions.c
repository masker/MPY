/*
###########################################################################
#  
#     This file is part of mpyEditor.
# 
#     mpyEditor is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
# 
#     mpyEditor is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
# 
#     You should have received a copy of the GNU General Public License
#     along with mpyEditor.  If not, see <http://www.gnu.org/licenses/>.
#
#     (C) Copyright 2013 Mike Asker    mike.asker@gmail.com
#
###########################################################################
#
#   mpy_functions.c
#   
#   This file is a collection of general purpose hardware functions for
#   controlling MSP430 peripherals using the MPY Editor and MPY Language
#
############################################################################
*/



// #include <signal.h>
// #include <msp430.h>
// #include "msp430g2553.h"
// #define TXD BIT1 // TXD on P1.1


#define _setbit(reg,bit)     reg |=   ( 1 << (bit & 15))
#define _resetbit(reg,bit)   reg &= ~ ( 1 << (bit & 15))  
#define _testbit(reg,bit)   ((reg & (1 << (bit & 15))) >> (bit & 15)) 


 
#include  <stdarg.h>




// Function Definitions
void __mpy_write_uart_TxByte(unsigned int);
void __mpy_write_lcd_TxByte(unsigned int);
void wait ( int  dly );
void print_str(int (*func)(int), char *string); 
void print_hex(int (*func)(int), unsigned int num, unsigned int bit_count);
void print_num(int (*func)(int), int num);
void print_value(char *string, int num);
void __out(int portpin, int value);
void __dirout(int portpin);
void __setout(int portpin, int value);
void _lcd2w_shift_1bit(int bit_value);

int _lcd_enable( void );


//---------------------------------------------------------------------------------------
// global varaibles used for the LCD interface

int _lcd_DB7;     // used to hold the pin name assigned to control the LCD DB7 signal in 6 wire  mode
int _lcd_DB6;     // ... DB6
int _lcd_DB5;     // ... DB5
int _lcd_DB4;     // ... DB4
int _lcd_EN;      // ... EN
int _lcd_RS;      // ... RS
int _lcd_DATA;    // ... DB6 in 2 wire mode
int _lcd_CLOCK;   // ... CLOCK
int _lcd_char_count; // used to count the number of charaters sent to the lcd so that we know when to move to the next line
int _lcd_mode;    // used to set whether we are in 6 wire mode or 2 wire mode (2=2wire mode, 6=6wire_mode)


//---------------------------------------------------------------------------------------
void __out(int portpin, int value)
// generic output command, does the same as the 'dirout' and 'out' macro combined
// It is defined here as a function so that it can be called from a C function 
{
  
  if (portpin < 0x20)
  {
      if (value > 0) { P1OUT |=    1 << (portpin & 15); } else { P1OUT &=   ~ (1 << (portpin & 15)); }
  } else {
      if (value > 0) { P2OUT |=    1 << (portpin & 15); } else {  P2OUT &=   ~ (1 << (portpin & 15)); }
  }
}
//---------------------------------------------------------------------------------------
//---------------------------------------------------------------------------------------

void __dirout(int portpin)
// generic output command, does the same as the 'dirout' and 'out' macro combined
// It is defined here as a function so that it can be called from a C function 
{
  
  if (portpin < 0x20)
  {
      P1DIR |=    1 << (portpin & 15);
      P1SEL &=   ~ (1 << (portpin & 15));
      P1REN &=   ~ (1 << (portpin & 15));
  } else {
      P2DIR |=    1 << (portpin & 15);
      P2SEL &=   ~ (1 << (portpin & 15));
      P2REN &=   ~ (1 << (portpin & 15));
  }
}


//---------------------------------------------------------------------------------------
static void __inline__ __pindir(int portpin, int direction)
// Sets the port direction 
{
  if(direction == 0x02) // OUT out
  {
      if (portpin < 0x20)
      {
          _setbit(P1DIR,portpin);
          _resetbit(P1SEL,portpin);
          _resetbit(P1REN,portpin);
      } else {
          _setbit(P2DIR,portpin);
          _resetbit(P2SEL,portpin);
          _resetbit(P2REN,portpin);
      }
  }
  else if (direction == 0x00)    // IN input
  {
      if (portpin < 0x20)
      {
          _resetbit(P1DIR,portpin);
          _resetbit(P1SEL,portpin);
          _resetbit(P1REN,portpin);
      } else {
          _resetbit(P2DIR,portpin);
          _resetbit(P2SEL,portpin);
          _resetbit(P2REN,portpin);
      }
  }
  else if (direction == 0x05)    // INPU input pullup
  {
      if (portpin < 0x20)
      {
          _resetbit(P1DIR,portpin);
          _resetbit(P1SEL,portpin);
          _setbit(P1REN,portpin);
          _setbit(P1OUT,portpin);
      } else {
          _resetbit(P2DIR,portpin);
          _resetbit(P2SEL,portpin);
          _setbit(P2REN,portpin);
          _setbit(P2OUT,portpin);
      }
  }
  else if (direction == 0x04)    // INPD input pulldown
  {
      if (portpin < 0x20)
      {
          _resetbit(P1DIR,portpin);
          _resetbit(P1SEL,portpin);
          _setbit(P1REN,portpin);
          _resetbit(P1OUT,portpin);
      } else {
          _resetbit(P2DIR,portpin);
          _resetbit(P2SEL,portpin);
          _setbit(P2REN,portpin);
          _resetbit(P2OUT,portpin);
      }
  }
  else if (direction == 0x0a)    // PULSEOUT pulse circuit output
  {
      if (portpin < 0x20)
      {
          _setbit(P1DIR,portpin);
          _setbit(P1SEL,portpin);
          _resetbit(P1REN,portpin);
      } else {
          _setbit(P2DIR,portpin);
          _setbit(P2SEL,portpin);
          _resetbit(P2REN,portpin);
      }
  }


}



//---------------------------------------------------------------------------------------
void _lcd_4bit_write( int value, int rs_value )
// Writes bits 7-4 to DB7-DB4, only bits 7-4 are used  all other bits are ignored
{
    if (_lcd_mode == 6) {   // 6 wire mode
      __out(_lcd_DB7, value & 0x80 );
      __out(_lcd_DB6, value & 0x40 );
      __out(_lcd_DB5, value & 0x20 );
      __out(_lcd_DB4, value & 0x10 );
      __out(_lcd_RS,  rs_value & 0x01);
      __out(_lcd_EN, 1);
      __out(_lcd_EN, 0);
    }
 
    if (_lcd_mode == 2) {      // 2 wire mode
      int i;
      // flush the shift register with 8 bits of zero data, in preparation for a the data 
      for (i=0; i<8; i++) {  
         _lcd2w_shift_1bit(0);
      }
      
      // send the first enable bit as the msb
      _lcd2w_shift_1bit(1);
      // then send the 4 bits msb first 
      _lcd2w_shift_1bit(value & 0x80);    
      _lcd2w_shift_1bit(value & 0x40);
      _lcd2w_shift_1bit(value & 0x20);
      _lcd2w_shift_1bit(value & 0x10);
      // followed by the RS 
      _lcd2w_shift_1bit(rs_value & 0x01);
      // then the final 2 unused bits
      _lcd2w_shift_1bit(0);
      _lcd2w_shift_1bit(1);
      // finally send a 1 to activate the enable signal
      _lcd2w_shift_1bit(0);

    }
}

///////////////////////////////////////////////////////////////////////
void _lcd2w_shift_1bit(int bit_value)
{
    __out(_lcd_DATA, bit_value );  __out(_lcd_CLOCK, 1 ); __out(_lcd_CLOCK, 0 );
}

void _lcd_control( int value, int dly )
// Write a control instruction, only bits 7-4 are used
{
//    __setout(_lcd_RS, 0);
    _lcd_4bit_write( value, 0 );
    wait( dly );
}

///////////////////////////////////////////////////////////////////////
void _lcd_clear()
//Clears both lines of LCD, and returns cursor
{
    _lcd_char_count = 0;
    _lcd_control( 0x00, 0 ); _lcd_control( 0x10, 3 );   // Clear Display    
    _lcd_control( 0x00, 0 ); _lcd_control( 0x20, 1 );   // Return Cursor to home position :  0,0,1,0
}    


//-----------------------------------------------------------------------
// Enable the LCD for direct wire control
//-----------------------------------------------------------------------
int lcd_enable( int DB7, int DB6, int DB5, int DB4, int EN, int RS)
{

  // first save the 6 lcd pins for use in this function and 
  _lcd_DB7 = DB7;
  _lcd_DB6 = DB6;
  _lcd_DB5 = DB5;
  _lcd_DB4 = DB4;
  _lcd_EN  = EN;
  _lcd_RS  = RS;
  __dirout(_lcd_DB7);
  __dirout(_lcd_DB6);
  __dirout(_lcd_DB5);
  __dirout(_lcd_DB4);
  __dirout(_lcd_EN);
  __dirout(_lcd_RS);
  
  
  _lcd_mode = 6;
  _lcd_enable();

}

//-----------------------------------------------------------------------
// Enable the LCD for reduced 2 wire control
// Using the 2-wire mode requires the user to connect to the LCD with a shift-register
// and the MSP430 is connected to the shift-register using the Data and Clock signals
//-----------------------------------------------------------------------
int lcd2w_enable( int DATA, int CLOCK)
{

  // first save the 6 lcd pins for use in this function and 
  _lcd_DATA = DATA;
  _lcd_CLOCK = CLOCK;
  __dirout(_lcd_DATA);
  __dirout(_lcd_CLOCK);
  
  _lcd_mode = 2;
  _lcd_enable();

}


///////////////////////////////////////////////////////////////////////
int _lcd_enable()
// function to enable the 6wire lcd interface
{



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


///////////////////////////////////////////////////////////////////////
#ifdef MPY_ADC
int adc(int pin) {
//    if ((pin & 15) > 7) { ADC10CTL0 |= (REFON | REF2_5V); } // turn on the Ref generator for the Temp sensor (shouldn't need to do this!)
    ADC10CTL1 = (pin & 15) << 12;
    ADC10AE0  = (1 << (pin & 15)) & 255;
    ADC10CTL0 |= ENC + ADC10SC;     // Start A/D conversion
    while (ADC10CTL1 & BUSY);       // Wait if ADC10 core is active
//    if ((pin & 15) > 7) { ADC10CTL0 &= ~(REFON | REF2_5V); }  // turn off the reference
    ADC10CTL0 &= ~ENC;
    return ADC10MEM; }              // return the result
#endif

int   random( int  S ) { 
          S = ( ( (S>>1) * (-18121) ) + 359 ) ; 
          return S ; } 


// wait a dly number of milliseconds, negative dly values are made positive
void  wait( int  dly ) { int i ; int k ; 
          if (dly < 0) { dly = - dly; }
          for ( i = 0 ; i < dly ; i = i + 1 ) { 
              for ( k = 0 ; k < 280 ; k = k + 1 ) { 
                  _NOP ( ) ; } } } 

static void __inline__ wait_cycles(register unsigned int n)
{
    __asm__ __volatile__ (
		"1: \n"
		" dec	%[n] \n"
		" jne	1b \n"
        : [n] "+r"(n));
}

// enter an infinite loop which 
void  halt(void) { 
          for ( ; ;  ) { 
                  _NOP ( ) ; } }  

// map command to map a value (val) from one range (ri1->ri2) to another range (ro1->ro2)
//    return (ro1 + (  ((val-ri1)*(ro2-ro1)) /(ri2-ri1)))
int   map( int val, int ri1, int ri2, int ro1, int ro2    ) { 
          long tmpl;
          tmpl = (((long)val-(long)ri1)*((long)ro2-(long)ro1))/((long)ri2-(long)ri1);
          return (ro1 + (int)tmpl);
          }

// limit command that limits the range a value can have
int   limit( int val, int lim1, int lim2 ) {

            if (lim2 > lim1) {
                if (val > lim2)
                    return lim2;
                else if (val < lim1)
                    return lim1; }
            else {
                if (val > lim1)
                    return lim1;
                else if (val < lim2)
                    return lim2; }
          }


///////////////////////////////////////////////////////////////////////
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
              print_hex( func, ival, 4 );
              break;
          case 'b':
              ival = va_arg(ap, int);
              print_hex( func, ival, 1 );
              break;

          case 's':
              sval = va_arg(ap, char *);
              print_str( func, sval);
              break;
       }
   }
   va_end(ap);
}


///////////////////////////////////////////////////////////////////////
void print_str( int (*func)(int), char *string)
{
    unsigned int __mpy_TxByte;
    while (*string) {
        __mpy_TxByte = *string++;
        (func)(__mpy_TxByte);
    }
}

///////////////////////////////////////////////////////////////////////
void print_hex( int (*func)(int), unsigned int num, unsigned int bit_count)
{
    unsigned int __mpy_TxByte;
    char chr, i, hex_dig; 
    for (i=16; i>0; i=i-bit_count ) {
//        hex_dig =  ((num >> (i-bit_count)) & 0xF); 
        hex_dig =  ((num >> (i-bit_count)) & ((1<<bit_count)-1)); 
        if (hex_dig >= 10) hex_dig += 7;
        __mpy_TxByte = 48 + hex_dig;   
        (func)(__mpy_TxByte);
    }
}

///////////////////////////////////////////////////////////////////////
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



///////////////////////////////////////////////////////////////////////
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

    // if char count is past the last character of the display the reset it 
    if (_lcd_char_count >= 80) { _lcd_char_count == 0; }
    

    // Clear the display and reset position to 0 when we are doing the first character
    if (_lcd_char_count == 0) { _lcd_clear(); }  
    
    // Move the char position on to 40 if we are at the end of the first 16 char line
    if (_lcd_char_count >= 16 && _lcd_char_count < 64 ) { 
       _lcd_char_count = 64;
       _lcd_control( 0xC0, 1 ); _lcd_control( 0x00, 1 );  // set GGRAM address to 64 which is the start of the 2nd line
    }
    
    if (value != 10)  // end of line will reset the char count and clear the display for the next print
    {
//        __out(_lcd_RS, 1);
        _lcd_4bit_write( value, 1 );        // bits 7-4 are written as is
        _lcd_4bit_write( value << 4, 1 );   // bits 3-0 shifted into bit possitions 7-4, all other bits are ignored
        _lcd_char_count += 1;
    } else {
        _lcd_char_count = 0;    
    }
}
///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////


//  Tone

int tone( int portpin, int note_period_us, int note_duration_ms, int note_value, int note_volume ) {
//  Outputs a tone on the output pin portpin. A speaker can be connected to the
//  portpin to hear the tone.
//  The tone frequency is controlled by adjusting the note_period parameter
//  period (the wider the pulse width the
//  louder the tone)
//  The duration is controlled by counting the number of periods
//  @param portpin           Pin number used for the audio output
//  @param note_period_us    Period of the output note tone (in us)
//  @param note_duration_ms  Duration of the tone (in ms)
//  @param note_value        How long the note is on within the note_duration (0-100)
//  @param note_volume       Volume of the tone, adjusts the pulse width
//                           thus increasing the energy of the pulse, 0-100


    int loop_period = (note_period_us - 156)/3;


    // note_value of 0 is a 1/4 of beat
    int cycles_total =  (int)( ((long)note_duration_ms * 1000) / (long)note_period_us );
    int cycles_on    =  (int)( ((long)cycles_total * (long)note_value)/100);
    int cycles_off   =  cycles_total - cycles_on;

    if (note_volume == 0) {
        cycles_on = -1;
        cycles_off = cycles_total;
        note_volume = 1;
    }

    int on_count  = note_volume;
    int off_count = loop_period - on_count;

    // initialize the port, (TDB remove, or subtract time from note_duration)
    __dirout( portpin );
    __out( portpin, 0 );

    // calculate on period_on_time,  period_off_time, and num_cycles
    int cycle_count = 0;

    while (cycle_count < cycles_on) {
         __out( portpin, 1 );
         wait_cycles( on_count);
         __out( portpin, 0 );
         wait_cycles( off_count);
         cycle_count++;
    }

    cycle_count = 0;
    while (cycle_count < cycles_off) {
         __out( portpin, 0 );
         wait_cycles( on_count);
         __out( portpin, 0 );
         wait_cycles( off_count);
         cycle_count++;
    }

    return on_count;
}

///////////////////////////////////////////////////////////////////////////
int playnote( int portpin, int note, int key, int accidental, int octave, int note_width, int duration_ms, int volume ) {
///  Plays a single note from a tune.
//  @param portpin           Pin number used for the audio output
//  @param char note         The note to be played, character 'A' to 'G'
//  @param accidental        Whether the note is a Flat or Sharp, flat is -1, sharp is +1
//  @param octave            The octave of the note from 1 to 9
//  @param note_length_ms    The length of the note
//  @param note_width        quiet is 0, stacatto is 25, normal (quaver) is 50, notes running together 100
//
//  The note and accidental are used as the index into table of musical note
//  frequency periods which is used together with the scale to calculate the
//  period in uS for the note


    // Note Time Period list for a full octave of 12 notes including the sharps
    // from 'C C# D D# ... A# B'
    // (These periods were calculated using a spreadsheet and scaled so that the
    // first value is the largest value that can fit into a 16 bit int variable.
    // This allows the values to be divided by two multiple times to get the
    // higher octaves while minimizing the rounding errors)
    int note_period_list[]  = {
        32107,
        30305,
        28604,
        26999,
        25483,
        24053,
        22702,
        21428,
        20226,
        19090,
        18019,
        17008         };

    // Index into the note_period_list. The note character specified is mapped
    // to an index of the note_period_list table.
    //                  A   B   C   D   E   F   G
    char note_idx[] = { 9,  11, 0,  2,  4,  5,  7 };

    //Modify the note depending on the Key
    if (accidental == 0 &&
        (( key == 'G' && ( note == 'F' )) ||
         ( key == 'D' && ( note == 'F' || note == 'C' )) ||
         ( key == 'A' && ( note == 'F' || note == 'C' || note == 'G' )) ||
         ( key == 'E' && ( note == 'F' || note == 'C' || note == 'G' || note == 'D')) ||
         ( key == 'B' && ( note == 'F' || note == 'C' || note == 'G' || note == 'D' || note == 'A' )))
        ){
        accidental = 1;
    }
    if (accidental == 0 &&
        (( key == 'd' && ( note == 'B' )) ||
         ( key == 'g' && ( note == 'B' || note == 'E' )) ||
         ( key == 'c' && ( note == 'B' || note == 'E' || note == 'A' )) ||
         ( key == 'f' && ( note == 'B' || note == 'E' || note == 'A' || note == 'D')))
        ){
        accidental = -1;
    }

    if (accidental == 99) { accidental = 0; }

    // The accidental value (sharp or flat) is used to increment the position in the table
    char idx = note_idx[ (char)note - 'A' ] + (char)accidental;
    // The base period is read and then shifted to the right by the octave number
    int period = note_period_list[ idx ] >> octave;


    tone(portpin, period, duration_ms, note_width, volume );

}

//////////////////////////////////////////////////////////////////////////
//
int playtune( int portpin, char *tune_str, int note_duration_ms ) {
//
//  Plays a tune specified in tune_str on a speaker attached to portpin.
//  The format for the tune_str loosely based on ABC notation
//  where each note is described by a sequence of note letters and various
//  other characters for sharps, flats, octave, and note duration
// (see  http://abcnotation.com/wiki/abc:standard:v2.1#the_tune_body )
//
//  @param portpin           Pin number used for the audio output
//  @param char *tune_str    Period of the output note tone (in us)
//  @param note_duration_ms  Default duration for the notes (in ms)

    char note = 0;
    int  octave = 0;
    int  accidental = 0;
    int  note_length;
    int  note_length_num = 1;
    int  note_length_den = 1;
    int  note_width;
    int  note_slur = 0;
    char *ptr, p, pn;
    ptr = tune_str;
    int volume = 1;
    char key = 'C';
    char ignore_rest_of_line = 0;

    // Loop through the tune_str a character at a time collecting all the values
    // needed to describe the note. If the next character is the start of the
    // new note (or the end of the tune_str) then output the current note
    // using the playnote() function
    while (*ptr!=0){

        // read the current and next characters
        p  = *ptr++;
        pn = *ptr;

        // Any of these chacacters are settings that are ignored
        // and causes all characters to the end of the line to be
        // ignored
        if (p == '\n') {
            ignore_rest_of_line = 0;
            continue;
        }
        if (p == '%') {
            ignore_rest_of_line = 1;
        }
        if ((p == 'X' || p == 'T' || p == 'R' || p == 'M' || p == 'L'|| p == 'Q' || p == 'Z') && (pn == ':')) {
            ignore_rest_of_line = 1;
        }
        if (ignore_rest_of_line == 1) { continue; }

        // Look for the Key setting
        // Only single character key signatures are recognised
        // Uppercase is a major key, lowercase a minor key.
        if (p == 'K') {
           key = 0;
           continue;
        }
        if (key == 0 && p == ':') {
           key = 1;
           continue;
        }
        if (key == 1 && ((p >= 'A' && p <= 'G') || (p >= 'a' && p <= 'g')) ) {
           key = p;
           ignore_rest_of_line = 1;
           continue;
        }




        // Count of the number of flat or sharp characters, (they can be stacked)
        if (p == '_') { accidental--; }
        if (p == '^') { accidental++; }
        if (p == '=') { accidental == 99; }

        // A note character
        if (p >= 'A' && p <= 'G') {
            note = p;
            octave = 3;
        }

        // A note chacter of the next scale up
        if (p >= 'a' && p <= 'g') {
            note = p - ('a'-'A');      // change the note back to uppercase
            octave = 4;                // and set the octave one higher
        }

        // A rest character has a note of 'A' but the note_width is set to 0
        // to make it not sound
        if (p == 'z' || p == 'x' || p == 'Z' || p == 'X') {
            note = 'A';
            note_width = 0;
        }

        // Stocatto shorttens the note_width
        if (p == '.') {
            note_width = 25;
        }

        // '(' and ')' starts and stops the slurring of notes so there is no gap
        // between them. Which is the same as making the note_width 100.
        if (p == '(') {
            note_slur = 100;
        }
        if (p == ')') {
            note_slur = 0;
        }

        // Increment or decrement the octave (they can be stacked)
        if (p == ',' ) { octave--; }
        if (p == '\'') { octave++; }

        // Modify the note length, look for  N/D characters
        // look for the numerator before the '/', by itself it denotes a half value
        if (p == '/') { note_length_den = 2; }
        if (p >='0' && p <= '9') {
            if (note_length_den == 2){
                note_length_den = (int)(p-'0');
            } else {
                note_length_num  = (int)(p-'0');
            }
        }

        // If we have a note to play and the next
        // character is another note or the end of the string
        // then play the current note
        if (note != 0 && (pn == 0 || pn == '_' || pn == '^' || pn == '=' || pn == 'z' ||  pn == '.' ||
            (pn >= 'A' && pn <= 'G') ||
            (pn >= 'a' && pn <= 'g') )) {

            // If we are slurring the notes make the note_width 100%
            if (note_slur == 100 && note_width == 50) {
                note_width = 100;
            }

            note_length = note_duration_ms * note_length_num / note_length_den;
            playnote( portpin, note, key, accidental, octave, note_width, note_length, volume);

            // Set up the defaults for the next note
            note = 0;
            accidental = 0;
            note_length_num = 1;
            note_length_den = 1;
            note_width = 50;
        }
    }
}

//---------------------------------------------------------------------------
void interrupt_setup( int portpin_intr, int param, int (*func)(int) )
// Sets up an interrupt for either IO, USCI Aurt mode, Watchdog timer
// The portpin paramter is used to define which of the interrupt are to be used.
// If the portpin_intr matches a normal portpin value then an IO interrupt is setup
// otherwise the interrupt is setup for one of the other peripheral types (watchdog_timer or uart)
// The func argument is unused, but it is used by mpy2c to associate this 
// interrupt with an ISR function.
//
// param specifies the type of interrupt, 
// for IO interrrupt   param=Edge Select
//          0= Rising Edge
//          1= Falling Edge
// for USCI Uart       param=Baudrate
// for Watchdog timer  param=Timer interval
{

  // First setup the IO interrupts for port 1 and port 2
  if (portpin_intr & 0x10)
  {
      P1IFG   &=  ~(1 << (portpin_intr & 15));    // Clear the interrupt flag for this bit 
      if (param == 0)                             // Setup the edge select
        P1IES &=  ~(1 << (portpin_intr & 15));    // Clear the bit for a Rising low-to-high transition
      else 
        P1IES |=   (1 << (portpin_intr & 15));    // Set the bit for a Falling high-to-low transition
      P1IE    |=   (1 << (portpin_intr & 15));    // Finally set the enable bit
  }
  else if (portpin_intr & 0x20 )
  {  
      P2IFG   &=  ~(1 << (portpin_intr & 15));     // Clear the interrupt flag for this bit 
      if (param == 0)                              // Setup the edge select
        P2IES &=  ~(1 << (portpin_intr & 15));     // Clear the bit for a Rising low-to-high transition
      else 
        P2IES |=   (1 << (portpin_intr & 15));    // Set the bit for a Falling high-to-low transition
      P2IE    |=   (1 << (portpin_intr & 15));    // Finally set the enable bit
  }
  else if (portpin_intr == 2) 
  {   // initialize the USCI uart  (taken from TI examples) Requires USCI peripheral as in the msp430g2xx3 devices 
#ifdef MPY_USCI
      P1SEL = BIT1 + BIT2 ;                     // P1.1 = RXD, P1.2=TXD
      P1SEL2 = BIT1 + BIT2 ;                    // P1.1 = RXD, P1.2=TXD
      UCA0CTL1 |= UCSSEL_2;                     // SMCLK
      UCA0BR0 = 104;                            // 1MHz 9600
      UCA0BR1 = 0;                              // 1MHz 9600
      UCA0MCTL = UCBRS0;                        // Modulation UCBRSx = 1
      UCA0CTL1 &= ~UCSWRST;                     // **Initialize USCI state machine**
      IE2 |= UCA0RXIE;                          // Enable USCI_A0 RX interrupt
#endif
  }
  // Setup the watchdog as an interval timer
  else if (portpin_intr == 1) 
  { 
      BCSCTL3 = LFXT1S_2;
      WDTCTL = param;  //~30mS intervals
      IE1 |= WDTIE;    //enable interrupt
//      _BIS_SR(LPM0_bits + GIE);
  }
}


//---------------------------------------------------------------------------
int interrupt_clear( int portpin_intr)
// clear the interrupt flag for thegiven extended portpin
{
  int flag;
  // First setup the IO interrupts for port 1 and port 2
  if (portpin_intr & 0x10)
  {   
      flag = ((P1IFG & (1 << (portpin_intr & 15))) >> (portpin_intr & 15));
      P1IFG  &=   ~(1 << (portpin_intr & 15));     // Clear the interrupt flag for this bit 
  }
  else if (portpin_intr & 0x20 )
  {
      flag = ((P2IFG & (1 << (portpin_intr & 15))) >> (portpin_intr & 15));
      P2IFG &=    ~(1 << (portpin_intr & 15));     // Clear the interrupt flag for this bit 
  }

  return( flag );
}



//---------------------------------------------------------------------------
void interrupt_disable( int portpin_intr)
// 

{
  // First setup the IO interrupts for port 1 and port 2
  if (portpin_intr & 0x10)
  {
      P1IE   &=   ~(1 << (portpin_intr & 15));    // Clear the enable bit
  }
  else if (portpin_intr & 0x20 )
  {
      P2IE  &=    ~(1 << (portpin_intr & 15));    //  Clear the enable bit
  }
  else if (portpin_intr == 2) 
  {  
#ifdef MPY_USCI
      IE2 &= ~UCA0RXIE;                          // Disable USCI_A0 RX interrupt  }
#endif
  }
  else if (portpin_intr == 1)  
  { 
      IE1 &= ~WDTIE;                            // Disable Watchdog interrupt
  }
}

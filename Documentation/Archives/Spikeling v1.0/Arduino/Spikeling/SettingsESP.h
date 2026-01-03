// -----------------------------------------------------------------------------
// Settings for the following ESP boards:
// 1) Wemos D1 Pro Board (ESP8266)
//    https://wiki.wemos.cc/products:d1:d1_mirni_pro
//    as the version used in the Thingpulse ESP8266 WiFi Color Display Kit 2.4″,
//    see https://thingpulse.com/product/esp8266-wifi-color-display-kit-2-4/
//    IMPLEMENTATION INCOMPLETE
//
// 2) Adafruit HUZZAH32 Feather Board (ESP32)
//    https://www.adafruit.com/product/3405
//    in combination with the Adafruit 2.4" TFT FeatherWing,
//    see https://learn.adafruit.com/adafruit-2-4-tft-touch-screen-featherwing
//
// Libraries (to be installed via Arduino IDE/Library manager:
// - "Mcp3208" by Patrick Rogalla, v1.0.2
// - "Adafruit_STMPE610" by Adafruit, v1.0.1
// - "Mini Grafx" by Daniel Eichhorn, v1.0.0
//   (contains a driver for the ILI9341 TFT spi display)
// - "Mcp23s08" by sumotoy (https://github.com/sumotoy/gpio_expander)
//   adapted by Thomas Euler
//
// -----------------------------------------------------------------------------
//#define USES_FAST_ADC
//#define USES_PLOTTING
//#define USES_FULL_REDRAW
#define   USES_HOUSEKEEPING
#define   USES_DAC

#include "Definitions.h"
#include <SPI.h>
#include "MiniGrafx.h"
#include "ILI9341_SPI.h"
#include <Adafruit_STMPE610.h>
#include <Mcp3208.h>
#include <Mcp23s08.h>

// -----------------------------------------------------------------------------
#define   MCP3208_FIRST  100
#define   MCP3208_LAST   107
#define   MCP23S08_FIRST 110
#define   MCP23S08_LAST  117

// -----------------------------------------------------------------------------
// Pin definitions (simulation-related)
// -----------------------------------------------------------------------------
#ifdef ESP8266
  #define PhotoDiodePin -1  //              Photodiode
  #define LEDOutPin     -2  //              LED
  #define ButtonPin     -3  //              Push button to switch spike modes
  #define VmPotPin      -4  //              Resting membrane potential
  #define Syn1PotPin    -5  //              efficacy synapse 1
  #define Syn2PotPin    -6  //              efficacy synapse 2
  #define NoisePotPin   -7  //              scaling of Noise level
  #define DigitalIn1Pin -8  //              Synapse 1 Input - expects 5V pulses
  #define DigitalIn2Pin -9  //              Synapse 2 input - expects 5V pulses
  #define AnalogInPin   -10 //              Analog in- takes 0-5V (positive only)
  #define DigitalOutPin -11 //              "Axon" - generates 5V pulses
  #define AnalogOutPin  -12 //              Analog out for full spike waveform
  #define DACOutPin     -13 // NEW          Analog out for full spike waveform (analog)
  #define HousekeepLED  -14 // NEW

  // Digital and analog I/O helper macros
  //
  #define pinModeHelper(pin, mode)          pinModeNew(pin, mode)
  #define digitalReadHelper(pin)            digitalReadNew(pin)
  #define digitalWriteHelper(pin, val)      digitalWriteNew(pin, val)
  #define analogReadHelper(pin)             analogReadNew(pin)
  #define analogWriteHelper(pin, val)       analogWriteNew(pin, val)
  #define dacWriteHelper(pin, val)          dummy(pin, val)
#endif
#ifdef ESP32
  #define PhotoDiodePin  MCP3208_FIRST+2    // -> A0       Photodiode
  #define LEDOutPin      21                 // -> D9/PWM   LED
  #define ButtonPin      MCP23S08_FIRST+1   // -> 2        Push button to switch spike modes
  #define VmPotPin       MCP3208_FIRST+0    // -> A3       Resting membrane potential
  #define Syn1PotPin     MCP3208_FIRST+3    // -> A7       efficacy synapse 1
  #define Syn2PotPin     MCP3208_FIRST+4    // -> A5       efficacy synapse 2
  #define NoisePotPin    MCP3208_FIRST+1    // -> A6       scaling of Noise level
  #define DigitalIn1Pin  MCP23S08_FIRST+2   // -> 4        Synapse 1 Input - expects 5V pulses
  #define DigitalIn2Pin  MCP23S08_FIRST+3   // -> 5        Synapse 2 input - expects 5V pulses
  #define AnalogInPin    MCP3208_FIRST+5    // -> A2       Analog in- takes 0-5V (positive only)
  #define DigitalOutPin  16                 // -> D3/DO    "Axon" - generates 5V pulses
  #define AnalogOutPin   17                 // -> D11/PWM  Analog out for full spike waveform
  #define DACOutPin      A0                 // NEW         Analog out for full spike waveform (analog)
  #define HousekeepLED   MCP23S08_FIRST+0   // NEW

  // Digital and analog I/O helper macros
  //
  #define pinModeHelper(pin, mode)      pinModeNew(pin, mode)
  #define digitalReadHelper(pin)        digitalReadNew(pin)
  #define digitalWriteHelper(pin, val)  digitalWriteNew(pin, val)
  #define analogReadHelper(pin)         analogReadNew(pin)
  #define analogWriteHelper(pin, val)   analogWriteNew(pin, val)
  #define dacWriteHelper(pin, val)      dacWrite(pin, val)

  // NOTES:
  // (1) analogWrite() is not implemented in the ESP32, therefore use ledcXXX()
  //     functions instead. This requires an LED channel ID (0..15), a frequency
  //    (not sure what unit that is ...) and a bit depth (up to 16 bits)
  //    https://github.com/espressif/arduino-esp32/blob/a4305284d085caeddd1190d141710fb6f1c6cbe1/cores/esp32/esp32-hal-ledc.c
  //
  #define LEDOut_LEDCh     0
  #define LEDOut_Freq      31250
  #define LEDOut_Bits      8
  #define AnalogOut_LEDCh  1
  #define AnalogOut_Freq   LEDOut_Freq
  #define AnalogOut_Bits   LEDOut_Bits
  //
  // (2) analogReadNew() uses the 8-channel ADC MCP3208; therefore instead of
  //     pins, the mapping to the ADC channels on the chip are defined above,
  //     It's a 12 bit ADC, therefore the results need to be divided by 4.
  //     The MCP3208 is connected to the second SPI bus of the ESP (HSPI), while
  //     the TFT display uses the primary SPI bus (VSPI). This is nescessary to
  //     be able to run the TFT at a particular frequency, at which the MCP3208
  //     does not seem to work reliable.
  //     For pins, see "hardware add-ons" section further below.
#endif

// Serial out
// (115200=testing; 921600=standard; 1843200=a bit faster but less stable)
//
#define SerOutBAUD  921600

// -----------------------------------------------------------------------------
// Pin definitions (hardware add-ons)
// -----------------------------------------------------------------------------
#ifdef ESP8266
  #define TFT_DC    D2
  #define TFT_CS    D1
  #define TFT_LED   D8
  #define TOUCH_CS  D3
  #define TOUCH_IRQ D4
  ADC_MODE(ADC_VCC);
#endif
#ifdef ESP32
  #define TFT_DC    33
  #define TFT_CS    15       // primary SPI bus (VSPI), client #1
  #define TOUCH_CS  32       // primary SPI bus (VSPI), client #2
  #define ADC_MISO  23       // secondary SPI bus (HSPI) ...
  #define ADC_MOSI  22
  #define ADC_SCK   27
  #define ADC_CS    13       // secondary SPI bus (HSPI), client #1
  #define DIO_CS    4        // secondary SPI bus (HSPI), client #2
  #define DIO_ADDR  0x20     // address of MCP23S08 (defined by A0,A1 pins)
  #define DIO_INT   36       // interrupt pin of MCP23S08 (not yet used)
  #define ADC_VREF  5000     // Vref for A/D
  #define ADC_CLK   1600000  // secondary SPI bus (HSPI), clock
//#define ADC_CLK   4000000  // secondary SPI bus (HSPI), clock

#endif

// Define colors usable in the paletted 16 color frame buffer
//
uint16_t palette[] = {ILI9341_BLACK, // 0
                      ILI9341_WHITE, // 1
                      ILI9341_NAVY, // 2
                      ILI9341_DARKCYAN, // 3
                      ILI9341_DARKGREEN, // 4
                      ILI9341_MAROON, // 5
                      ILI9341_PURPLE, // 6
                      ILI9341_OLIVE, // 7
                      ILI9341_LIGHTGREY, // 8
                      ILI9341_DARKGREY, // 9
                      ILI9341_BLUE, // 10
                      ILI9341_GREEN, // 11
                      ILI9341_CYAN, // 12
                      ILI9341_RED, // 13
                      ILI9341_MAGENTA, // 14
                      ILI9341_YELLOW}; // 15

const int SCREEN_WIDTH    = 320;
const int SCREEN_HEIGHT   = 240;
const int BITS_PER_PIXEL  = 4; // 2^4 = 16 colors
const int FONT_HEIGHT     = 14; // Standard font
#ifdef ESP8266
  const int SCREEN_ORIENT = 3;
#endif
#ifdef ESP32
  const int SCREEN_ORIENT = 1;
#endif

// Initialize the drivers
//
ILI9341_SPI       tft     = ILI9341_SPI(TFT_CS, TFT_DC);
MiniGrafx         gfx     = MiniGrafx(&tft, BITS_PER_PIXEL, palette);
Adafruit_STMPE610 ts      = Adafruit_STMPE610(TOUCH_CS);
#ifdef ESP32
  SPIClass        *hspi   = new SPIClass(HSPI);
  MCP3208         adc(ADC_VREF, ADC_CS, hspi);
  uint16_t        ADCData[8][2];
  MCP23S08        dio(DIO_CS, DIO_ADDR, 0, hspi);
  uint8_t         DIOData;
#endif

// Definitions and variables for plotting
//
#define INFO_DY      20  // Height of info panel
#define MAX_TRACES   3   // Maximal number of traces shown in parallel
#define MAX_VALUES   320 // Maximal trace length
#define PLOT_UPDATE  16  // Redraw screen every # values

const char* OutputInfoStr[] = {"V_m[mV]", "I_t[pA]", "I_PD[pA]", "I_AI[pA]",
                               "I_Sy[pA]", "StmSt", "SpIn1", "SpIn2",
                               "t[us]"};

int    TraceCols[MAX_TRACES] = {13,11,15};
int    Traces[MAX_TRACES][MAX_VALUES];
int    TracesStrIndex[MAX_TRACES];
int    TraceSet;
float  TracesMinMax[MAX_TRACES][2];
int    iPnt, dyPlot, dxInfo;
char   timeStr[16];
bool   stateHousekeepingLED;

// -----------------------------------------------------------------------------
// Other hardware-related definitions
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------
void setTraceSet()
{
  switch(TraceSet) {
    case 0:
    default:
      TracesStrIndex[0]  = ID_V;
      TracesMinMax[0][0] = -110;
      TracesMinMax[0][1] = 25;
      TracesStrIndex[1]  = ID_I_TOTAL;
      TracesMinMax[1][0] = -250;
      TracesMinMax[1][1] = 250;
      TracesStrIndex[2]  = ID_I_STIM_STATE;
      TracesMinMax[2][0] = -50;
      TracesMinMax[2][1] = 50;
  }
}


void initializeHardware()
{
  #ifdef ESP8266
    // Turn on the background LED of TFT
    //
    pinMode(TFT_LED, OUTPUT);
    digitalWrite(TFT_LED, HIGH);

    // Set pins
    //
    // ...
  #endif
  #ifdef ESP32
    // Set pins
    //
    pinMode(DigitalOutPin, OUTPUT);
    ledcSetup(LEDOut_LEDCh, LEDOut_Freq, LEDOut_Bits);
    ledcAttachPin(LEDOutPin, LEDOut_LEDCh);
    ledcSetup(AnalogOut_LEDCh, AnalogOut_Freq, AnalogOut_Bits);
    ledcAttachPin(AnalogOutPin, AnalogOut_LEDCh);

    // Initialize SPI interface for MCP3208 and MCP23S08
    //
    pinMode(ADC_CS, OUTPUT);
    digitalWrite(ADC_CS, HIGH);
    pinMode(DIO_CS, OUTPUT);
    digitalWrite(DIO_CS, HIGH);
    SPISettings settingsHSPI(ADC_CLK, MSBFIRST, SPI_MODE0);
    hspi->begin(ADC_SCK, ADC_MISO, ADC_MOSI, ADC_CS);
    hspi->beginTransaction(settingsHSPI);
    for(int i=0; i<8; i++) {
      ADCData[0][0] = 0;
      ADCData[0][1] = 0;
    }
    dio.begin();
    dio.gpioPinMode(ButtonPin -MCP23S08_FIRST, INPUT);
    dio.gpioPinMode(DigitalIn1Pin -MCP23S08_FIRST, INPUT);
    dio.gpioPinMode(DigitalIn2Pin -MCP23S08_FIRST, INPUT);
    dio.gpioPinMode(HousekeepLED -MCP23S08_FIRST, OUTPUT);
    DIOData = 0;
  #endif

  // Initialise a few variables
  //
  stateHousekeepingLED = false;
  iPnt = 0;
  dyPlot = SCREEN_HEIGHT -INFO_DY;
  dxInfo = SCREEN_WIDTH /(MAX_TRACES +1);
  timeStr[0] = 0;
  for(int i=0; i<MAX_TRACES; i++) {
    TracesMinMax[i][0] = 0;
    TracesMinMax[i][1] = 0;
  }
  TraceSet = 0;
  setTraceSet();

  // Set rotation and clear screen
  // (landscape, USB port up)
  //
  gfx.init();
  gfx.setRotation(SCREEN_ORIENT);
  gfx.setFastRefresh(true);
  gfx.fillBuffer(0);
  gfx.setTextAlignment(TEXT_ALIGN_CENTER);
  gfx.commit();
}

// -----------------------------------------------------------------------------
void dummy(int x, int y)
{}


void pinModeNew(int pin, int mode)
{}


void digitalWriteNew(uint8_t pin, bool val)
{
  if((pin >= MCP23S08_FIRST) && (pin <= MCP23S08_LAST)) {
    // Handle output pins connected to the port expander MCP23S08
    //
    #ifdef USES_HOUSEKEEPING
    dio.gpioDigitalWriteFast(pin -MCP23S08_FIRST, val);
    #else
    dio.gpioDigitalWrite(pin -MCP23S08_FIRST, val);
    #endif
  }
  else {
    // Handle directly to the ESP connected pins
    //
    switch(pin) {
      case DigitalOutPin:
        digitalWrite(pin, val);
        break;
    }
  }
}


void analogWriteNew(int pin, int val)
{
 #ifdef ESP32
    switch(pin) {
      case LEDOutPin:
        ledcWrite(LEDOut_LEDCh, val);
        break;
      case AnalogOutPin:
        ledcWrite(AnalogOut_LEDCh, val);
        break;
    }
  #endif
}


int digitalReadNew(uint8_t pin)
{
  if((pin >= MCP23S08_FIRST) && (pin <= MCP23S08_LAST)) {
    // Currently only input pins connected to the port expander
    // MCP23S08 are handled
    //
    #ifdef USES_HOUSEKEEPING
    return (DIOData & 0x01 << (pin -MCP23S08_FIRST)) > 0 ? HIGH : LOW;
    #else
    return dio.gpioDigitalRead(pin -MCP23S08_FIRST) > 0 ? HIGH : LOW;
    #endif
  }
  return LOW;
}


int analogReadNew(int pin)
{
  uint16_t res = 0;

  if((pin >= MCP3208_FIRST) && (pin <= MCP3208_LAST)) {
    // Currently only input pins connected to A/D IC MCP3208 are handeled
    //
    switch (pin) {
      case Syn1PotPin:
        res = 300;
        break;
      case Syn2PotPin:
        res = 128;
        break;
      case AnalogInPin:
        res = 100;
        break;

      default:
        #ifdef USES_HOUSEKEEPING
        res = ADCData[pin -MCP3208_FIRST][1] >> 2;
        #else
        // *** TODO ***
        #endif
    }
  }
  return res;
}

// -----------------------------------------------------------------------------
// Housekeeping routine, to be called once per loop
// -----------------------------------------------------------------------------
void housekeeping()
{
  uint16_t v;
  uint8_t  iCh;

  // Read A/D channels from MCP3208 and store data
  //
  for(iCh=0; iCh<3; iCh++) {
    v  = adc.read(MCP3208::Channel(iCh | 0b1000));
    if((v > 4066) || (v < 30)) {
      ADCData[iCh][1] = ADCData[iCh][0];
    }
    else {
      ADCData[iCh][0] = v;
      ADCData[iCh][1] = v;
    }
   }

   // Flash housekeeping LED, if defined
   //
   #ifdef HousekeepLED
   digitalWriteNew(HousekeepLED, stateHousekeepingLED);
   stateHousekeepingLED = !stateHousekeepingLED;
   #endif

   // Refresh MCP23S08 and retrieve data
   //
   DIOData = dio.readGpioPort();
   dio.gpioPortUpdate();
}

// -----------------------------------------------------------------------------
// Graphics
// -----------------------------------------------------------------------------
int getYCoord(int iTr, float v)
{
  // Convert the value into a coordinate on the screen
  //
  return SCREEN_HEIGHT -1 -map(round(v), TracesMinMax[iTr][0], TracesMinMax[iTr][1], 0, dyPlot);
}


void plot(output_t* Output)
{
  int y, iTr;

  // Depending on selected trace set, add data to trace array
  //
  switch(TraceSet) {
    case 0:
    default:
      Traces[0][iPnt] = getYCoord(0, Output->v);
      Traces[1][iPnt] = getYCoord(1, Output->I_total);
      Traces[2][iPnt] = getYCoord(2, Output->Stim_State);
  }

  // Draw new piece of each trace
  //
  if(iPnt > 0) {
    #ifndef USES_FULL_REDRAW
      gfx.setColor(0);
      gfx.drawLine(iPnt, 0, iPnt, dyPlot);
    #endif
    for(iTr=0; iTr<MAX_TRACES; iTr++) {
      gfx.setColor(TraceCols[iTr]);
      gfx.drawLine(iPnt-1, Traces[iTr][iPnt-1], iPnt, Traces[iTr][iPnt]);
    }
  }

  iPnt++;
  if(iPnt >= MAX_VALUES) {
    // Set trace data pointer to the beginning of the array and clear screen
    //
    iPnt = 0;
    #ifndef USES_FULL_REDRAW
      gfx.setColor(0);
      gfx.drawLine(0, 0, 0, dyPlot);
    #else
      gfx.fillBuffer(0);
    #endif

    // Redraw info area
    //
    for(iTr=0; iTr<MAX_TRACES; iTr++) {
      gfx.setColor(TraceCols[iTr]);
      gfx.drawString(dxInfo/2 +(iTr+1)*dxInfo +5, dyPlot, OutputInfoStr[TracesStrIndex[iTr]]);
    }
  }
  if((((iPnt-1) % PLOT_UPDATE) == 0) || (iPnt == 0)) {
    // Redraw time and mode
    // (first old string in black, then new string in white; this is much faster then
    //  clearing the info area with a filled rectangle)
    //
    gfx.setColor(0);
    gfx.drawString(dxInfo/2, dyPlot, timeStr);
    sprintf(timeStr, "M%d %.1fs\n", Output->NeuronBehaviour, Output->currentMicros /1E6);
    gfx.setColor(1);
    gfx.drawString(dxInfo/2, dyPlot, timeStr);

    // Commit graph commands
    //
    gfx.commit();
  }
}

// -----------------------------------------------------------------------------

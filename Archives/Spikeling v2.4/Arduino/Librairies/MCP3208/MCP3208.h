/*!
 *  @file MCP3208.h
 *
 *  This is a library for the MCP3208 - 8-Channel 12-Bit ADC with SPI Interface.
 *
 *  Designed to work with MICROCHIP's MCP3208.
 *
 *  These breakout use SPI to communicate, 4 pins are required.
 *  
 *  This code was modified from Adafruit's MCP3008 library, following MIT License:
 *  
 *		Adafruit_MCP3008.h
 *		This is a library for the MCP3008 - 8-Channel 10-Bit ADC with SPI Interface.
 *		Designed specifically to work with the Adafruit MCP3008.
 *		Pick one up today in the adafruit shop!
 *		------> https://www.adafruit.com/product/856
 *		These breakout use SPI to communicate, 4 ping are required.
 *		Adafruit invests time and resources providing this open source code,
 *		please support Adafruit andopen-source hardware by purchasing products
 *		from Adafruit!
 *  
 *	MIT license, all text above must be included in any redistribution
 */

#ifndef MCP3208_h
#define MCP3208_h

#include <Arduino.h>
#include <SPI.h>

#define MCP3208_SPI_MAX_5V 3600000         ///< SPI MAX Value on 5V pin
#define MCP3208_SPI_MAX_3V 1350000         ///< SPI MAX Value on 3V pin
#define MCP3208_SPI_MAX MCP3208_SPI_MAX_3V ///< SPI MAX Value
#define MCP3208_SPI_ORDER MSBFIRST         ///< SPI ORDER
#define MCP3208_SPI_MODE SPI_MODE0         ///< SPI MODE

/*!
 *  @brief  Class that stores state and functions for interacting with
 *          MCP3208 Chip
 */
class MCP3208 {
public:
  bool begin(uint8_t cs = SS, SPIClass *theSPI = &SPI);
  bool begin(uint8_t sck, uint8_t mosi, uint8_t miso, uint8_t cs);
  int readADC(uint8_t channel);
  int readADCDifference(uint8_t differential);

private:
  uint8_t cs;
  uint8_t mosi;
  uint8_t miso;
  uint8_t sck;
  bool hwSPI;
  int SPIxADC(uint8_t channel, bool differential);
  SPIClass *_spi;
};

#endif

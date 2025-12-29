// -----------------------------------------------------------------------------     
#include <stdio.h>
#include <inttypes.h>
#include <SPI.h>
#include <Arduino.h>

#if defined(ESP32) || defined(ESP8622)
#else
  #include <avr/interrupt.h>
#endif  

#include "Mcp23s08.h"

// -----------------------------------------------------------------------------     
MCP23S08::MCP23S08(){
#if defined (SPI_HAS_TRANSACTION)
	_spiTransactionsSpeed = MAXSPISPEED;//set to max supported speed (in relation to chip and CPU)
#else
	_spiTransactionsSpeed = 0;
#endif
}

void MCP23S08::setSPIspeed(uint32_t spispeed){
	#if defined (SPI_HAS_TRANSACTION)
	if (spispeed > 0){
		if (spispeed > MAXSPISPEED) {
			_spiTransactionsSpeed = MAXSPISPEED;
		} else {
			_spiTransactionsSpeed = spispeed;
		}
	} else {
		_spiTransactionsSpeed = 0;//disable SPItransactons
	}
	#else
	_spiTransactionsSpeed = 0;
	#endif
}

//return 255 if the choosed pin has no INT, otherwise return INT number
//if there's support for SPI transactions it will use SPI.usingInterrupt(intNum);
//to prevent problems from interrupt
/*USE:
  int intNumber = mcp.getInterruptNumber(gpio_int_pin);
  if (intNumber < 255){
    attachInterrupt(intNumber, keypress, FALLING);//attack interrupt
  } else {
    Serial.println("sorry, pin has no INT capabilities!");
  }
 */

// ***TE 2018-08-18***
// Disabled because SPI.usingInterrupt() not defined for ESPxxx
/*
int mcp23s08::getInterruptNumber(byte pin) {
	int intNum = digitalPinToInterrupt(pin);
	if (intNum != NOT_AN_INTERRUPT) {
		#if defined (SPI_HAS_TRANSACTION)
			SPI.usingInterrupt(intNum);
		#endif
		return intNum;
	}
	return 255;
}
*/
MCP23S08::MCP23S08(const uint8_t csPin,const uint8_t haenAdrs){
	_spiTransactionsSpeed = 0;
	mSpi = &SPI;
	postSetup(csPin,haenAdrs,&SPI);
}

MCP23S08::MCP23S08(const uint8_t csPin,const uint8_t haenAdrs,uint32_t spispeed){
	postSetup(csPin,haenAdrs,&SPI,spispeed);
}

MCP23S08::MCP23S08(const uint8_t csPin,const uint8_t haenAdrs,uint32_t spispeed,SPIClass *spi){
	postSetup(csPin,haenAdrs,spi,spispeed);
}


void MCP23S08::postSetup(const uint8_t csPin,const uint8_t haenAdrs,SPIClass *spi,uint32_t spispeed){
	#if defined (SPI_HAS_TRANSACTION)
		if (spispeed > 0) setSPIspeed(spispeed);
	#endif
	mSpi = spi;
	_cs = csPin;
	if (haenAdrs >= 0x20 && haenAdrs <= 0x23){//HAEN works between 0x20...0x23
		_adrs = haenAdrs;
		_useHaen = 1;
	} else {
		_adrs = 0;
		_useHaen = 0;
	}
	_readCmd  = (_adrs << 1) | 1;
	_writeCmd = _adrs << 1;
	//setup register values for this chip
	IOCON = 	0x05;
	IODIR = 	0x00;
	GPPU = 		0x06;
	GPIO = 		0x09;
	GPINTEN = 	0x02;
	IPOL = 		0x01;
	DEFVAL = 	0x03;
	INTF = 		0x07;
	INTCAP = 	0x08;
	OLAT = 		0x0A;
	INTCON = 	0x04;
}

void MCP23S08::begin(bool protocolInitOverride) {
	if (protocolInitOverride){
		mSpi->begin();
		#if defined (SPI_HAS_TRANSACTION)
		if (_spiTransactionsSpeed == 0){//do not use SPItransactons
			mSpi->setClockDivider(SPI_CLOCK_DIV4); // 4 MHz (half speed)
			mSpi->setBitOrder(MSBFIRST);
			mSpi->setDataMode(SPI_MODE0);
		}
		#else//do not use SPItransactons
		mSpi->setClockDivider(SPI_CLOCK_DIV4); // 4 MHz (half speed)
		mSpi->setBitOrder(MSBFIRST);
		mSpi->setDataMode(SPI_MODE0);
		#endif
	}	
	pinMode(_cs, OUTPUT);
	digitalWrite(_cs, HIGH);
	delay(100);
	
	_useHaen == 1 ? writeByte(IOCON,0b00101000) : writeByte(IOCON,0b00100000);
	/*
    if (_useHaen){
		writeByte(IOCON,0b00101000);//read datasheet for details!
	} else {
		writeByte(IOCON,0b00100000);
	}
	*/
	_gpioDirection = 0xFF;//all in
	_gpioState = 0x00;//all low 
}


uint8_t MCP23S08::readAddress(byte addr){
	byte low_byte = 0x00;
	startSend(1);
	mSpi->transfer(addr);
	low_byte  = mSpi->transfer(0x0);
	endSend();
	return low_byte;
}


void MCP23S08::gpioPinMode(uint8_t mode){
	if (mode == INPUT){
		_gpioDirection = 0xFF;
	} else if (mode == OUTPUT){	
		_gpioDirection = 0x00;
		_gpioState = 0x00;
	} else {
		_gpioDirection = mode;
	}
	writeByte(IODIR,_gpioDirection);
}


void MCP23S08::gpioPinMode(uint8_t pin, uint8_t mode){
	if (pin < 8){//0...7
		mode == INPUT ? _gpioDirection |= (1 << pin) :_gpioDirection &= ~(1 << pin);
		writeByte(IODIR,_gpioDirection);
	}
}


void MCP23S08::gpioPort(uint8_t value){
	if (value == HIGH){
		_gpioState = 0xFF;
	} else if (value == LOW){	
		_gpioState = 0x00;
	} else {
		_gpioState = value;
	}
	writeByte(GPIO,_gpioState);
}


uint8_t MCP23S08::readGpioPort(){
	return readAddress(GPIO);
}

uint8_t MCP23S08::readGpioPortFast(){
	return _gpioState;
}

int MCP23S08::gpioDigitalReadFast(uint8_t pin){
	if (pin < 8){//0...7
		int temp = bitRead(_gpioState,pin);
		return temp;
	} else {
		return 0;
	}
}

void MCP23S08::portPullup(uint8_t data) {
	if (data == HIGH){
		_gpioState = 0xFF;
	} else if (data == LOW){	
		_gpioState = 0x00;
	} else {
		_gpioState = data;
	}
	writeByte(GPPU, _gpioState);
}




void MCP23S08::gpioDigitalWrite(uint8_t pin, bool value){
	if (pin < 8){//0...7
		value == HIGH ? _gpioState |= (1 << pin) : _gpioState &= ~(1 << pin);
		writeByte(GPIO,_gpioState);
	}
}

void MCP23S08::gpioDigitalWriteFast(uint8_t pin, bool value){
	if (pin < 8){//0...8
		value == HIGH ? _gpioState |= (1 << pin) : _gpioState &= ~(1 << pin);
	}
}

void MCP23S08::gpioPortUpdate(){
	writeByte(GPIO,_gpioState);
}

int MCP23S08::gpioDigitalRead(uint8_t pin){
	if (pin < 8) return (int)(readAddress(GPIO) & 1 << pin);
	return 0;
}

uint8_t MCP23S08::gpioRegisterReadByte(byte reg){
  uint8_t data = 0;
    startSend(1);
    mSpi->transfer(reg);
    data = mSpi->transfer(0);
    endSend();
  return data;
}


void MCP23S08::gpioRegisterWriteByte(byte reg,byte data){
	writeByte(reg,(byte)data);
}

/* ------------------------------ Low Level ----------------*/
void MCP23S08::startSend(bool mode){
#if defined (SPI_HAS_TRANSACTION)
	if (_spiTransactionsSpeed > 0) 
		mSpi->beginTransaction(SPISettings(_spiTransactionsSpeed, MSBFIRST, SPI_MODE0));
#endif
#if defined(__FASTWRITE)
	digitalWriteFast(_cs, LOW);
#else
	digitalWrite(_cs, LOW);
#endif
	mode == 1 ? mSpi->transfer(_readCmd) : mSpi->transfer(_writeCmd);
}

void MCP23S08::endSend(){
#if defined(__FASTWRITE)
	digitalWriteFast(_cs, HIGH);
#else
	digitalWrite(_cs, HIGH);
#endif
#if defined (SPI_HAS_TRANSACTION)
	if (_spiTransactionsSpeed > 0) 
		mSpi->endTransaction();
#endif
}


void MCP23S08::writeByte(byte addr, byte data){
	startSend(0);
	mSpi->transfer(addr);
	mSpi->transfer(data);
	endSend();
}

// -----------------------------------------------------------------------------     

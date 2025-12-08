/***************************************************
Simple example of reading the MCP3208 analog input of
channel 0 and channel 1, and printing the difference.

Author: Rodolfo Prieto Maldonado
License: Public Domain
****************************************************/

#include <MCP3208.h>

MCP3208 adc;

int count = 0;

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("MCP3208 differential test.");

  /// Hardware SPI (specify CS, use any available digital pin)
  /// Can use defaults if available, 
  /// ex: UNO (SS=10), Huzzah (SS=15), Feather 32u4 (SS=17) or M0 (SS=16)
  adc.begin();
  
  /// Specifying the digital pin to use
  //adc.begin(10);  

  /// Software SPI (specify all, use any available digital)
  /// (sck, mosi, miso, cs);
  //adc.begin(13, 11, 12, 10); 
}

void loop() {
  /// 0: Return channel 0 minus channel 1
  /// 1: Return channel 1 minus channel 0
  /// 2: Return channel 2 minus channel 3
  /// 3: Return channel 3 minus channel 2
  /// 4: Return channel 4 minus channel 5
  /// 5: Return channel 5 minus channel 4
  /// 6: Return channel 6 minus channel 7
  /// 7: Return channel 7 minus channel 6
  Serial.print(adc.readADCDifference(0)); Serial.print("\t");

  Serial.print("["); Serial.print(count); Serial.println("]");
  count++;
  
  delay(1000);
}

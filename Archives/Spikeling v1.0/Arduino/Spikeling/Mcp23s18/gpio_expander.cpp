// -----------------------------------------------------------------------------     
#include <stdio.h>
#include <string.h>
#include <inttypes.h>
  #include <Arduino.h>
  
#if defined(ESP32) || defined(ESP8622)
#else
  #include <avr/interrupt.h>
#endif  

#include "gpio_expander.h"

gpio_expander::gpio_expander() 
{
}

// -----------------------------------------------------------------------------     





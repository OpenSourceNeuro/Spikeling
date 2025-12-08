#pragma once  
#include <cstdint>



// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Librairies import                         */ 
                                                                      
#include "Izhikevich_parameters.h"
#include <Arduino.h>
#include <esp_system.h>
#include <SPI.h>
#include <MCP_ADC.h>                                      // Microchip SPI ADC Library by Rob Tillaart                 https://github.com/RobTillaart/MCP_ADC
#include <MCP_DAC.h>                                      // Microchip SPI DAC Library by Rob Tillaart                 https://github.com/RobTillaart/MCP_DAC
#include <Gaussian.h>                                     // Gaussian Library by Ivan Seidel                           https://github.com/ivanseidel/Gaussian
#include <SerialCommand.h>                                // SerialCommand Library by Shyd (based on Steven Cogswell)  https://github.com/shyd/Arduino-SerialCommand


// // // // // // // // // // // // // // // // // // // // // // // //
/*                              Timing                               */
struct Timing {
  uint32_t current_us;
  uint32_t lastStep_us;
  uint32_t step_us;
};
inline Timing timing{
 .current_us  =  0,
 .lastStep_us =  0,
 .step_us     = 3000
};

// // // // // // // // // // // // // // // // // // // // // // // //
/*                        Serial parameters                          */

const float V_SCALE     = 100.0f;                         // 2 decimal places for voltages
const float I_SCALE     = 100.0f;                         // 2 decimal places for currents
const float SYN_V_SCALE = 1.0f;                           // Syn*Vm already in “mV-ish” ints

struct SamplePacket {                                   // This struct must remain exactly 16 bytes (8 × int16_t), enforced by the static_assert below.
  int16_t v_q;                                            // v_out * V_SCALE -- v_q: int16_t, v_out in mV*0.01 => [-327.68, +327.67] V
  int16_t stim_state;                                     // Stim_State
  int16_t Itot_q;                                         // I_Total * I_SCALE
  int16_t syn1_vm_q;                                      // Syn1_Vm * SYN_V_SCALE
  int16_t Isyn1_q;                                        // I_Synapse1 * I_SCALE
  int16_t syn2_vm_q;                                      // Syn2_Vm * SYN_V_SCALE
  int16_t Isyn2_q;                                        // I_Synapse2 * I_SCALE
  int16_t trigger_q;                                      // Trigger
};

static_assert(sizeof(SamplePacket) == 16,"SamplePacket must remain 16 bytes (protocol compatibility)");



// // // // // // // // // // // // // // // // // // // // // // // //
/*                       Hardware parameters                         */

constexpr unsigned long BaudRate   = 250000;

constexpr int bits10     = 1023;
constexpr int bits12     = 4095;


// Inline globals objects       
inline MCP3208 ADC1;                                      // First MCP3208 12-bit SPI ADC
inline MCP3208 ADC2;                                      // Second MCP3208 12-bit SPI ADC
inline MCP4922 DAC;                                       // MCP4922 12-bit dual SPI DAC
inline SamplePacket pkt;                                  // Reusable 16-byte sample packet buffer for streaming data over serial

struct Potentiometer {
  int offset;
};
inline const Potentiometer pot = {
  .offset = bits12/15
};

// // // // // // // // // // // // // // // // // // // // // // // //
/*                          Pin Definition                           */

struct SPI_pins {
  uint8_t sck;                                            // Clock
  uint8_t mosi;                                           // Data In
  uint8_t miso;                                           // Data Out
  uint8_t cs_adc1;                                        // Chip Selection 1
  uint8_t cs_adc2;                                        // Chip Selection 2
  uint8_t cs_dac;                                         // Chip Selection 3
};

struct MCP3208_pins {
  uint8_t syn1_a;                                         // ADC 1.0: Input Analog pin for Synapse 1
  uint8_t syn1_pot;                                       // ADC 1.1: Synapse 1 Gain potentiometer pin
  uint8_t syn2_a;                                         // ADC 1.2: Input Analog pin for Synapse 2  
  uint8_t syn2_pot;                                       // ADC 1.3: Synapse 2 Gain potentiometer pin
  uint8_t current_in;                                     // ADC 1.4: Input Analog pin for CurrentIn stimuli
  uint8_t current_in_pot;                                 // ADC 1.5: Inject Current potentiometer pin
  uint8_t pd;                                             // ADC 1.6: Photodiode reading pin
  uint8_t pd_pot;                                         // ADC 1.7: Photodiode Gain potentiometer pin

  //                                                      // ADC 2.0
  uint8_t stim_str_pot;                                   // ADC 2.1: Stimulus amplitude potentiometer pin
  uint8_t stim_freq_pot;                                  // ADC 2.2: Stimulus frequency potentiometer pin
  //                                                      // ADC 2.3
  uint8_t noise_pot;                                      // ADC 2.4: Noise generator potentiometer pin
};

struct MCP4922_pins {
  uint8_t axon_a;                                         // DAC 3.0: OutputAnalog pin for the axon
  uint8_t stim_a;                                         // DAC 3.1: Output Analog pin for the stimulating Current Input pin
};

struct GPIO_pins {
  uint8_t syn1_d;                                         // Input Digital pin for Synapse 1
  uint8_t syn2_d;                                         // Input Digital pin for Synapse 2
  uint8_t axon_d;                                         // Output Digital pin for the axon
  uint8_t stim_d;                                         // Output Digital pin for the stimulating LED  
  uint8_t spike;                                          // Buzzer
  uint8_t led_r;                                          // Red Vm LED
  uint8_t led_g;                                          // Green Vm LED
  uint8_t led_b;                                          // Blue Vm LED
};

struct HardwarePins {
  SPI_pins        spi;                                    // ESP32 SPI + chip selects
  MCP3208_pins    adc1;                                   // MCP3208 #1 channels
  MCP3208_pins    adc2;                                   // MCP3208 #2 channels
  MCP4922_pins    dac;                                    // MCP4922
  GPIO_pins       gpio;                                   // ESP32 GPIOs
};

inline const HardwarePins pins = {
  .spi = {                                                // SPI pins (ESP32-S3) 
    .sck     = 12,                                          // GPIO 12
    .mosi    = 11,                                          // GPIO 11
    .miso    = 13,                                          // GPIO 13
    .cs_adc1 = 10,                                          // GPIO 10
    .cs_adc2 =  9,                                          // GPIO 9
    .cs_dac  = 15                                           // GPIO 15
  },

  .adc1 = {                                               // MCP3208 #1 (ADC1) channels 
    .syn1_a          = 0,                                   // CH0 
    .syn1_pot        = 1,                                   // CH1
    .syn2_a          = 2,                                   // CH2
    .syn2_pot        = 3,                                   // CH3
    .current_in      = 4,                                   // CH4
    .current_in_pot  = 5,                                   // CH5  
    .pd              = 6,                                   // CH6
    .pd_pot          = 7,                                   // CH7
  },

  .adc2 = {                                               // MCP3208 #2 (ADC2) channels 
    .stim_str_pot  = 1,                                     // CH1
    .stim_freq_pot = 2,                                     // CH2
    .noise_pot     = 4                                      // CH4
  },

  .dac = {                                                // MCP4922 #2 (DAC) channels 
    .axon_a = 0,                                            // CH0
    .stim_a = 1                                             // CH1
  },
  
  .gpio = {                                               // ESP32-S3 GPIO pins 
    .syn1_d = 38,                                           // GPIO 38
    .syn2_d = 39,                                           // GPIO 39
    .axon_d = 16,                                           // GPIO 16
    .stim_d =  1,                                           // GPIO 1
    .spike  = 18,                                           // GPIO 18
    .led_r  = 21,                                           // GPIO 21
    .led_g  = 14,                                           // GPIO 14
    .led_b  = 47                                            // GPIO 47
  }
};

   

// // // // // // // // // // // // // // // // // // // // // // // //
/*                       Spike LEDs parameters                       */

constexpr  int ledc_Resolution = 10;                      // PWM resolution in bits: duty cycle range 0 - 1023            
constexpr  int ledc_Max = (1 << ledc_Resolution) - 1;     // Maximum PWM duty value for the chosen resolution (1023)
constexpr  int ledc_Freq  = 20000;                        // PWM frequency in Hz (20 kHz, above audible range to avoid coil whine)

inline uint16_t led_r_last = 0, led_g_last = 0, led_b_last = 0;

inline void setLedc(uint8_t pin, uint16_t value, uint16_t &last) {
  if (value != last) {
    last = value;
    ledcWrite(pin, value);
  }
}



// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Neuron parameters                         */

struct NeuronModel {
  // Dynamic state
  float   v;                                              // Voltage in Izhikevich model
  float   u;                                              // Recovery variable in Izhikevich model
  // Integration step
  float   dt_ms;                                          // Default 0.1. This is the "intended" refresh rate of the model.
  // Izhikevich parameters
  float   a;                                              // Time scale of recovery variable u. Smaller a gives slower recovery
  float   b;                                              // Recovery variable associated with u. greater b coules it more strongly 
  float   c;                                              // After spike reset value
  float   d;                                              // After spike reset of recovery variable
  float   v_rest;                                         // Membrane resting potential
  // Display thresholds
  float   Vm_min;                                         // Minimum voltage value the v variable from Izhikevich can take
  float   Vm_max;                                         // Maximum voltage value 
  float   Vm_spike;                                       // Voltage value above which the neuron will spike
  float   Vm_peak;                                        // Voltage peak value from which the v variable will start its recovery
  float   v_out;                                          // Displayed voltage 
  // Accumulated current
  float   total_current;                                  // Sum of all applied current to the neuron (I_IC, I_PD, I_Synapse1, I_Synapse2, I_Stim, I_Noise) 
  // Spike 
  bool    spike;                                          // Boolean used for registrating spike events
  uint8_t pin_spike;                                      // Hardware pin used to signal spikes (buzzer, etc.)
  // Refresh rate
};

// Default neuron model preset
constexpr IzhikevichModel  defaultModel  = IzhikevichModel::TonicSpiking;
constexpr IzhikevichParams defaultParams = getIzhikevichParams(defaultModel);

inline IzhikevichModel currentModel = defaultModel;       // Track which Izhikevich preset is currently active

inline NeuronModel neuron = {
  .v             = defaultParams.v_rest,                  // Start at resting potential
  .u             = 0.0f,
  .dt_ms         = 0.1f,
  .a             = defaultParams.a,
  .b             = defaultParams.b,
  .c             = defaultParams.c,
  .d             = defaultParams.d,
  .v_rest        = defaultParams.v_rest,
  .Vm_min        = -110.0f,
  .Vm_max        = 100.0f,
  .Vm_spike      = -30.0f,
  .Vm_peak       = 30.0f,
  .v_out         = 0.0f,
  .total_current = 0.0f,
  .spike         = false,  
  .pin_spike     = pins.gpio.spike
};


inline bool spike_pin_last = false;

inline void setSpikePin(bool level) {
  if (level != spike_pin_last) {
    spike_pin_last = level;
    digitalWrite(neuron.pin_spike, level ? HIGH : LOW);
  }
}



// // // // // // // // // // // // // // // // // // // // // // // //
/*                     Voltage Clamp parameters                      */

struct VoltageClamp{
  // Direct Current Stimulus
  uint8_t pin;                                            // Input Current pin
  float   value_currentIn;                                // CurrentIn_Value
  float   currentIn_scaling;                              // CurrentInScaling
  float   current;                                        // Stimulus input current
  // Clamp potentiometer
  uint8_t pot_pin;                                        // Clamp current pot pin
  float   pot_value;                                      // Clamp potentiometer value
  float   pot_scaling;                                    //  Clamp scale value
  float   current_clamp;                                  //  Clamp input current
  // Input Current flag
  bool    enable;                                         // Boolean used for enabling Clamp potentiometer
};

inline VoltageClamp IC{
  .pin               = pins.adc1.current_in,
  .value_currentIn   = 0.0f,                              // Stimulus Current-In value read for the voltage clamp
  .currentIn_scaling = 0.1f,
  .current           = 0.0f,
  .pot_pin           = pins.adc1.current_in_pot,
  .pot_value         = 0.0f,
  .pot_scaling       = bits12/100.0f,                     // Inject Current value scaling - The lower, the stronger the impact of the IC potentiometer
  .current_clamp     = 0.0f,    
  .enable = true,
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Noise parameters                          */

struct NoiseGenerator {
  uint8_t  pot_pin;                                       // pin_NoisePot
  int      pot_value;                                     // Noise gain value
  float    pot_scaling;                                   // Noise scaling
  float    amp;                                           // Noise amplitude
  float    current;                                       // Noise Input current
  bool     enable;                                        // Noise_Flag (true: use pot+Gaussian, false: GUI generated value)
  float    mean;                                          // Mean
  float    sigma;                                         // Standard deviation
  float    newSigma;                                      // Current Standard deviation
  float    var;                                           // Variance
  Gaussian dist;                                          // Gaussian(0, sigma^2)
};

inline NoiseGenerator noise{
  .pot_pin     = pins.adc2.noise_pot,
  .pot_value   = 0,
  .pot_scaling = bits12/25.0f,                            // Noise gain scaling - The lower, the stronger the impact of the Noise_Potentiometer.  Default = 1000
  .amp         = 0.0f,
  .current     = 0.0f,
  .enable      = true,
  .mean        = 0.0f,                                     // Set the Gaussian distribution mean to 0
  .sigma       = 0.0f,
  .newSigma    = 0.0f,
  .var         = 0.0f,
  .dist        = Gaussian(0.0f, 0.0f)                     // Constructs a Gaussian (normal) distribution with mean = 0, variance = (Noise amplitude /2)^2
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                      PhotoDiode parameters                        */

constexpr int PD_WindowSize = 10;                         // Number of Photodiode reading to average

struct Photodiode {
  // hardware
  uint8_t pin;                                            // Photodiode pin
  uint8_t pot_pin;                                        // Photodiode Pot pin
  // Photodiode reading parameters
  int   pot_value;                                        // Photodiode pot value
  float pot_scaling;                                      // Photodiode pot scaling
  float gain;                                             // Photodiode Gain
  float amp;                                              // Photodiode Amplitude
  // Photodiode averaging
  int   value;                                            // Photodiode value (latest)
  int   values[PD_WindowSize] = {0};                      // Photodiode array (10 values)
  int   counter;                                          // Photodiode reading counter
  int   avgWindow;                                        // Photodiode numeber of values to be averaged
  int   sum;                                              // Photodiode values summed
  float average;                                          // Photodiode values averaged
  // generate Photodiode parameters
  float inv_scaling;                                      // 1 / Photodiode scaling
  float decay;                                            // Photodiode decay
  float ampMin;                                           // Photodiode gain minimum value
  float recovery;                                         // Photodiode recovery
  int   polarity;                                         // Photodiode polarity
  float current;                                          // Photodiode Inpute current  
  // Flags
  bool  gain_enable;                                      // Photodiode Gain Flag (enables potentiometer)
  bool  decay_enable;                                     // Photodiode Decay Flag
  bool  recovery_enable;                                  // Photodiode Recovery Flag
};

inline Photodiode PD = {
    .pin             = pins.adc1.pd,
    .pot_pin         = pins.adc1.pd_pot,
    .pot_value       = 0,
    .pot_scaling     = bits12/50.0f,                      // the lower, the stronger the impact on PD_Gain
    .gain            = 0.0f,
    .amp             = 1.0f,
    .value           = 0,
    .counter         = 0,
    .avgWindow       = PD_WindowSize,
    .sum             = 0,
    .average         = 0.0f,
    .inv_scaling     = 1.0 / 0.45f,
    .decay           = 0.001f,
    .ampMin          = 0.0f,                              // the photodiode gain cannot decay below this value
    .recovery        = 0.025f,
    .polarity        = 1,
    .current         = 0.0f,
    .gain_enable     = true,
    .decay_enable    = true,
    .recovery_enable = true
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                        Synapse parameters                         */
struct Synapse {
  // Hardware
  uint8_t pin_digital;                                    // pin_Syn*_D 
  uint8_t pin_analog;                                     // pin_Syn*_A 
  uint8_t pot_pin;                                        // pin_Syn*_Pot 
  // Pot/gain
  float gain;                                             // Syn*_Gain
  int   pot_value;                                        // Syn* pot value
  float pot_scaling;                                       // Syn*_PotScaling
  // State
  int   spikeState;                                       // Synapse 1 digital input  
  float current ;                                         // I_Synapse*
  float decay;                                            // Synapse*_decay
  float Vm;                                               // Syn*_Vm
  float Vm_input;
  // Axonal input offset
  float analogOffsetLow;
  float analogOffsetHigh;
  // Flags
  bool  gain_enable;                                      // Syn*_Gain_Flag
  bool  decay_enable;                                     // Syn*_Decay_Flag
};

inline Synapse syn1 = {
  .pin_digital      = pins.gpio.syn1_d,
  .pin_analog       = pins.adc1.syn1_a,
  .pot_pin          = pins.adc1.syn1_pot,
  .gain             = 0,                                  // Synapse 1 gain potentiometer value
  .pot_value        = 0,
  .pot_scaling       = bits12/50.0f,                       // Synapse 1 gain sacaling - The lower, the stronger the impact of the Syn2_Potentiometer.  Default = 2
  .spikeState       = LOW,
  .current          = 0.0f,                               // Synapse 1 input current
  .decay            = 0.995f,                             // Synpase 1 decay rate. The difference to 1 matters - the smaller the difference, the slower the decay. Default  = 0.995
  .Vm               = 0.0f,
  .Vm_input         = 0.0f,
  .analogOffsetLow  = -10.0f,
  .analogOffsetHigh = -400.0f,
  .gain_enable      = true,
  .decay_enable     = true
};

inline Synapse syn2 = {
  .pin_digital      = pins.gpio.syn2_d,
  .pin_analog       = pins.adc1.syn2_a,
  .pot_pin          = pins.adc1.syn2_pot,
  .gain             = 0,                                  // Synapse 2 gain potentiometer value
  .pot_value        = 0,
  .pot_scaling      = bits12/50.0f,                       // Synapse 2 gain sacaling - The lower, the stronger the impact of the Syn2_Potentiometer.  Default = 2
  .spikeState       = LOW,                                // Synapse 2 digital input        
  .current          = 0.0f,                               // Synapse 2 input current
  .decay            = 0.990f,                             // Synpase 2 decay rate. The difference to 1 matters - the smaller the difference, the slower the decay. Default  = 0.990
  .Vm               = 0.0f,
  .Vm_input         = 0.0f, 
  .analogOffsetLow  = -10.0f,
  .analogOffsetHigh = -400.0f,
  .gain_enable      = true,
  .decay_enable     = true
};
             


// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Axon parameters                           */

struct Axon {
  // Hardware
  uint8_t pin_digital;                                    // pin_Syn*_D 
  uint8_t pin_analog;                                     // pin_Syn*_A 
  float Vm;
  float offset; 
  float Vm_range_inv;
};

inline Axon axon{
  .pin_digital  = pins.gpio.axon_d,
  .pin_analog   = pins.dac.axon_a,
  .Vm           = 0.0f,
  .offset       = -6.75f,
  .Vm_range_inv = 1.0f / (neuron.Vm_max - neuron.Vm_min)
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                        Stimuli parameters                         */

struct Stimulus {
  // Hardware
  int   pin_stim_light;                                   // pin_Stim_D  (PWM)
  int   pin_stim_current;                                 // pin_CurrentIn
  int   pin_strPot;                                       // pin_StimStrPot
  int   pin_freqPot;                                      // pin_StimFrePot
  // Strength / frequency
  int   strPot;                                           // StimStr_Value
  float str_digitalMap;                                    // StrimStr mapping range
  int   str_digital;                                      // StimStrD
  float str_analogMap;                                     // StrimStr mapping range
  int   str_analog;                                       // StimStrA
  int   str_analog_min;                                   // StimStrA_mini
  int   freqPot;                                          // StimFre_Value
  float freq_map;                                           // StrimFre mapping range
  int   freq;                                             // StimFre
  // Output values
  int   value_digital;                                    // Stim_val_D
  int   value_analog;                                     // Stim_val_A
  int   value_custom;                                     // StimCus_val
  float current_scaling;                                  // Stim_CurrentScaling
  float light_scaling;                                    // StimLED_scaling
  float light_offset;                                     // StimLED_offset
  // Duty-cycle & timing
  int   counter;                                          // Stim_counter
  int   steps;                                            // Stim_steps
  int   dutyCycle;                                        // Stim_DutyCycle
  int   dutyCycle_Min;                                    // Stim_minDutyCycle
  int   state;                                            // Stim_State (for serial output)
  int   trigger;                                          // Stimulus trigger (begining of each loop)
  int   pwm;
  int   dac;
  // Flags
  bool  strength_enable;                                  // StimStr_Flag
  bool  frequency_enable;                                 // StimFre_Flag
  bool  custom_enable;                                    // StimCus_Flag
  bool  trigger_enable;
  bool  serialTrigger_enable; 
};

inline Stimulus stim{
  .pin_stim_light       = pins.gpio.stim_d,
  .pin_stim_current     = pins.dac.stim_a,
  .pin_strPot           = pins.adc2.stim_str_pot,
  .pin_freqPot          = pins.adc2.stim_freq_pot,
  .strPot               = 0,
  .str_digitalMap       = 100.0f / (bits12 / 2),
  .str_digital          = 0,
  .str_analog           = 0,
  .str_analogMap        = 200.0f / (bits12 / 2),
  .str_analog_min       = 5,
  .freqPot              = 0,
  .freq_map             = 200.0f / float(bits12),
  .freq                 = 0,                              // Scaled stimulus frequency
  .value_digital        = 0,                              // Stimulus Digital output for stimulating LED
  .value_analog         = 0,                              // Stimulus Analog output for Current in pin
  .value_custom         = 0,
  .current_scaling      = 0.9f,
  .light_scaling        = 5.12f,                          // Scaling applied to the digital out value
  .light_offset         = 10.0f,
  .counter              = 0,                              // Stimulus step counter (number of void loops)
  .steps                = 0,                              // Number of steps required for half a stimulus duty cycle
  .dutyCycle            = 500,                            // Default stimulus duty cycle value
  .dutyCycle_Min        = 10,                             // Minimum loop steps the stimulus duty cycle cannot fall under
  .state                = 0,                              // Status of the stimulus (ON or OFF / 1 or 0);
  .trigger              = 0,
  .pwm                  = 0,
  .dac                  = 0,
  .strength_enable      = true,
  .frequency_enable     = true,
  .custom_enable        = true,
  .trigger_enable       = false,
  .serialTrigger_enable = false
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                           Global flags                            */
 
inline bool   Buzzer_enable  = true;
inline bool   LED_enable     = true;

inline float Vm_led_gain = bits10 / (neuron.Vm_peak - neuron.Vm_min);

// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Hardware Settings                         */

inline void HardwareSettings(){
  // Give USB a moment (especially after reset on S3)
  delay(1500);
  Serial.begin(BaudRate);
  delay(500);

  pinMode(pins.gpio.spike,OUTPUT);

  pinMode(pins.gpio.led_r, OUTPUT);
  pinMode(pins.gpio.led_g, OUTPUT);
  pinMode(pins.gpio.led_b, OUTPUT);
  
  pinMode(pins.gpio.syn1_d,INPUT);

  pinMode(pins.gpio.syn2_d,INPUT);

  pinMode(pins.gpio.axon_d,OUTPUT);
  
  pinMode(pins.gpio.stim_d,OUTPUT);

  digitalWrite(pins.gpio.spike,LOW);
  digitalWrite(pins.gpio.axon_d,LOW);
  digitalWrite(pins.gpio.stim_d,LOW);
  digitalWrite(pins.gpio.led_r,LOW);
  digitalWrite(pins.gpio.led_g,LOW);
  digitalWrite(pins.gpio.led_b,LOW);

  ledcAttach(pins.gpio.led_r, ledc_Freq, ledc_Resolution);
  ledcAttach(pins.gpio.led_g, ledc_Freq, ledc_Resolution);
  ledcAttach(pins.gpio.led_b, ledc_Freq, ledc_Resolution);
  ledcWrite(pins.gpio.led_r, 0);  
  ledcWrite(pins.gpio.led_g, 0);   
  ledcWrite(pins.gpio.led_b, 0);  

  ledcAttach(pins.gpio.stim_d, ledc_Freq, ledc_Resolution);
  ledcWrite(pins.gpio.stim_d, 0);

  SPI.begin(pins.spi.sck, pins.spi.miso, pins.spi.mosi, -1);
  ADC1.begin(pins.spi.cs_adc1);
  ADC2.begin(pins.spi.cs_adc2);
  DAC.begin(pins.spi.cs_dac);

  // --- Seed RNG once (ESP32S3 has a hw RNG) ---
  randomSeed(esp_random());
}

inline void SerialBlank(){        

}



// // // // // // // // // // // // // // // // // // // // // // // //
/*                          mapfloat helper                          */

inline float mapfloat(float x, float in_min, float in_max, float out_min, float out_max)
{
  return (float)(x - in_min) * (out_max - out_min) / (float)(in_max - in_min) + out_min;
}


#pragma once  

#include <cstdint>



// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Librairies import                         */ 

#include "Izhikevich_parameters.h"
#include <Arduino.h>
#include <esp_system.h>
#include <SPI.h>
#include <MCP_ADC.h>                                      // Microchip SPI ADC Library by Rob Tillaart                 https://github.com/RobTillaart/MCP_ADC
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
 .step_us     = 2000
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                        Serial parameters                          */

const float V_SCALE     = 100.0f;                         // 2 decimal places for voltages
const float I_SCALE     = 100.0f;                         // 2 decimal places for currents
const float SYN_V_SCALE = 100.0f;                           // Syn*Vm already in “mV-ish” ints

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

constexpr unsigned long BaudRate   = 500000;

constexpr int bits8      = 255;
constexpr int bits10     = 1023;
constexpr int bits12     = 4095;
constexpr int dac_bits   = 8;
constexpr int dac_max    = (1 << dac_bits) - 1;
constexpr uint8_t stim_dac_zero = (dac_max + 1) / 2;  // 128
constexpr uint8_t stim_dac_span = dac_max - stim_dac_zero; // 127
constexpr uint16_t current_in_rail_margin   = 80;  // ADC values near 0 or 4095 are not accepted as autozero
constexpr uint16_t current_in_stable_delta  = 8;   // Max ADC-count movement considered stable
constexpr uint16_t current_in_arm_samples   = 50;  // 50 loops × 2 ms = ~100 ms with your current timing
   
     
inline MCP3208 ADC1;                                      // First MCP3208 12-bit SPI ADC
inline MCP3208 ADC2;                                      // Second MCP3208 12-bit SPI ADC
inline SamplePacket pkt;                                  // Reusable 16-byte sample packet buffer for streaming data over serial



// // // // // // // // // // // // // // // // // // // // // // // //
/*                           Potentiometer                           */

struct PotFilter {                                      // This struct filters raw ADC readings from potentiometers to reduce:- random ADC spikes / EMI (median-of-3) - mechanical jitter / detent bounce (IIR smoothing) - +/-1 LSB chatter when the knob is not moving (deadband)
  float    alpha        = 0.20f;                          // IIR coefficient (0..1): higher = faster response, lower = smoother
  uint16_t deadband     = 6;                              // Output deadband (ADC counts): ignores tiny changes around the stable value
  bool     initialized  = false;                          // One-time init flag (seeds the filter state on first use)
  uint16_t raw_1        = 0;                              // Previous raw ADC sample (t-1)
  uint16_t raw_2        = 0;                              // Previous raw ADC sample (t-2)
  float    filt_f       = 0.0f;                           // Filter accumulator (float) for IIR
  uint16_t filt_u       = 0;                              // Rounded filtered value (ADC counts)
  uint16_t stable_u     = 0;                              // Deadbanded/stable output (ADC counts)

  static inline uint16_t median3(uint16_t a, uint16_t b, uint16_t c) { // Returns the median of 3 values (robust spike rejection)
    if (a > b) { uint16_t t = a; a = b; b = t; }          // Sort a/b
    if (b > c) { uint16_t t = b; b = c; c = t; }          // Sort b/c
    if (a > b) { uint16_t t = a; a = b; b = t; }          // Sort a/b again (now b is the median)
    return b;                                             // Return the median value
  }

  inline void reset(uint16_t raw) {                       // Resets internal state to a known value (use at boot / mode changes)
    initialized = true;                                   // Mark the filter as initialized
    raw_1       = raw;                                    // Seed previous raw samples
    raw_2       = raw;                                    // Seed previous raw samples
    filt_f      = (float)raw;                             // Seed IIR accumulator
    filt_u      = raw;                                    // Seed rounded output
    stable_u    = raw;                                    // Seed stable (deadbanded) output
  }

  inline uint16_t update(uint16_t raw) {                  // Push a new raw ADC sample; returns the filtered stable value (0..4095)
    if (!initialized) {                                   // If this is the first ever sample:
      reset(raw);                                         // Seed the filter state from the first sample
      return stable_u;                                    // Return a stable value immediately
    }

    const uint16_t m = median3(raw, raw_1, raw_2);         // Median-of-3: rejects single-sample spikes

    raw_2 = raw_1;                                        // Shift history (t-2 <- t-1)
    raw_1 = raw;                                          // Shift history (t-1 <- t)

    filt_f += alpha * ((float)m - filt_f);                // IIR low-pass: moves accumulator toward the median sample
    filt_u  = (uint16_t)lroundf(filt_f);                  // Round float accumulator back to integer ADC counts

    const int32_t d = (int32_t)filt_u - (int32_t)stable_u; // Compute delta vs current stable output

    if (d >= (int32_t)deadband || d <= -(int32_t)deadband) { // If change exceeds deadband threshold:
      stable_u = filt_u;                                  // Accept the new value as the stable output
    }

    return stable_u;                                      // Return stable output (what you should use for mapping)
  }
};

struct Potentiometer {
  int      offset;                                        // Potentiometer zero offset to controle misreading
  int      half_range;                                    // Potentiometer 12bits half-range :2047
  float    alpha_pot;                                     // Default IIR alpha for all pot filters (0..1)
  uint16_t deadband_detent;                               // Deadband (counts) for detent pots (patch, stim, syn, PD): kills +/-1 LSB chatter
  uint16_t deadband_smooth;                               // Deadband (counts) for smooth pots (noise): keeps it responsive
  bool     use_patch_pot;                                 // Boolean used for enabling Patch potentiometer
  bool     use_noise_pot;                                 // Boolean used for enabling Noise potentiometer
  bool     use_photodiode_pot;                            // Boolean used for enabling Photodiode potentiometer
  bool     use_stimfrequency_pot;                         // Boolean used for enabling Stimulus Frequency potentiometer
  bool     use_stimstrength_pot;                          // Boolean used for enabling Stimulus Strength potentiometer
};
inline Potentiometer pot = {
  .offset                = bits12/15,
  .half_range            = (bits12 + 1) / 2,
  .alpha_pot             = 0.20f,
  .deadband_detent       = 6,                              // Detent pots: stable at each click
  .deadband_smooth       = 2,                              // Smooth pot (noise): more responsive
  .use_patch_pot         = true,
  .use_noise_pot         = true,
  .use_photodiode_pot    = true,
  .use_stimfrequency_pot = true,
  .use_stimstrength_pot  = true
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                          Pin Definition                           */

struct SPI_pins {
  uint8_t sck;                                            // Clock
  uint8_t mosi;                                           // Data In
  uint8_t miso;                                           // Data Out
  uint8_t cs_adc1;                                        // Chip Selection 1
  uint8_t cs_adc2;                                        // Chip Selection 2
};

struct MCP3208_pins {
  uint8_t current_in_pot;                                 // ADC 1.0: Inject Current potentiometer pin
  uint8_t syn1_pot;                                       // ADC 1.1: Synapse 1 Gain potentiometer pin
  uint8_t syn2_pot;                                       // ADC 1.2: Synapse 2 Gain potentiometer pin 
  uint8_t pd_pot;                                         // ADC 1.3: Photodiode Gain potentiometer pin
  uint8_t stim_str_pot;                                   // ADC 1.4: Stimulus amplitude potentiometer pin
  uint8_t stim_freq_pot;                                  // ADC 1.5: Stimulus frequency potentiometer pin
  uint8_t noise_pot;                                      // ADC 1.6: Noise generator potentiometer pin                                                   
  uint8_t syn1_a;                                         // ADC 2.0: Input Analog pin for Synapse 1
  uint8_t syn2_a;                                         // ADC 2.1:Input Analog pin for Synapse 2
  uint8_t pd;                                             // ADC 2.2:Photodiode reading pin
  uint8_t current_in;                                     // ADC 2.3: Input Analog pin for CurrentIn stimuli
};

struct GPIO_pins {
  uint8_t syn1_d;                                         // Input Digital pin for Synapse 1
  uint8_t syn2_d;                                         // Input Digital pin for Synapse 2
  uint8_t axon_a;                                         // OutputAnalog pin for the axon
  uint8_t axon_d;                                         // Output Digital pin for the axon
  uint8_t stim_a;                                         // Output Analog pin for the stimulating Current Input pin
  uint8_t stim_d;                                         // Output Digital pin for the stimulating LED   
  uint8_t spike;                                          // Buzzer
  uint8_t led_r;                                          // RGB common anode / LED power, active HIGH, PWM
  uint8_t led_g;                                          // Green cathode, active LOW
  uint8_t led_b;                                          // Blue cathode, active LOW
  uint8_t mode;                                           // Neuron mode button
  uint8_t pinCP1;                                         // Charlie Plexing LED1
  uint8_t pinCP2;                                         // Charlie Plexing LED2
  uint8_t pinCP3;                                         // Charlie Plexing LED3
  uint8_t pinCP4;                                         // Charlie Plexing LED4
};

struct HardwarePins {
  SPI_pins        spi;                                    // ESP32 SPI + chip selects
  MCP3208_pins    adc1;                                   // MCP3208 #1 channels
  MCP3208_pins    adc2;                                   // MCP3208 #2 channels
  GPIO_pins       gpio;                                   // ESP32 GPIOs
};  

inline const HardwarePins pins = {
  .spi = {                                                // SPI pins (ESP32-S3) 
    .sck     = 18,                                          // GPIO 18
    .mosi    = 32,                                          // GPIO 32
    .miso    = 33,                                          // GPIO 33
    .cs_adc1 = 0,                                           // GPIO 0
    .cs_adc2 = 4,                                           // GPIO 4
  },
  .adc1 = {                                               // MCP3208 #1 (ADC1) channels 
    .current_in_pot  = 0,                                   // CH0 
    .syn1_pot        = 1,                                   // CH1
    .syn2_pot        = 2,                                   // CH2
    .pd_pot          = 3,                                   // CH3
    .stim_str_pot    = 4,                                   // CH4
    .stim_freq_pot   = 5,                                   // CH5  
    .noise_pot       = 6,                                   // CH6
  },
  .adc2 = {                                               // MCP3208 #2 (ADC2) channels 
    .syn1_a       = 0,                                     // CH0
    .syn2_a       = 1,                                     // CH1
    .pd           = 2,                                     // CH2
    .current_in   = 3                                      // CH3
  },
  .gpio = {                                               // ESP32-S3 GPIO pins 
    .syn1_d = 35,                                           // GPIO 35
    .syn2_d = 34,                                           // GPIO 34
    .axon_a = 25,                                           // GPIO 25
    .axon_d = 15,                                           // GPIO 15
    .stim_a = 26,                                           // GPIO 26
    .stim_d = 22,                                           // GPIO 22
    .spike  = 13,                                           // GPIO 13
    .led_r  = 27,                                           // GPIO 27: RGB common anode / LED power, active HIGH PWM
    .led_g  = 14,                                           // GPIO 14: green cathode, active LOW
    .led_b  = 12,                                           // GPIO 12: blue cathode, active LOW
    .mode   = 39,                                           // GPIO 39
    .pinCP1 = 2,                                            // GPIO 2
    .pinCP2 = 5,                                            // GPIO 5
    .pinCP3 = 19,                                           // GPIO 19
    .pinCP4 = 21                                            // GPIO 21
  }
};
 


// // // // // // // // // // // // // // // // // // // // // // // //
/*           Button debounce state (shared across modules)           */

struct ButtonDebounce {
  uint8_t  lastStable;                                      // Debounced stable level
  uint8_t  lastRaw;                                         // Last raw read level
  uint32_t lastChange_ms;                                   // Timestamp of last raw transition
  uint32_t debounce_ms;                                     // Debounce window
  uint8_t  raw;                                             // Latest sampled raw level (filled by poll function)
  uint32_t now_ms;                                          // Latest sampled time (filled by poll function)
};
inline ButtonDebounce modeBtn {
  .lastStable         = LOW,
  .lastRaw            = LOW,
  .lastChange_ms      = 0,
  .debounce_ms        = 30,
  .raw                = LOW,
  .now_ms             = 0
};



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
  // Mode
  int     mode;
  int     modeState;
  int     nModes;
  int     modeDelay;
  int     openingDelay;
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
  .pin_spike     = pins.gpio.spike,
  .mode          = 0,
  .modeState     = 0,
  .nModes        = (int)IzhikevichModelCount,
  .modeDelay     = 500,
  .openingDelay  = 50
};





// // // // // // // // // // // // // // // // // // // // // // // //
/*                     Patch Clamp parameters                      */

// Clamp mode: "CurrentClamp" mimics classical I-clamp (command current, observe Vm).
// "VoltageClamp" enables a PI feedback controller that drives injected current so Vm tracks a command voltage.

enum class ClampMode : uint8_t { CurrentClamp = 0, VoltageClamp = 1 };
inline ClampMode clampMode = ClampMode::CurrentClamp;

struct PatchClamp{
  // --- Direct Patch Stimulus (external Patch jack) 
  uint8_t  pin;                                           // ADC pin for the Patch jack (external analog input)
  uint16_t input_value_raw;                               // Raw ADC reading (0..4095)
  uint16_t input_value;                                   // Filtered ADC reading;
  float    input_value_f;                                 // Filter accumulator (float) 
  float    alpha_in;                                      // IIR alpha for Current-In filtering (0..1)
  float    input_scaling;                                 // Conversion factor from ADC counts -> engineering units (e.g., a.u./count or mV/count)
  float    current_input;                                 // Current-In contribution to injected current (a.u.). Used in CurrentClamp; often 0 in VoltageClamp.
  // --- Shared patch potentiometer (ADC1) 
  uint8_t  pot_pin;                                       // ADC pin for the Patch knob (front-panel control)                           
  PotFilter pot_filt;                                     // Filter state for Patch knob ADC (median + IIR + deadband)
  float    pot_centered;                                  // Baseline-centered Current-In ADC reading (counts).
  float    pot_value;
  float    pot_adj;            
  float    pot_scaling;                                   // Current-clamp knob scaling (a.u. per count after deadzone) 
  float    denom;                                         // Effective half-range after deadzone removal (counts)
  float    frac;                                          // Normalized knob position in [-1..+1]
  // --- Current clamp command (I-clamp style)
  float    current_clamp;                                 // Command injected current (a.u.) from knob or host (I-clamp style)
  float    i_current;                                     // Final injected current
  float    current_in_zero;                               // Baseline estimate of Current-In ADC (counts). Updated slowly when stimulus output is OFF.
  bool     current_in_ready;
  uint16_t current_in_stable_count;
  uint16_t current_in_prev_value;
  float    current_in_candidate_zero;
  // --- Voltage clamp command (V-clamp style)
  float    v_hold;                                        // Holding potential command (mV) (baseline)
  float    v_cmd;                                         // Total command voltage (mV): typically v_cmd = v_hold + v_step
  float    v_cmd_span;                                    // Knob span around v_rest: v_hold = v_rest + frac*v_cmd_span (mV)
  float    v_step;                                        // Voltage step added to hold during protocols (mV)
  float    v_step_max;                                    // Max |v_step| mapped from full-scale stimulus input (mV)
  float    i_command;                                     // Final command/injected current
  float    magnitude;
  // --- Voltage clamp controller (PI)
  float    Kp;                                            // Proportional gain (a.u. per mV error)
  float    Ki;                                            // Integral gain (a.u. per (mV*ms)) if dt is in ms
  float    e_int;                                         // Integrated voltage error (mV*ms)
  float    I_clamp;                                       // Clamp current output (a.u.) computed by PI in VoltageClamp mode
  float    I_min;                                         // Compliance min (a.u.): clamp cannot inject below this
  float    I_max;                                         // Compliance max (a.u.): clamp cannot inject above this
  // --- GUI output
  float    I_for_gui;                                     //Current value reported to the GUI 
};
inline PatchClamp patch{
  .pin                = pins.adc2.current_in,
  .input_value_raw    = 0,
  .input_value        = 0,   
  .input_value_f      = bits12 * 0.5f,
  .alpha_in           = 0.25f,                     
  .input_scaling      = 100.0f / ((float)((bits12 + 1) / 2) - (float)(bits12 / 15)),
  .current_input      = 0.0f,
  .pot_pin            = pins.adc1.current_in_pot,
  .pot_centered       = 0.0f, 
  .pot_value          = 0.0f,
  .pot_adj            = 0.0f,
  .pot_scaling        = 1.0f / (bits12/200.0f), 
  .denom              = 0.0f,
  .frac               = 0.0f,
  .current_clamp      = 0.0f,
  .i_current          = 0.0f,
  .current_in_zero           = 0.0f,
  .current_in_ready          = false,
  .current_in_stable_count   = 0,
  .current_in_prev_value     = 0,
  .current_in_candidate_zero = 0.0f,
  .v_hold             = -70.0f,
  .v_cmd              = defaultParams.v_rest,             
  .v_cmd_span         = 70.0f,                             
  .v_step             = 0.0f,
  .v_step_max         = 70.0f,  
  .i_command          = 0.0f,
  .magnitude          = 0.0f,   
  .Kp                 = 7.5f,                             
  .Ki                 = 0.10f,
  .e_int              = 0.0f,
  .I_clamp            = 0.0f,
  .I_min              = -200.0f,
  .I_max              = 300.0f,
  .I_for_gui          = 0.0f
};

struct Integrator {
  float e;                                                // Error computation: Defined as command minus measured: e = v_cmd - v_meas
  float p;                                                // Proportional term (instantaneous response): p = Kp * e
  float i_hold;                                           // Integral term I = Ki * e_int_candidate (Ki in [uA/(mV*ms)] so I is [uA])
  float i_final;
  float out_unsat_hold;                                   // Unsaturated PI output [uA]
  float out_unsat;
  float out_sat;                                          // Apply compliance (saturation) limits. This emulates the fact that the clamp amplifier cannot inject infinite current. I_min/I_max are the current compliance rails in [uA].
  bool  saturated_high;                                   // Anti-windup saturation high
  bool  saturated_low;                                    // Anti-windup saturation low
  bool  allow_integrate;
};
inline Integrator pi {
  .e                      = 0.0f,
  .p                      = 0.0f,
  .i_hold                 = 0.0f,
  .i_final                = 0.0f,
  .out_unsat_hold         = 0.0f,
  .out_unsat              = 0.0f,
  .out_sat                = 0.0f,
  .saturated_high         = false,
  .saturated_low          = false,
  .allow_integrate        = false
};


// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                        Setting PatchClamp mode                                        */

inline void setClampMode(ClampMode m) {
  if (clampMode == m) return;
  clampMode = m;

  // Reset PI state when entering/exiting voltage clamp
  patch.e_int   = 0.0f;
  patch.I_clamp = 0.0f;

  // On entry to V-clamp, start by holding the present Vm (avoids sudden jumps)
  if (clampMode == ClampMode::VoltageClamp) {
    patch.v_step = 0.0f;
    patch.v_hold = constrain(neuron.v, neuron.Vm_min, neuron.Vm_peak);
    patch.v_cmd  = patch.v_hold;
  } else {
    // Leaving V-clamp: clear step so it won't “stick” next time
    patch.v_step = 0.0f;
  }
}



// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Noise parameters                          */

struct NoiseGenerator {
  uint8_t   pot_pin;                                      // ADC pin for the Noise knob (front-panel control)
  PotFilter pot_filt;                                     // Filter state for Noise knob ADC (median + IIR + deadband)
  int16_t   pot_value;                                    // Raw ADC reading (0..4095)
  float     pot_scaling;                                  // Amplitude scale factor in (amp_units per ADC count after offset)
  float     amp;                                          // Noise amplitude in engineering units                   
  float     current;                                      // Noise Input current. This is the value added into I_total.
  float     mean;                                         // Gaussian mean of the noise current (same units as current), typically 0.
  float     sigma;                                        // Gaussian standard deviation (same units as current)
  float     sigma_per_amp;                                // Mapping from amplitude -> sigma. Example: 0.5 means sigma = amp/2.
  float     kSigmaUpdateEps;                              // Threshold for updating RNG parameters (sigma units). Prevents reconfiguring dist on tiny knob jitter.
  float     newSigma;                                     // Current Standard deviation
  float     var;                                          // Gaussian variance = sigma^2 (units: current^2)
  Gaussian  dist;                                         // Gaussian RNG/distribution object (mean, variance). 
};
inline NoiseGenerator noise{
  .pot_pin         = pins.adc1.noise_pot,
  .pot_value       = 0,
  .pot_scaling     = 1.0f / (bits12/25.0f),                            
  .amp             = 0.0f,
  .current         = 0.0f,
  .mean            = 0.0f,                                     
  .sigma           = 0.0f,
  .sigma_per_amp   = 0.5f,
  .kSigmaUpdateEps = 1e-3f, 
  .newSigma        = 0.0f,
  .var             = 0.0f,
  .dist            = Gaussian(0.0f, 0.0f)                     
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                      PhotoDiode parameters                        */

// // // // // // // // // // // // // // // // // // // // // // // //
/*                      PhotoDiode parameters                        */

struct Photodiode {
  // --- Hardware 
  uint8_t  pin;                                             // ADC pin for photodiode sensor input (raw light signal)
  uint8_t  pot_pin;                                         // ADC pin for photodiode gain pot (bipolar, centered)
  PotFilter pot_filt;                                       // Filter state for PD gain pot ADC (median + IIR + deadband)
  // --- Gain pot / control
  int16_t  pot_value;                                       // Raw ADC reading (0..4095)
  float    pot_scaling;                                     // Gain-units-per-count
  float    gain;                                            // Photodiode gain applied to averaged sensor signal (dimensionless)
  // --- Adaptive gain (photoreceptor-style adaptation)
  float    amp;                                             // Adaptive amplitude / gain state (dimensionless). Multiplies the photodiode-driven current
  // --- Raw readings + moving average (ring buffer)
  uint16_t raw;
  uint16_t adc;
  uint16_t value;                                           // Latest raw photodiode ADC reading
  int      values[10] = {0};                                // Ring buffer (fixed length = 10)
  uint8_t  counter;                                         // Ring-buffer index [0..windowN-1]
  uint8_t  windowN;                                         // Window length in samples (<= 10)
  float    invWindowN;                                      // 1.0f / windowN
  int32_t  sum;                                             // Sum of samples currently in ring buffer
  float    average;                                         // Moving-average photodiode reading
  // --- Current generation
  float    I_per_count;                                     // Model current per ADC count when gain=1 and amp=1
  float    current;                                         // Photodiode-driven injected current added into I_total
  // --- Adaptation dynamics
  float    decay;                                           // Decay rate for amp per tick
  float    ampMin;                                          // Minimum allowed amp (prevents gain collapsing to zero)
  float    recovery;                                        // Recovery rate pushing amp back toward 1.0
  int      polarity;                                        // Sign derived from gain (+1 if gain>=0 else -1)
  // --- Control flags
  bool     decay_enable;                                    // Photodiode Decay Flag
  bool     recovery_enable;                                 // Photodiode Recovery Flag
};
inline Photodiode PD = {
    .pin             = pins.adc2.pd,
    .pot_pin         = pins.adc1.pd_pot,
    .pot_value       = 0,
    .pot_scaling     = 1 / (bits12/50.0f),                      
    .gain            = 0.0f,
    .amp             = 1.0f,
    .raw             = 0,
    .adc             = 0,
    .value           = 0,
    .counter         = 0,
    .windowN         = 10,
    .invWindowN      = 0.1f,     
    .sum             = 0,
    .average         = 0.0f,
    .I_per_count     = 0.25f,                           
    .current         = 0.0f,
    .decay           = 0.001f,
    .ampMin          = 0.0f,                              
    .recovery        = 0.025f,
    .polarity        = 1,
    .decay_enable    = true,
    .recovery_enable = true
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                        Synapse parameters                         */

struct Synapse {
  // --- Hardware
  uint8_t  pin_digital;                                     // Digital spike/trigger input (TTL) from presynaptic source
  uint8_t  pin_analog;                                      // Analog Vm input (ADC) from presynaptic source (optional, for display/monitoring)
  uint8_t  pot_pin;                                         // ADC pin for the Synapse knobs (front-panel control) 
  uint16_t pot_raw;
  uint16_t pot_raw_filter;
  PotFilter pot_filt;                                       // Filter state for Synapse gain pot ADC (median + IIR + deadband)
  // --- Gain (synaptic weight)
  float    gain;                                            // Synaptic event amplitude (current increment per spike). Sign can encode excitation/inhibition.
  int16_t  pot_value;                                       // Raw ADC reading (0..4095)
  float    pot_scaling;                                     // Counts-per-gain-unit
  // --- State
  uint8_t  spikeState;                                      // Last read digital level 
  uint8_t  lastSpikeState;                                  // For edge detection of digital spike input
  bool     risingEdge;                                      // Edge detection bool
  float    current;                                         // Synaptic current state (uA). Decays exponentially each tick.
  float    decay;                                           // Per-tick decay factor in (0..1). Closer to 1 = slower decay.
  float    defaultdecay;
  float    Vm;                                              // Mapped presynaptic Vm in internal model units (mV)
  uint16_t Vm_input;                                        // Raw ADC reading (counts) for presynaptic Vm
  // --- ADC calibration for Vm mapping
  float analogOffsetLow;                                    // ADC count corresponding to "low" reference in mapfloat 
  float analogOffsetHigh;                                   // ADC count offset for high-end reference in mapfloat
  // --- Control flags
  bool  use_syn_pot;
  bool  decay_enable;                                       // Activate GUI decay input
};
inline Synapse syn1 = {
  .pin_digital      = pins.gpio.syn1_d,
  .pin_analog       = pins.adc2.syn1_a,
  .pot_pin          = pins.adc1.syn1_pot,
  .pot_raw          = 0,
  .pot_raw_filter   = 0,
  .gain             = 0,                                  
  .pot_value        = 0,
  .pot_scaling       = 1 / (bits12/50.0f),
  .spikeState       = LOW,
  .lastSpikeState   = LOW,
  .risingEdge       = false,
  .current          = 0.0f,
  .decay            = 0.995f,
  .defaultdecay     = 0.995f,
  .Vm               = 0.0f,
  .Vm_input         = 0,
  .analogOffsetLow  = 0.0f,
  .analogOffsetHigh = 1425.0f,
  .use_syn_pot      = true,
  .decay_enable     = true
};
inline Synapse syn2 = {
  .pin_digital      = pins.gpio.syn2_d,
  .pin_analog       = pins.adc2.syn2_a,
  .pot_pin          = pins.adc1.syn2_pot,
  .gain             = 0,
  .pot_value        = 0,
  .pot_scaling      = 1 / (bits12/50.0f),
  .spikeState       = LOW,
  .current          = 0.0f,
  .decay            = 0.990f,
  .defaultdecay     = 0.990f,
  .Vm               = 0.0f,
  .Vm_input         = 0, 
  .analogOffsetLow  = 0.0f,
  .analogOffsetHigh = 1425.0f,
  .use_syn_pot      = true,
  .decay_enable     = true
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                        Stimuli parameters                         */

struct Stimulus {
  // --- Hardware
  int     pin_stim_light;                                   // PWM output pin driving the stimulus LED
  int     pin_stim_current;                                 // DAC output pin driving the stimulus-out analog (loopback to Current-In)
  int     pin_strPot;                                       // ADC pin for stimulus strength pot
  int     pin_freqPot;                                      // ADC pin for stimulus frequency pot
  PotFilter strPot_filt;                                     // Filter state for stimulus strength pot
  PotFilter freqPot_filt;                                    // Filter state for stimulus frequency pot
  // --- Strength pot acquisition + mapping
  int     strPot_raw;                                       // Raw ADC reading for strength pot (0..4095)
  int     strPot;                                           // Filtered ADC reading;
  float   strPot_f;                                         // Filter accumulator for strength ADC.
  int     strPot_centered;                                  //Centered strength pot counts: strPot - half_range (≈ -2048…+2047).
  int     strPot_adj;                                       //Dead-zone–adjusted strength value (centered with ±offset removed). 
  float   str_digitalMap;                                   // Scale: ADC-centered counts -> str_digital units (e.g., percent -100..+100)
  int16_t str_digital;                                      // Signed digital strength command (e.g., -100..+100). Negative -> LED off
  float   str_analogMap;                                    // Scale: ADC counts -> str_analog units (e.g., -100..+100 after offset)
  int16_t str_analog;                                       // Signed analog strength command (e.g., -100..+100). Sign used for polarity
  int     str_analog_min;                                   // Dead-zone threshold for analog polarity detection (prevents jitter)
  // --- Frequency pot acquisition + mapping
  int     freqPot_raw;                                      // Raw ADC reading for frequency pot (0..4095)
  int     freqPot;                                          // Filtered ADC reading;
  float   freqPot_f;                                        // Filter accumulator for frequency ADC.
  int     freqPot_centered;                                 // Centered frequency pot counts: freqPot - half_range.
  int     freqPot_adj;                                      // Dead-zone–adjusted centered frequency.
  int     freq;                                             // Signed frequency modifier (mapped units; used to compute steps/period)
  // --- Polarity
  float   sign;                                             // Stimulus polarity
  float   denom;
  float   freq_map_full;
  // Custom command conditioning (host/serial smoothing + deadband)
  int     cmd_in;                                           // Latest raw custom command (copy of value_custom)
  int     cmd_hold;                                         // Held command after deadband (prevents +/-1 LSB chatter)
  float   cmd_f;                                            // IIR filtered command (float accumulator)
  int     cmd;                                              // Final filtered command (rounded to int)
  int     cmd_abs;                                          // Absolute value of cmd (magnitude)
  bool    custom_active;                                    // True when cmd magnitude exceeds dead-zone threshold
  int     cmd_deadband;                                     // Deadband threshold in LSB (0 disables deadband)
  float   cmd_alpha;                                        // IIR alpha in [0..1] (1.0 disables smoothing)
  // -- Output amplitudes (pre-gating)
  int     value_digital;                                    // PWM amplitude command before duty-cycle gating (0..ledc_Max)
  int     value_analog;                                     // DAC amplitude command before duty-cycle gating (0..dac_max)
  int     value_custom;                                     // Custom stimulus command from host/serial (signed; sign = polarity)
  float   current_scaling;                                  // Scale factor mapping analog strength units -> DAC counts
  int     amp;
  // -- Duty-cycle waveform state (pot mode)
  int     counter;                                          // Tick counter within stimulus period
  int     steps;                                            // Period length in ticks (full period). ON phase uses steps/2.
  int     dutyCycle;                                        // Base period (ticks) before applying freq modifier
  int     dutyCycle_Min;                                    // Minimum allowed period (ticks)
  float   steps_f;                                          // Period length in float format
  float   state;                                            // “Stim active” indicator for telemetry (0 = OFF; nonzero = ON, may encode sign)
  int     trigger;                                          // One-tick pulse marking start of each stimulus period (for logging)
  int     pwm;                                              // Phase-gated PWM output actually written this tick
  int     dac;                                              // Phase-gated DAC output actually written this tick
  uint16_t dacVal;                                          // 12-bit DAC code [0..dac_max] (MCP4922 => 0..4095)
  // --- Control flags
  bool    custom_disable;                                   // true => custom stimulus ON  (host/serial uses value_custom) / false => custom stimulus OFF (pot mode)
  bool    trigger_enable;                                   // Internal “pending trigger” flag (can be replaced by (counter==0))
  bool    serialTrigger_enable;                             // Host-requested trigger pulse (used in custom mode)
};
inline Stimulus stim{
  .pin_stim_light       = pins.gpio.stim_d,
  .pin_stim_current     = pins.gpio.stim_a,
  .pin_strPot           = pins.adc1.stim_str_pot,
  .pin_freqPot          = pins.adc1.stim_freq_pot,
  .strPot_raw           = 0,
  .strPot               = 0,
  .strPot_f             = bits12 * 0.5f,
  .strPot_centered      = 0,
  .strPot_adj           = 0,
  .str_digitalMap       = 100.0f / ((bits12 / 2) - pot.offset),
  .str_digital          = 0,
  .str_analogMap        = 100.0f / ((bits12 / 2) - pot.offset),
  .str_analog           = 0,
  .str_analog_min       = 5,
  .freqPot_raw          = 0,
  .freqPot              = 0,
  .freqPot_f            = bits12 * 0.5f,
  .freqPot_centered     = 0,
  .freqPot_adj          = 0,
  .freq                 = 0,           
  .sign                 = 0.0f,
  .denom                = 0.0f,
  .freq_map_full        = 0.0f,
  .cmd_in               = 0,
  .cmd_hold             = 0,
  .cmd_f                = 0.0f,
  .cmd                  = 0,
  .cmd_abs              = 0,
  .custom_active        = false,
  .cmd_deadband         = 2,          // Equivalent to kCmdDeadband
  .cmd_alpha            = 0.25f,      // Equivalent to kCmdAlpha
  .value_digital        = 0,                              
  .value_analog         = 0,                              
  .value_custom         = 0,
  .current_scaling = (float)stim_dac_span / 100.0f,
  .amp                  = 0,                     
  .counter              = 0,                              
  .steps                = 0,                              
  .dutyCycle            = 500,                            
  .dutyCycle_Min        = 10,                             
  .steps_f              = 0.0f,
  .state                = 0.0f,                             
  .trigger              = 0,
  .pwm                  = 0,
  .dac                  = 0,
  .dacVal               = 0,
  .custom_disable       = true,
  .trigger_enable       = false,
  .serialTrigger_enable = false,
};




// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Axon parameters                           */

struct Axon {
  // --- Hardware
  uint8_t  pin_digital;                                   // TTL "spike out" pin (axon digital output)
  uint8_t  pin_analog;                                    // DAC "Vm out" pin (axon analog output) 
  // --- Output state
  float    Vm;                                            // Store the *analog output representation*
  // --- DAC mapping helpers
  float    Vm_range;                                      // Precomputed 1/(Vm_max - Vm_min) for mapping v_out -> normalized [0..1]
  float    norm;                                          // Working variable: normalized v_out in [0..1] before quantization
  uint8_t  dacVal;                                        // Quantized 8-bit DAC code written to pin_analog (0..255)
};
inline Axon axon{
  .pin_digital  = pins.gpio.axon_d,
  .pin_analog   = pins.gpio.axon_a,
  .Vm           = 0.0f,
  .Vm_range     = 1.0f / (neuron.Vm_max - neuron.Vm_min),
  .norm         = 0.0f,
  .dacVal       = 0
};



// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Spike parameters                          */
 
struct Spike {
  // --- Gain mapping from Vm range to PWM range
  float    led_Vm;                                        // [PWM counts per mV] scaling factor for red LED Vm encoding
  float    led_Vm_pwmf;                                   // Floating-point PWM duty computed from Vm before clamp/quantization
  int      led_Vm_pwm;                                    // Quantized PWM duty in integer counts (0..ledc_Max)
  // --- LEDC PWM configuration
  int      ledc_Resolution;                               // PWM resolution in bits: duty cycle range 0 - 1023   
  int      ledc_Max;                                      // Maximum duty count for current resolution (=(1<<res)-1)
  int      ledc_Freq  = 20000;                            // PWM frequency in Hz (20 kHz, above audible range to avoid coil whine)
  // --- Cached last duty values written to LEDC channels (used to skip redundant hardware writes)
  uint16_t led_r_last;                                    // Last PWM duty sent to red channel
  uint16_t led_g_last;                                    // Last PWM duty sent to green channel
  uint16_t led_b_last;                                    // Last PWM duty sent to blue channel
  // --- UI/host toggles
  bool     Buzzer_enable;                                 // Enables spike buzzer / spike indicator GPIO output 
  bool     LED_enable;                                    // Enables RGB LED Vm/spike visualization
}; 
inline Spike spike{
  .led_Vm          = bits10 / (neuron.Vm_peak - neuron.Vm_min),
  .led_Vm_pwmf     = 0.0f,
  .led_Vm_pwm      = 0,
  .ledc_Resolution = 10,
  .ledc_Max        = (1 << 10) - 1,
  .ledc_Freq       = 20000,
  .led_r_last      = 0,
  .led_g_last      = 0,
  .led_b_last      = 0,
  .Buzzer_enable   = true,
  .LED_enable      = true,
};


// -----------------------------------------------------------------------------
// Fault-wired RGB Vm / spike LED helpers
// -----------------------------------------------------------------------------
//
// Physical wiring mistake on V2.5 board:
//
//   GPIO27 = RGB common anode / LED power, active HIGH, PWM
//   GPIO14 = green cathode, active LOW
//   GPIO12 = blue cathode, active LOW
//   red cathode = permanently connected to GND through resistor
//
// Consequence:
//   - red brightness is controlled only by PWM on GPIO27
//   - green and blue can only be added by pulling their cathodes LOW
//   - Vm display must therefore be red-only
//   - spike flash is made by turning power fully ON and pulling green/blue LOW
//

inline void writeFaultRgbLed(uint16_t powerDuty, bool greenOn, bool blueOn) {
  powerDuty = constrain(powerDuty, 0, spike.ledc_Max);

  // Cache logical display state.
  // led_r_last = common-anode power PWM duty.
  // led_g_last / led_b_last = logical brightness cache only.
  spike.led_r_last = powerDuty;
  spike.led_g_last = greenOn ? spike.ledc_Max : 0;
  spike.led_b_last = blueOn  ? spike.ledc_Max : 0;

  // GPIO27 controls the common anode / LED power.
  // Higher duty = brighter red, because red cathode is hardwired to GND.
  ledcWrite(pins.gpio.led_r, powerDuty);

  // Green and blue are cathodes, active LOW.
  digitalWrite(pins.gpio.led_g, greenOn ? LOW : HIGH);
  digitalWrite(pins.gpio.led_b, blueOn  ? LOW : HIGH);
}


inline void setVmRgbLed(uint16_t vmDuty) {
  // Vm display: red only.
  // Green and blue must stay OFF, otherwise Vm colour will not be red.
  writeFaultRgbLed(vmDuty, false, false);
}


inline void setSpikeRgbLedWhite() {
  // Spike display: full power + green/blue cathodes pulled LOW.
  // Red is automatically ON because its cathode is permanently connected to GND.
  writeFaultRgbLed(spike.ledc_Max, true, true);
}


inline void setRgbLedOff() {
  // Power OFF and active-low cathodes released HIGH.
  writeFaultRgbLed(0, false, false);
}

inline void calibrate_StimulusCurrentInZero() {

  const int n = 256;
  uint32_t acc = 0;

  for (int i = 0; i < n; i++) {
    acc += ADC2.read(patch.pin);
    delayMicroseconds(200);
  }

  patch.current_in_zero = (float)acc / (float)n;
  patch.input_value_f   = patch.current_in_zero;
  patch.input_value     = (uint16_t)lroundf(patch.current_in_zero);
}

inline void neutralise_StimulusCurrentIn() {

  patch.pot_centered  = 0.0f;
  patch.pot_adj       = 0.0f;
  patch.current_input = 0.0f;

  if (clampMode == ClampMode::VoltageClamp) {
    patch.v_step = 0.0f;
    patch.v_cmd  = constrain(patch.v_hold, neuron.Vm_min, neuron.Vm_peak);
  }
}

// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Hardware Settings                         */

inline void init_PotFilters() {

  // --- Patch knob (bipolar detent) ---
  patch.pot_filt.alpha    = pot.alpha_pot;                                         // Use global default smoothing
  patch.pot_filt.deadband = pot.deadband_detent;                                   // Use detent deadband
  patch.pot_filt.reset(ADC1.read(patch.pot_pin));                                  // Seed filter with a real reading

  // --- Noise knob (unipolar, smooth) ---
  noise.pot_filt.alpha    = pot.alpha_pot;                                         // Same smoothing (tune if desired)
  noise.pot_filt.deadband = pot.deadband_smooth;                                   // Smaller deadband for smooth control
  noise.pot_filt.reset(ADC1.read(noise.pot_pin));                                  // Seed filter with a real reading

  // --- Photodiode gain knob (bipolar detent) ---
  PD.pot_filt.alpha       = pot.alpha_pot;                                         // Use global default smoothing
  PD.pot_filt.deadband    = pot.deadband_detent;                                   // Use detent deadband
  PD.pot_filt.reset(ADC1.read(PD.pot_pin));                                        // Seed filter with a real reading

  // --- Synapse gain knobs (bipolar detent) ---
  syn1.pot_filt.alpha     = pot.alpha_pot;                                         // Use global default smoothing
  syn1.pot_filt.deadband  = pot.deadband_detent;                                   // Use detent deadband
  syn1.pot_filt.reset(ADC1.read(syn1.pot_pin));                                    // Seed filter with a real reading

  syn2.pot_filt.alpha     = pot.alpha_pot;                                         // Use global default smoothing
  syn2.pot_filt.deadband  = pot.deadband_detent;                                   // Use detent deadband
  syn2.pot_filt.reset(ADC1.read(syn2.pot_pin));                                    // Seed filter with a real reading

  // --- Stimulus strength/frequency knobs (bipolar detent) ---
  stim.strPot_filt.alpha    = pot.alpha_pot;                                       // Use global default smoothing
  stim.strPot_filt.deadband = pot.deadband_detent;                                 // Use detent deadband
  stim.strPot_filt.reset(ADC1.read(stim.pin_strPot));                              // Seed filter with a real reading

  stim.freqPot_filt.alpha    = pot.alpha_pot;                                      // Use global default smoothing
  stim.freqPot_filt.deadband = pot.deadband_detent;                                // Use detent deadband
  stim.freqPot_filt.reset(ADC1.read(stim.pin_freqPot));                            // Seed filter with a real reading
}

inline void HardwareSettings(){

  delay(500);                                               // Give USB/Serial a moment after reset (ESP32 can enumerate slowly)
  Serial.begin(BaudRate);                                   // Start UART for CLI + streaming at the configured baud rate
  delay(500);                                               // Extra settle time so the host opens the port before first prints



  pinMode(pins.gpio.spike,  OUTPUT);                        // Buzzer / spike digital output pin (TTL gate for buzzer / spike pulse)
  pinMode(pins.gpio.axon_d, OUTPUT);                        // Axon digital output (TTL spike output to BNC / header)
  pinMode(pins.gpio.stim_d, OUTPUT);                        // Stimulus digital output (TTL stim gate / square-wave output)
  
  pinMode(pins.gpio.led_r,  OUTPUT);                        // RGB common anode / LED power, active HIGH PWM
  pinMode(pins.gpio.led_g,  OUTPUT);                        // Green cathode, active LOW
  pinMode(pins.gpio.led_b,  OUTPUT);                        // Blue cathode, active LOW
  
  pinMode(pins.gpio.syn1_d, INPUT);                         // Synapse 1 digital input (external trigger / synapse gate)
  pinMode(pins.gpio.syn2_d, INPUT);                         // Synapse 2 digital input (external trigger / synapse gate)

  pinMode(pins.gpio.mode,   INPUT_PULLDOWN);                // Mode button: pulled-down, pressed = HIGH 


  // Only GPIO27 uses PWM, GPIO14 and GPIO12 are active-low digital cathode switches.
  ledcAttach(pins.gpio.led_r, spike.ledc_Freq, spike.ledc_Resolution);

  ledcAttach(pins.gpio.stim_d, spike.ledc_Freq, spike.ledc_Resolution); // Attach LEDC PWM to stim TTL pin (for analog-ish PWM output)

  

  digitalWrite(pins.gpio.spike,  LOW);                      // Force buzzer/spike output LOW at boot (avoid accidental beep)
  digitalWrite(pins.gpio.axon_d, LOW);                      // Force axon TTL LOW at boot (avoid false spike on connected devices)
  digitalWrite(pins.gpio.stim_d, LOW);                      // Force stim TTL LOW at boot (avoid unintended stimulus)

  // Safe LED-off state for the faulty RGB wiring.
  // GPIO27 power OFF, green/blue active-low cathodes released HIGH.
  digitalWrite(pins.gpio.led_r, LOW);
  digitalWrite(pins.gpio.led_g, HIGH);
  digitalWrite(pins.gpio.led_b, HIGH);

  ledcWrite(pins.gpio.led_r,     0);                        // Start PWM duty at 0 (LED fully off)

  ledcWrite(pins.gpio.stim_d, 0);                           // Start stim PWM duty at 0 (no stimulus output)
  dacWrite(pins.gpio.stim_a, stim_dac_zero);
  dacWrite(pins.gpio.axon_a, axon.dacVal);

  modeBtn.lastStable = modeBtn.lastRaw = digitalRead(pins.gpio.mode); // Seed debouncer with current level (prevents boot toggle)

  randomSeed(esp_random());                                 // Seed pseudo-RNG using ESP32 hardware RNG (used for noise, etc.)
  
  // Put all SPI chip-selects in a safe inactive state
  pinMode(pins.spi.cs_adc1, OUTPUT); digitalWrite(pins.spi.cs_adc1, HIGH);
  pinMode(pins.spi.cs_adc2, OUTPUT); digitalWrite(pins.spi.cs_adc2, HIGH);
  // Start SPI 
  SPI.begin(pins.spi.sck, pins.spi.miso, pins.spi.mosi, -1);// Start SPI bus (explicit SCK/MISO/MOSI; no HW CS pin used here)
  // Initialise devices (library-specific)
  ADC1.begin(pins.spi.cs_adc1);                             // Initialize external ADC #1 with its chip-select pin
  ADC2.begin(pins.spi.cs_adc2);                             // Initialize external ADC #2 with its chip-select pin  

  calibrate_StimulusCurrentInZero();
  
  init_PotFilters();                                        // Seed all pot filters so first readings are stable (reduces startup jitter)
}




// // // // // // // // // // // // // // // // // // // // // // // //
/*                          mapfloat helper                          */

inline float mapfloat(float x, float in_min, float in_max, float out_min, float out_max)
{
  return (float)(x - in_min) * (out_max - out_min) / (float)(in_max - in_min) + out_min;
}



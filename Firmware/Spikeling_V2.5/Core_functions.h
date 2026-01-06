#pragma once     
#include "Serial_functions.h"



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                       Setting Neuronal Mode                                           */

inline void poll_ModeButton() {
  modeBtn.raw    = digitalRead(pins.gpio.mode);                                               // Sample raw level (LOW released, HIGH pressed)
  modeBtn.now_ms = millis();                                                                  // Sample time for debounce timing
}

inline void update_NeuronMode() {

  if (modeBtn.raw != modeBtn.lastRaw) {                                                       // Track raw transitions and reset debounce timer when raw changes
    modeBtn.lastRaw = modeBtn.raw;                                                            // Save new raw state
    modeBtn.lastChange_ms = modeBtn.now_ms;                                                   // Start debounce timing from this change
  }
  
  if ((modeBtn.now_ms - modeBtn.lastChange_ms) < modeBtn.debounce_ms) {                       // Ignore changes until input has been stable long enough
    return;                                                                                   // Not stable yet
  }
 
  if (modeBtn.raw != modeBtn.lastStable) {                                                    // Debounced edge detected
    modeBtn.lastStable = modeBtn.raw;                                                         // Commit new stable state
    
    if (modeBtn.lastStable == HIGH) {                                                         // INPUT_PULLDOWN: press event is rising edge (LOW -> HIGH)
      int next = neuron.mode + 1;                                                             // Advance to next mode index
      if (next >= neuron.nModes) next = 0;                                                    // Wrap around
      ApplyNeuronModeIndex(next);                                                             // Apply mode + update LEDs + update model
    }
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                      Clamp control: current clamp vs voltage clamp                                    */

// In CurrentClamp mode, the "PC" knob/GUI directly injects current (I-clamp style).
// In VoltageClamp mode, the same knob/GUI defines a command voltage (v_cmd), and a PI controller
// Computes the injected clamp current (I_clamp) so that neuron.v tracks v_cmd.

inline void update_VoltageCommand() {
  if (!PC.vcmd_enable) return;                                                              // If GUI/serial is overriding v_cmd, don't read the pot

  // Raw ADC is [0..4095]; center around 0 and apply a deadzone to avoid jitter near mid-point.
  float centered = float(ADC1.read(PC.pot_pin)) - float(bits12) * 0.5f;

  if (centered >= pot.offset) {
    centered -= pot.offset;
  } else if (centered <= -pot.offset) {
    centered += pot.offset;
  } else {
    centered = 0.0f;
  }

  const float denom = float(bits12) * 0.5f - float(pot.offset);                              // ~ (2048 - offset)
  float frac = (denom > 1.0f) ? (centered / denom) : 0.0f;                                   // frac in [-1..+1]
  frac = constrain(frac, -1.0f, 1.0f);

  // Command voltage is centered on v_rest for intuitive use in teaching labs.
  PC.v_cmd = neuron.v_rest + frac * PC.v_cmd_span;
  PC.v_cmd = constrain(PC.v_cmd, neuron.Vm_min, neuron.Vm_peak);
}


inline void update_InputCurrent() {
  
  
  if (clampMode == ClampMode::VoltageClamp) {                                                // If we are in Voltage Clamp mode...
    if (!PC.vcmd_enable) return;                                                             // Voltage clamp: pot controls Vhold ONLY if not overridden by GUI
    
    PC.pot_value = ADC1.read(PC.pot_pin) - bits12/2;                                         // Reads PC potentiometer value and scales it to -2048..2048
    
    float PC_value = 0.0f;                                                                   // Will hold the “effective knob command” after applying a dead-zone.
    
    if (PC.pot_value >= pot.offset) {                                                        // If knob is sufficiently above center (past dead-zone)...
      PC_value = (PC.pot_value - pot.offset) / PC.pot_scaling;                                 // ...subtract the dead-zone edge and scale to engineering units.
    } 
    else if (PC.pot_value <= -pot.offset) {                                                  // If knob is sufficiently below center (past dead-zone)...
      PC_value = (PC.pot_value + pot.offset) / PC.pot_scaling;                                 // ...add the dead-zone edge (note the sign) and scale to units.
    }

    PC.v_hold = constrain(neuron.v_rest + PC_value, neuron.Vm_min, neuron.Vm_peak);          // ...interpret knob command as a ΔV around v_rest, then clamp to safe range.
    PC.v_cmd  = constrain(PC.v_hold + PC.v_step, neuron.Vm_min, neuron.Vm_peak);
    return;
  } 
  
  if (!PC.enable) return;                                                                    // If GUI/serial is overriding the clamp, don't read the pot

  PC.pot_value = ADC1.read(PC.pot_pin) - bits12/2;                                           // Reads PC potentiometer value and scales it to -2048..2048

  float PC_value = 0.0f;                                                                     // Will hold the “effective knob command” after applying a dead-zone.

  if (PC.pot_value >= pot.offset) {                                                          // If knob is sufficiently above center (past dead-zone)...
    PC_value = (PC.pot_value - pot.offset) / PC.pot_scaling;                                 // ...subtract the dead-zone edge and scale to engineering units.
  } 
  else if (PC.pot_value <= -pot.offset) {                                                    // If knob is sufficiently below center (past dead-zone)...
    PC_value = (PC.pot_value + pot.offset) / PC.pot_scaling;                                   // ...add the dead-zone edge (note the sign) and scale to units.
  } 
  else {                                                                                     // Otherwise knob is inside the dead-zone...
    PC_value = 0.0f;                                                                           // ...treat it as zero command (prevents drift/jitter around center).
  }
  PC.current_clamp = PC_value;                                                               // Interpret the knob command as injected current and store it.
}




// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                          Noise Generator                                              */

inline void update_Noise() {  
  if (!noise.enable) return;                                                                  // If GUI/serial override is active (noise.enable == false), don't use the pot
  
  noise.pot_value = ADC1.read(noise.pot_pin);                                                 // Reads Noise potentiometer value from 0 to 4095                                                             
  
  if (noise.pot_value <= pot.offset){                                                         // If Noise potentiometer value is below the offset:
    noise.current = 0.0f;                                                                       // Set Noise current to 0
    return;                                                                                     // Return to caller and pass the rest of the void function
  }

  noise.amp = (noise.pot_value - pot.offset) / noise.pot_scaling;                             // Generates Noise amplitude from the reading, substracts the offset and scales it from parameters
  
  noise.newSigma = 0.5f * noise.amp;                                                          // Generate a standard variation (σ) equal to half the Noise amplitude
  
  if (fabsf(noise.newSigma - noise.sigma) > 1e-3f) {                                       // Update Gaussian parameters if sigma has changed significantly
    noise.sigma = noise.newSigma;                                                             // Stores the new σ in the struct
    noise.var = noise.sigma * noise.sigma;                                                    // Compute the variance (σ²) as a double,

    using DistFloat = decltype(noise.dist.variance);                                          // Cast from float to whatever type Gaussian uses
    noise.dist.variance = static_cast<DistFloat>(noise.var);                                  // Update the Gaussian distribution’s variance so that future calls to noise.dist.random() use the new σ².
    noise.dist.mean     = static_cast<DistFloat>(noise.mean);                                 // Keeps mean as it is
  }

  noise.current = static_cast<float>(noise.dist.random());                                  // Draws one random sample from the Gaussian and generates Noise current from drawing one random sample from the Noisy gaussian 
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                              PhotoDiode                                               */

inline void update_Photodiode() {
  PD.value = ADC2.read(PD.pin);                                                               // Reads Photodiode value from 0 to ~400

  // Store new value in ring buffer
  PD.sum -= PD.values[PD.counter];                                                            // remove old sample
  PD.values[PD.counter] = PD.value;                                                           // store new sample
  PD.sum += PD.value;                                                                         // add new sample
  PD.counter ++;                                                                              // Increment the counter by 1
  if (PD.counter >= PD.avgWindow) {                                                           // If, for this void loop, the counter has reached the max count number:
    PD.counter = 0;                                                                             // Reset the counter to 0
  }
  PD.average = PD.sum / PD.avgWindow;                                                         // Generate an average Photodiode value from the 10 latest reading samples

// Get potentiometer value
  if (PD.gain_enable){                                                                        // If the board Photodiode Gain is enabled:
    PD.pot_value = ADC1.read(PD.pot_pin) - bits12/2;                                            // Reads Photodiode Gain potentiometer value and scales it to -2048 to 2048
    
    if (PD.pot_value >= pot.offset){                                                            // If PD potentiometer value is above the offset:
        PD.gain = (PD.pot_value - pot.offset) / PD.pot_scaling;                                   // Generates gain value from the reading, subtracts the offset and scales it from parameters
    } 
    else if (PD.pot_value <= -pot.offset){                                                      // If PD potentiometer value is below the offset:
      PD.gain = (PD.pot_value + pot.offset) / PD.pot_scaling;                                     // Generates gain value from the reading, add the offset and scales it from parameters
    }
    else{                                                                                       // If PD potentiometer value is within offset range:
      PD.gain = 0.0f;                                                                             // Set PD Gain to 0
    }
  }
    
  PD.polarity = (PD.gain >= 0.0f) ? 1 : -1;                                                   // Set Photodiode polarity (positive if gain above 0, negative if gain stricly below 0)

  PD.current = (PD.average * PD.gain * PD.inv_scaling) * PD.amp;                              // Generates Photodiode current, amplified by the PD_Gain readings

  if (PD.decay_enable){                                                                       // If the GUI Photodiode Decay is disabled 
    PD.decay = 0.001f;                                                                          // Set Photodiode Decay by default to 0.001
  }

  if (PD.amp > PD.ampMin){                                                                    // If Photodiode Amplification is above the minimum value:
    PD.amp -= PD.polarity * PD.decay * PD.current;                                              // Adapts the Amplification proportionally to the photodiode current
    if (PD.amp < PD.ampMin){                                                                    // If Photodiode Amplification becomes lower than the minimum value:
      PD.amp = PD.ampMin;                                                                         // Then Photodiode Amplification remains at the minimum value
    }
  }

  if (PD.recovery_enable){                                                                    // If the GUI Photodiode Recovery is disabled:
    PD.recovery = 0.025f;                                                                       // Set Photodiode Recovery by default to 0.025
  }

  if (PD.amp < 1.0f){                                                                         // If Photodiode Amplification is below 1:
    PD.amp +=  PD.recovery;                                                                     // Increment Photodiode Amplification by Photodiode Recovery 
  }
}




// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                              Synapses                                                 */

inline void update_Synapse(Synapse &syn, float defaultDecay) {

  syn.spikeState = digitalRead(syn.pin_digital);                                              // Reads Synapse digital spike input

  if (syn.gain_enable){                                                                       // If the board Synapse Gain is enabled:
    syn.pot_value = ADC1.read(syn.pot_pin) - bits12/2;                                          // Reads Synaptic Gain potentiometer value and scales it to -2048 to 2048
    
    if (syn.pot_value >= pot.offset){                                                           // If the Synaptic Gain is above offset:
      syn.gain = (syn.pot_value - pot.offset) / syn.pot_scaling;                                       // Generates Synaptic Amplification 1 from the reading, substracts the offset and scales it from parameters
    }
    else if (syn.pot_value <= -pot.offset){                                                     // If the Synaptic Gain is below offset:
      syn.gain = (syn.pot_value + pot.offset) / syn.pot_scaling;                                       // Generates Synaptic Amplification from the reading, adds the offset and scales it from parameters
    } 
    else{                                                                                       // If the Synaptic Gain is within offset range:
      syn.gain = 0.0f;                                                                            // Set Synaptic Amplication to 0
    }
  }
  
  if (syn.spikeState == HIGH){                                                                // If Spike on Synapse is detected
    syn.current += syn.gain;                                                                     // Generates Synaptic current by incrementing Synaptic Amplification
  }
  
  if (syn.decay_enable == true){                                                              // If the GUI Synaptic Decay 1 is disabled: 
    syn.decay = defaultDecay;                                                                   // Set Synpatic Decay to default value
  }
  
  syn.current *= syn.decay;                                                                   // Decrement Synaptic 1 current towards zero

  syn.Vm_input = ADC2.read(syn.pin_analog);                                                   // Reads Synapse Vm input
  syn.Vm = mapfloat(syn.Vm_input,
                    syn.analogOffsetLow,
                    bits12 - syn.analogOffsetHigh, 
                    neuron.Vm_min, 
                    neuron.Vm_max) + axon.offset;                                             // Maps Synapse Vm to Spikeling Neuron range
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                         Total input current                                           */

inline void compute_AllCurrent() {                                                            // Define the inline function that computes neuron.total_current.

/*              --  Select the “primary command current” based on clamp mode  --              */
  // In CurrentClamp: the command is simply the current from the clamp pot (PC.current_clamp).
  // In VoltageClamp: the command is the PI controller output current (PC.I_clamp) that enforces Vcmd.
  float PatchClamp_current = (clampMode == ClampMode::VoltageClamp)                           // Check if we are in voltage clamp mode...
                ? PC.I_clamp                                                                    // ...use PI clamp current as the command.
                : PC.current_clamp;                                                             // ...otherwise use pot-defined injected current.

/*                               --  Current-In contribution  --                               */
  // - In CurrentClamp, include Current-In (StimOut->CurrentIn loopback generates PC.current)
  // - In VoltageClamp, exclude it (avoid disturbance-current labs)
  const float CurrentIn_current = (clampMode == ClampMode::VoltageClamp)                       // If voltage clamp...
                                ? 0.0f                                                         // ...ignore Current-In to keep VC protocols clean
                                : PC.current;                                                  // ...else include Current-In in current clamp mode


/*           --  Sum all current sources into the neuron’s total injected current  --           */
  neuron.total_current = PatchClamp_current                                                   // Primary command: pot current (CC) or PI output (VC)
                       + CurrentIn_current                                                    // External Current-In injection (CC only)
                       + PD.current                                                           // Photodiode / light input contribution
                       + syn1.current                                                         // Synapse 1 current contribution
                       + syn2.current                                                         // Synapse 2 current contribution
                       + noise.current;                                                       // Noise injection contribution
}


// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                            Stimulus - Determining Analog and Digital Values                           */

inline void update_StimulusOutput() {

/*                                 --  All Stimulus GUI buttons OFF  --                                  */

  if ( stim.strength_enable && stim.custom_enable ) {                                         // If GUI "Stimulus Strength" and "Custom Stimulus" are disabled:
    stim.strPot = ADC1.read(stim.pin_strPot);                                                   // Reads Stimulus Strength potentiometer value
    stim.str_digital = int16_t((stim.strPot - bits12/2)) * stim.str_digitalMap;                // Maps this value from -100 to 100 that will correspond to the digital (LED output) stimulus strength %
    stim.str_analog = int16_t(stim.strPot * stim.str_analogMap - 100.0f);                       // Maps this value from 0 to 100 that will correspond to the analog (Input Current) stimulus strength %
  }
  
  if ( stim.frequency_enable && stim.custom_enable) {                                         // If GUI "Stimulus Frequency" and "Custom Stimulus" are disabled:
    stim.freqPot = ADC1.read(stim.pin_freqPot);                                                 // Reads Stimulus Frequency potentiometer value
    stim.freq = int16_t(100.0f - stim.freqPot * stim.freq_map);                                 // Maps this value from 100 to -100 
  }

  /*                             --  GUI Custom Stimulus button OFF  --                                    */

  if ( stim.custom_enable ){                                                                  // If GUI "Custom Stimulus" is disabled:
    if ( stim.str_digital >= 0 ){                                                               // If the Stimulus Strength value is positive:
      stim.value_digital = (int)(stim.str_digital * stim.light_scaling);                          // The stimulus digital output is proportional to the potentiometer reading and scaled from parameters
    }
    else {
      stim.value_digital = 0;
    }

    stim.value_analog = (int)abs(stim.str_analog) * stim.current_scaling;                     // The stimulus analog output absolute value is proportional to the potentiometer reading and scaled to parameters
    
    if ( stim.counter < stim.steps/2 ){                                                       // If the number of void loops has not reached half the stimulus duty cycle:
      stim.pwm = constrain(stim.value_digital, 0, ledc_Max);                                    // Sets the stimulus digital output value for the stimulating LED
      stim.dac = stim.value_analog;                                                             // Sets the stimulus analog output value for the Stimulus current output
      stim.state = stim.str_analog;                                                             // Register stimulus ON state
    }
    else {                                                                                    // If number of void loops has exceeded half the stimulus duty cycle period:
      stim.pwm = 0;                                                                             // Sets the stimulus digital output to 0
      stim.dac = 0;                                                                             // Sets the stimulus analog output to 0                                                                               
      stim.state = 0;                                                                           // Register stimulus OFF state
    }
    
    // Quantize/clamp the *selected* DAC output (already 0 during OFF half-cycle)
    int val = static_cast<int>(stim.dac);                                                     // Use stim.dac (0 or amplitude), not stim.value_analog
    val = constrain(val, 0, dac_max);
    uint8_t dacVal = static_cast<uint8_t>(val);

    ledcWrite(stim.pin_stim_light, stim.pwm);                                                 // PWM is already 0 or amplitude depending on phase
    dacWrite(stim.pin_stim_current, dacVal);                                                  // Write the phase-correct DAC value


    stim.counter ++;                                                                          // Increment the Stimulus counter by 1
    
    if ( !stim.trigger_enable ){                                                              // If the Trigger flag is false:
      stim.trigger = 0;                                                                         // Set Trigger to 0 
    }

    if ( stim.trigger_enable ){                                                               // If the Trigger flag is true:
      stim.trigger = 1;                                                                         // Set Trigger to 1
      stim.trigger_enable = false;                                                              // Disable the Trigger Flag
    }

    if ( stim.counter >= stim.steps ){                                                        // If Stimulus counter has reached the stimulus duty cycle period:
      stim.counter = 0;                                                                         // Reset the void loop counter
      stim.trigger_enable = true;                                                               // Enable the Trigger flag
      float s = stim.dutyCycle + ((stim.freq * stim.dutyCycle) / 100.0f) + stim.dutyCycle_Min;  // Define the stimulus duty cycle period proportional to the stimulus frequency potentiometer value
      stim.steps = (int)(s);                                                                    // Set stimulus steps value
    }
  }
  
  /*                               --  GUI Custom Stimulus Button ON  --                                 */

  else {                                                                                      // If GUI "Custom Stimulus"is enabled:
    stim.trigger = 0;                                                                           // Set Trigger to 0
    if ( stim.serialTrigger_enable ){                                                           // If Serial-Trigger flag is enabled:
      stim.trigger = 1;                                                                           // Set Trigger to 1
      stim.serialTrigger_enable = false;                                                          // Disable Serial-Trigger flag
    }
    if (stim.value_custom > 0){                                                                 // If the Custom Stimulus value is aobve 0:
      stim.value_digital = (stim.value_custom * stim.light_scaling);                              // Applies the serial received stimulus value to the stimulating LED and scales from parameters
    }
    else {                                                                                      // If the Custom Stimulus value is below or equal to 0:
      stim.value_digital = 0;                                                                     // Set the stimulating LED to 0
    }
                                                     
    stim.value_analog = static_cast<int>(stim.value_custom) * stim.current_scaling;             // The stimulus analog output absolute value is scaled to parameters             
    
    int val = static_cast<int>(stim.value_analog);
    val = constrain(val, 0, dac_max);
    uint8_t dacVal = static_cast<uint8_t>(val);
    
    ledcWrite(stim.pin_stim_light, constrain(stim.value_digital, 0, ledc_Max));                 // Sends the stimulus digital output value to the stimulating LED
    dacWrite(stim.pin_stim_current, dacVal);                                                    // Sends the stimulus analog output value to the Stimulus current output
    
    stim.state = stim.value_custom;                                                             // Register stimulus ON state
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                    Stimulus - Applying Analog Values                                  */
 
inline void update_StimulusCurrentIn() {                                                      // Update “Current-In” based stimulus input (ADC2 on MCP3208)
  
  PC.value_currentIn = ADC2.read(PC.pin);                                                     // Read the Current-In ADC channel (typically 0..4095)

  float sign = 0.0f;                                                                          // Will become +1, -1, or 0 depending on requested stimulus polarity

/*                                -----  Determine stimulus sign  -----                                  */

  if (stim.custom_enable) {                                                                   // If GUI "Custom Stimulus" button is OFF -> use analog strength pot sign
    if (stim.str_analog > stim.str_analog_min) {                                                // If Strength pot above +threshold -> positive polarity
      sign = +1.0f;                                                                               // Set sign to positive
    } 
    else if (stim.str_analog < -stim.str_analog_min) {                                          // If Strength pot below -threshold -> negative polarity
      sign = -1.0f;                                                                               // Set sign to negative
    } 
    else {                                                                                      // If Strength pot near 0 (inside dead-zone)
      sign = 0.0f;                                                                                // No polarity -> treat as zero stimulus
    }
  } 
  else {                                                                                      // If GUI "Custom Stimulus" button is ON -> use stim.value_custom sign
    if (stim.value_custom > 0) {                                                                // If Custom value positive
      sign = +1.0f;                                                                               // Positive polarity
    } 
    else if (stim.value_custom < 0) {                                                           // If Custom value negative
      sign = -1.0f;                                                                               // Negative polarity
    } 
    else {                                                                                      // If Custom value exactly zero
      sign = 0.0f;                                                                                // No stimulus (also avoids analog misread/jitter)
    }
  }

/*                             -----  Voltage clamp interpretation  -----                                */
  // In VoltageClamp mode, the same Current-In ADC is reinterpreted as a *command voltage step* (ΔV), not as an injected current. “StimulusOut -> CurrentIn” loopback becomes a V-step protocol.

  if (clampMode == ClampMode::VoltageClamp) {                                                 // If we are in Voltage Clamp mode...
    float mag = (PC.value_currentIn / float(bits12)) * PC.v_step_max;                           // Map ADC magnitude [0..4095] -> [0..v_step_max] (model “mV-ish” units)
    
    if (sign == 0.0f) {                                                                         // If no polarity requested (dead-zone or zero custom)...
      PC.v_step = 0.0f;                                                                           // ...force the step to 0
    } 
    else {                                                                                      // Otherwise polarity is defined...
      PC.v_step = sign * mag;                                                                     // ...apply sign to the magnitude to create ΔV step
    }

    PC.v_cmd = constrain(PC.v_hold + PC.v_step,                                                 // Command voltage = holding potential + step
                         neuron.Vm_min,                                                         // Clamp command lower bound
                         neuron.Vm_peak);                                                       // Clamp command upper bound (safe max)

    PC.current = 0.0f;                                                                          // In V-clamp mode, do NOT also inject current via IC.current (keeps I–V clean)

    return;                                                                                     // Done for VoltageClamp mode
  }

/*                             -----  Current clamp interpretation  -----                                */
  // In CurrentClamp mode, the Current-In ADC is interpreted as an injected current command (I).

  if (sign == 0.0f) {                                                                           // If no polarity requested (dead-zone or custom==0)...
    PC.current = 0.0f;                                                                            // ...force injected current to 0 (prevents analog misreading)
  } 
  else {                                                                                        // Otherwise polarity is defined...
    PC.current = sign * (PC.value_currentIn * PC.currentIn_scaling);                              // Scale ADC to current and apply sign (+ or -)
  }
}


inline void update_VoltageClampPI() {                                                           // Define the inline function that updates the voltage-clamp PI loop.

  if (clampMode != ClampMode::VoltageClamp) {                                                   // If we are NOT in voltage clamp mode...
    PC.I_clamp = 0.0f;                                                                            // ...force PI output to 0 (not used in current clamp mode).
    PC.e_int   = 0.0f;                                                                            // ...reset the integrator so it does not accumulate while inactive.
    return;                                                                                       // Exit early; nothing else to do.
  }

  // ---------------------------- Error computation ----------------------------
  float e = PC.v_cmd - neuron.v;                                                                // Voltage error: positive if neuron.v is below command (needs more depolarizing current).

  // ---------------------------- Proportional term ----------------------------
  float p = PC.Kp * e;                                                                          // Proportional output current: reacts immediately to the present error.

  // ---------------------------- Integral candidate update ----------------------------
  float e_int_candidate = PC.e_int + (e * neuron.dt_ms);                                        // Proposed new integrator state (integrate error over time).

  float i_candidate = PC.Ki * e_int_candidate;                                                  // Integral output current computed from the proposed integrator state.

  // ---------------------------- Unsaturated output ----------------------------
  float out_unsat = p + i_candidate;                                                            // PI output current before applying compliance (saturation).

  // ---------------------------- Apply compliance limits ----------------------------
  float out_sat = out_unsat;                                                                    // Start from the unsaturated value.
  if (out_sat > PC.I_max) out_sat = PC.I_max;                                                   // Clamp to maximum injectable current (positive compliance).
  if (out_sat < PC.I_min) out_sat = PC.I_min;                                                   // Clamp to minimum injectable current (negative compliance).

  // ---------------------------- Anti-windup logic ----------------------------
  // Goal: prevent the integrator from “winding up” when the amplifier is saturated and the error is trying to push it further into saturation.
  bool saturated_high = (out_unsat > PC.I_max);                                                 // True if output hit the high compliance limit.
  bool saturated_low  = (out_unsat < PC.I_min);                                                 // True if output hit the low compliance limit.
  bool error_reduces_high_sat = saturated_high && (e < 0.0f);                                   // If saturated high, a negative error would reduce output (good -> allow integration).
  bool error_reduces_low_sat  = saturated_low  && (e > 0.0f);                                   // If saturated low, a positive error would increase output (good -> allow integration).

  if ((!saturated_high && !saturated_low) ||                                                    // If not saturated at all...
      error_reduces_high_sat ||                                                                   // ...or saturated high but error pulls back...
      error_reduces_low_sat) {                                                                    // ...or saturated low but error pulls back...
        PC.e_int = e_int_candidate;                                                               // Commit the integrator update.
  }                                                                                             // Else: do not integrate this step (prevents runaway integrator windup).

  // ---------------------------- Output assignment ----------------------------
  PC.I_clamp = out_sat;                                                                         // Save the final (compliance-limited) clamp current for injection into the neuron model.
}


// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                       Spike and Axon output                                           */

inline void update_Spike() {

if (clampMode == ClampMode::VoltageClamp) {                                                     // If we are currently operating in Voltage Clamp mode. 
  neuron.v_out = neuron.v;                                                                        // Export the model voltage directly as the output voltage. In voltage clamp we do not generate spike events; we simply report the clamped Vm.
  digitalWrite(axon.pin_digital, LOW);                                                            // Force the axon digital output LOW so no TTL “spike” pulses are emitted. Force the axon digital output LOW so no TTL “spike” pulses are emitted interpreting clamp plateaus/steps as spikes.
  digitalWrite(pins.gpio.spike, LOW);                                                             // Force the spike-indicator GPIO LOW (typically drives a LED / buzzer logic). Avoid “false spike” signals during voltage clamp.

  if ( LED_enable ) {
    // Subthreshold LED encoding still useful: red encodes Vm, others off
    float pwm_f = (neuron.v_out - neuron.Vm_min) * Vm_led_gain;
    int pwm = int(constrain(pwm_f, 0.0f, float(bits10)));
    setLedc(pins.gpio.led_r, pwm, led_r_last);
    setLedc(pins.gpio.led_g, 0, led_g_last);
    setLedc(pins.gpio.led_b, 0, led_b_last);
  }

  float norm = (neuron.v_out - neuron.Vm_min) * axon.Vm_range_inv;
  norm = constrain(norm, 0.0f, 1.0f);
  uint8_t dacVal = static_cast<uint8_t>(norm * dac_max + 0.5f);
  axon.Vm = dacVal;
  dacWrite(axon.pin_analog,axon.Vm);
  return;
}


  if ( neuron.v>= neuron.Vm_spike ) {                                                         // Whenever neuron is considered to be spiking,
    
    neuron.v_out = neuron.Vm_peak;                                                              // Forces the displayed Vm value to Vm_peak
    digitalWrite(axon.pin_digital, HIGH);                                                       // Sends digital output through the Axon digital pin
    
    if ( LED_enable ) {
      // Full white flash on spike
      setLedc(pins.gpio.led_r, ledc_Max, led_r_last);                                             // set red LED to HIGH
      setLedc(pins.gpio.led_g, ledc_Max, led_g_last);                                             // set green LED to HIGH
      setLedc(pins.gpio.led_b, ledc_Max, led_b_last);                                             // set blue LED to HIGH
    }
    if ( Buzzer_enable ) {
      digitalWrite(pins.gpio.spike, HIGH);
    }
  }
    
  else {                                                                                      // Whenever neuron is not spiking
    
    neuron.v_out = neuron.v;                                                                    // The displayed Vm value corresponds to Spikeling Vm
    digitalWrite(axon.pin_digital, LOW);                                                        // Keep the digital output in a LOW state 
    digitalWrite(pins.gpio.spike, LOW);       
                                                                                       
    if ( LED_enable ) {
      // Subthreshold: red encodes Vm, others off
      float pwm_f = (neuron.v_out - neuron.Vm_min) * Vm_led_gain;                                 // Maps pwm value to the displayed Vm on a 10 bits scale
      int pwm = int(constrain(pwm_f, 0.0f, float(bits10)));
      setLedc(pins.gpio.led_r, pwm, led_r_last);                                                  // Set the red LED to the displayed Vm
      setLedc(pins.gpio.led_g, 0, led_g_last);                                                    // Keeps the green LED OFF
      setLedc(pins.gpio.led_b, 0, led_b_last);                                                    // Keeps the blue LED OFF
    }                                                   
  }    

  float norm = (neuron.v_out - neuron.Vm_min) * axon.Vm_range_inv;
  norm = constrain(norm, 0.0f, 1.0f);
  uint8_t dacVal = static_cast<uint8_t>(norm * dac_max + 0.5f);                               // Quantize to 8-bit DAC value [0..255]
  axon.Vm = dacVal;                                                                           // Generates axon Vm by mappint the displayed Vm 
  dacWrite(axon.pin_analog,axon.Vm);                                                          // Sends Axon Vm analog output through the Axon Vm output                                             
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                              Serial                                                   */

inline int16_t q_round(float x) {                                                            // Quantize a scaled float to int16 with symmetric rounding
  if (x >= 0.0f)
    return (int16_t)(x + 0.5f);
  else
    return (int16_t)(x - 0.5f);
}

inline void send_SamplePacket() {
  pkt.v_q        = q_round(neuron.v_out * V_SCALE);                                           // Membrane Potential
  pkt.stim_state = (int16_t)stim.state;                                                       // Stimulus State
  pkt.Itot_q     = q_round(neuron.total_current * I_SCALE);                                   // Total Current
  pkt.syn1_vm_q  = q_round(syn1.Vm * SYN_V_SCALE);                                            // Synapse 1 Membrane Potential
  pkt.Isyn1_q    = q_round(syn1.current * I_SCALE);                                           // Synapse 1 Current
  pkt.syn2_vm_q  = q_round(syn2.Vm * SYN_V_SCALE);                                            // Synapse 2 Membrane Potential
  pkt.Isyn2_q    = q_round(syn2.current * I_SCALE);                                           // Synapse 2 Current
  pkt.trigger_q  = (int16_t)stim.trigger;                                                     // Trigger

  // 2-byte sync header
  const uint8_t header[2] = { 0xAA, 0x55 };
  Serial.write(header, 2);

  Serial.write(reinterpret_cast<uint8_t*>(&pkt), sizeof(pkt));                                // Send raw bytes (16 bytes per packet)

  wifiSendSamplePacket(pkt);
}



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
/*                          PatchClamp control: Current-Clamp vs Voltage-Clamp                           */

inline void update_PatchInput() {

/*   -- In VoltageClamp mode, the patch knob defines a command voltage (v_cmd), and a PI controller --   */  
  if (clampMode == ClampMode::VoltageClamp) {                                                 // If we are in Voltage Clamp mode:
    if (!pot.use_patch_pot) return;                                                             // If GUI is overriding v_cmd, don't read the pot
    
    const uint16_t pot_raw = ADC1.read(patch.pot_pin);                                           // Read Patch knob raw ADC (0..4095)
    const uint16_t pot_adc = patch.pot_filt.update(pot_raw);                                     // Filtered ADC (median + IIR + deadband)
    patch.pot_value = float((int32_t)pot_adc - (int32_t)pot.half_range);                          // Center to -2048..+2047 (float for legacy math)

    if (patch.pot_value >= pot.offset) {                                                        // If centered is positive beyond the deadzone, 
      patch.pot_value -= pot.offset;                                                              // shift it down by offset.
    } else if (patch.pot_value <= -pot.offset) {                                                // If centered is negative beyond the deadzone, 
      patch.pot_value += pot.offset;                                                              // shift it up by offset.
    } else {                                                                                    // Otherwise it’s inside the deadzone,
      patch.pot_value = 0.0f;                                                                     // treat as exactly zero.
    } 

    patch.denom = float(pot.half_range - pot.offset);                                           // Compute the maximum magnitude possible AFTER applying the deadzone.
    patch.frac = (patch.denom > 1.0f) ? (patch.pot_value / patch.denom) : 0.0f;                 // Normalise to a fraction in [-1..+1] (unless denom is invalid/small).
    patch.frac = constrain(patch.frac, -1.0f, 1.0f);                                            // Safety clamp (numerical stability + ensures predictable mapping).

    patch.v_hold = neuron.v_rest + patch.frac * patch.v_cmd_span;                               // Map the normalised knob position to an absolute command voltage.
    patch.v_cmd = constrain(patch.v_hold, neuron.Vm_min, neuron.Vm_peak);                       // Ensure Vcmd cannot exceed model bounds
  } 

/*          -- In CurrentClamp mode, the patch knob directly injects current (I-clamp style) --          */
  else{                                                                                         // If we are in Current Clamp mode:
    if (!pot.use_patch_pot) return;                                                               // If GUI/serial is overriding the clamp, don't read the pot

    const uint16_t pot_raw = ADC1.read(patch.pot_pin);                                           // Read Patch knob raw ADC (0..4095)
    const uint16_t pot_adc = patch.pot_filt.update(pot_raw);                                     // Filtered ADC (median + IIR + deadband)
    patch.pot_value = float((int32_t)pot_adc - (int32_t)pot.half_range);                          // Center to -2048..+2047 (float for legacy math)

    if (patch.pot_value >= pot.offset) {                                                          // If centered is positive beyond the deadzone, 
      patch.current_clamp = (patch.pot_value - pot.offset) * patch.pot_scaling;                    // Subtract the dead-zone edge and scale to engineering units.
    } else if (patch.pot_value <= -pot.offset) {                                                  // If centered is negative beyond the deadzone, 
      patch.current_clamp = (patch.pot_value + pot.offset) * patch.pot_scaling;                    // Add the dead-zone edge and scale to engineering units.
    } else {                                                                                      // Otherwise it’s inside the deadzone,
      patch.current_clamp = 0.0f;                                                                   // treat as exactly zero.
    } 
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                          Noise Generator                                              */

inline void update_Noise() { 

  if (!pot.use_noise_pot) return;                                                             // If GUI/serial override is active (noise.enable == false), don't use the pot
  
  const uint16_t noise_raw = ADC1.read(noise.pot_pin);                                          // Read Noise knob raw ADC (0..4095)
  noise.pot_value = (int16_t)noise.pot_filt.update(noise_raw);                                   // Filtered ADC (stable, reduced jitter)                                                     
  
  if (noise.pot_value <= pot.offset){                                                         // If Noise potentiometer value is below the offset:
    noise.current = 0.0f;                                                                       // Set Noise current to 0
    return;                                                                                     // Retrun and avoidf wasting time computing sigma
  }

  noise.amp = (noise.pot_value - pot.offset) * noise.pot_scaling;                             // Generates Noise amplitude from the reading, substracts the offset and scales it from parameters
  
  noise.newSigma = noise.sigma_per_amp * noise.amp;                                           // Generate a standard variation (σ) equal to half the Noise amplitude
  
  if (fabsf(noise.newSigma - noise.sigma) > noise.kSigmaUpdateEps) {                          // Update Gaussian parameters if sigma has changed significantly
    noise.sigma = noise.newSigma;                                                               // Stores the new σ in the struct
    noise.var = noise.sigma * noise.sigma;                                                      // Compute the variance (σ²)
    noise.dist.variance = noise.var;                                                            // Update the Gaussian distribution’s variance so that future calls to noise.dist.random() use the new σ².
    noise.dist.mean = noise.mean;                                                               // Keeps mean as it is
  }

  noise.current = noise.dist.random();                                                        // Draws one random sample from the Gaussian and generates Noise current from drawing one random sample from the Noisy gaussian 
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                              PhotoDiode                                               */

inline void update_Photodiode() {

  PD.value = ADC2.read(PD.pin);                                                               // Reads Photodiode value from 0 to ~400

  PD.sum -= PD.values[PD.counter];                                                            // Remove old sample
  PD.values[PD.counter] = PD.value;                                                           // Store new sample
  PD.sum += PD.value;                                                                         // Add new sample
  PD.counter ++;                                                                              // Increment the counter by 1
  if (PD.counter >= PD.avgWindow) {                                                           // If, for this void loop, the counter has reached the max count number:
    PD.counter = 0;                                                                             // Reset the counter to 0
  }
  PD.average = PD.sum * PD.avgWindow;                                                         // Generate an average Photodiode value from the 10 latest reading samples

  if (pot.use_photodiode_pot){                                                                // If the board Photodiode Gain is enabled:
    const uint16_t pd_raw = ADC1.read(PD.pot_pin);                                               // Read PD gain knob raw ADC (0..4095)
    const uint16_t pd_adc = PD.pot_filt.update(pd_raw);                                          // Filtered ADC (median + IIR + deadband)
    PD.pot_value = (int16_t)((int32_t)pd_adc - (int32_t)pot.half_range);                          // Center to -2048..+2047
    
    if (PD.pot_value >= pot.offset){                                                            // If PD potentiometer value is above the offset:
        PD.gain = (PD.pot_value - pot.offset) * PD.pot_scaling;                                   // Generates gain value from the reading, subtracts the offset and scales it from parameters
    }else if (PD.pot_value <= -pot.offset){                                                     // If PD potentiometer value is below the offset:
      PD.gain = (PD.pot_value + pot.offset) * PD.pot_scaling;                                     // Generates gain value from the reading, add the offset and scales it from parameters
    }else{                                                                                      // If PD potentiometer value is within offset range:
      PD.gain = 0.0f;                                                                             // Set PD Gain to 0
    }
  } 
  PD.polarity = (PD.gain >= 0.0f) ? 1 : -1;                                                   // Set Photodiode polarity (positive if gain above 0, negative if gain stricly below 0)

  PD.current = (PD.average * PD.gain * PD.scaling) * PD.amp;                                  // Generates Photodiode current, amplified by the PD_Gain readings

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
  if (syn.spikeState == HIGH && syn.lastSpikeState == LOW) {
    syn.risingEdge = true;
  } else {
    syn.risingEdge = false;
  }
  syn.lastSpikeState = syn.spikeState;

  if (syn.use_syn_pot){                                                                       // If the board Synapse Gain is enabled:
    const uint16_t syn_raw = ADC1.read(syn.pot_pin);                                             // Read Syn gain knob raw ADC (0..4095)
    const uint16_t syn_adc = syn.pot_filt.update(syn_raw);                                       // Filtered ADC (median + IIR + deadband)
    syn.pot_value = (int16_t)((int32_t)syn_adc - (int32_t)pot.half_range);                        // Center to -2048..+2047
    
    if (syn.pot_value >= pot.offset){                                                           // If the Synaptic Gain is above offset:
      syn.gain = (syn.pot_value - pot.offset) * syn.pot_scaling;                                  // Generates Synaptic Amplification 1 from the reading, substracts the offset and scales it from parameters
    }else if (syn.pot_value <= -pot.offset){                                                    // If the Synaptic Gain is below offset:
      syn.gain = (syn.pot_value + pot.offset) * syn.pot_scaling;                                  // Generates Synaptic Amplification from the reading, adds the offset and scales it from parameters
    }else{                                                                                      // If the Synaptic Gain is within offset range:
      syn.gain = 0.0f;                                                                            // Set Synaptic Amplication to 0
    }
  }
  if (syn.risingEdge == true){                                                                // If Spike on Synapse is detected
    syn.current += syn.gain;                                                                    // Generates Synaptic current by incrementing Synaptic Amplification
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

inline void update_AllCurrent() {                                                         

/*              --  Select the “primary command current” based on clamp mode  --              */
  if (clampMode == ClampMode::VoltageClamp) {                                                 // If we are in voltage clamp mode
    patch.i_command = patch.I_clamp;                                                            // The command is the PI controller output current that enforces Vcmd.
    patch.i_current = 0.0f;                                                                     // Ignore Current-In to keep VC protocols clean
  }
/*                               --  Current-In contribution  --                               */
  else{                                                                                       // If we are in current clamp mode
    patch.i_command = patch.current_clamp;                                                      // The command is simply the current from the clamp pot 
    patch.i_current = patch.current_input;                                                      // Include current_input (StimOut->current_input loopback generates patch.current)
  }

/*           --  Sum all current sources into the neuron’s total injected current  --           */
  neuron.total_current = patch.i_command                                                      // Primary command: pot current (CC) or PI output (VC)
                       + patch.i_current                                                      // External Current-In injection (CC only)
                       + PD.current                                                           // Photodiode / light input contribution
                       + syn1.current                                                         // Synapse 1 current contribution
                       + syn2.current                                                         // Synapse 2 current contribution
                       + noise.current;                                                       // Noise injection contribution
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                            Stimulus - Determining Analog and Digital Values                           */

inline void update_StimulusOutput() {

  if (stim.custom_disable){                                                                   // If GUI "Custom Stimulus" is disabled:

    if (pot.use_stimstrength_pot) {                                                             // If GUI "Stimulus Strength" is disabled:                             
      stim.strPot_raw = ADC1.read(stim.pin_strPot);                                               // Read strength knob raw ADC (0..4095)
      stim.strPot = (int)stim.strPot_filt.update((uint16_t)stim.strPot_raw);                      // Filtered (median + IIR + deadband)
      stim.strPot_f = stim.strPot_filt.filt_f;                                                    // Keep float accumulator (debug / legacy)
      stim.strPot_centered = stim.strPot - pot.half_range;                                        // Center the potentiometer around 0
      
      if (stim.strPot_centered >= pot.offset) {                                                   // If the Stimulus Strength is above offset:
        stim.strPot_adj  = stim.strPot_centered - pot.offset;                                       // Remove the positive dead-zone
        stim.str_digital = (int16_t)lroundf(stim.strPot_adj * stim.str_digitalMap);                 // Maps this value from -100 to 100 that will correspond to the digital (LED output) stimulus strength %
        stim.str_analog  = (int16_t)lroundf(stim.strPot_adj * stim.str_analogMap);                  // Maps this value from 0 to 100 that will correspond to the analog (Input Current) stimulus strength %
      } else if (stim.strPot_centered <= -pot.offset) {                                           // If the Stimulus Strength is below offset:
        stim.strPot_adj  = stim.strPot_centered + pot.offset;                                       // Remove the negative dead-zone
        stim.str_digital = (int16_t)lroundf(stim.strPot_adj * stim.str_digitalMap);                 // Maps this value from -100 to 100 that will correspond to the digital (LED output) stimulus strength %
        stim.str_analog  = (int16_t)lroundf(stim.strPot_adj * stim.str_analogMap);                  // Maps this value from 0 to 100 that will correspond to the analog (Input Current) stimulus strength %
      } else {                                                                                    // If the Stimulus Strength is within offset range:
        stim.strPot_adj  = 0;                                                                       // Zero adjusted value in the dead-zone
        stim.str_digital = 0;                                                                       // Set the stimulus digital output to 0
        stim.str_analog  = 0;                                                                       // Set the stimulus analog output to 0
      }
    }

    stim.value_analog = (int)lroundf((float)abs(stim.str_analog) * stim.current_scaling);       // The stimulus analog output absolute value is proportional to the potentiometer reading and scaled to parameters

    if (stim.str_digital >= 0){                                                                 // If the Stimulus Strength value is positive:
      stim.value_digital = (int)lroundf((float)stim.str_digital * stim.light_scaling);            // The stimulus digital output is proportional to the potentiometer reading and scaled from parameters
    } else {                                                                                    // Otherwise
      stim.value_digital = 0;                                                                     // Set the stimulus digital output to 0
    }

    if (pot.use_stimfrequency_pot) {                                                          // If GUI "Stimulus Frequency" is disabled:
      stim.freqPot_raw = ADC1.read(stim.pin_freqPot);                                           // Read frequency knob raw ADC (0..4095)
      stim.freqPot = (int)stim.freqPot_filt.update((uint16_t)stim.freqPot_raw);                 // Filtered (median + IIR + deadband)
      stim.freqPot_f = stim.freqPot_filt.filt_f;                                                          // Convert filtered float to an integer ADC count (0..4095)
      stim.freqPot_centered = stim.freqPot - pot.half_range;                                    // Center the potentiometer around 0

      stim.denom = float(pot.half_range - pot.offset);                                        // Usable half-span outside dead-zone
      stim.freq_map_full = 100.0f / ((stim.denom > 1.0f) ? stim.denom : 1.0f);                // Prevent divide-by-zero if offset is mis-set

      if (stim.freqPot_centered >= pot.offset) {                                              // If the Stimulus Frequency is above offset:
        stim.freqPot_adj = stim.freqPot_centered - pot.offset;                                  // Remove the positive dead-zone
        stim.freq = (int16_t)lroundf(-stim.freqPot_adj * stim.freq_map_full);                   // Maps this value from 100 to -100
      } else if (stim.freqPot_centered <= -pot.offset) {                                      // If the Stimulus Frequency is below offset:
        stim.freqPot_adj = stim.freqPot_centered + pot.offset;                                  // Remove the negative dead-zone
        stim.freq = (int16_t)lroundf(-stim.freqPot_adj * stim.freq_map_full);                   // Maps this value from 100 to -100
      } else {                                                                                // If the Stimulus Frequency is within offset range:
        stim.freqPot_adj = 0;                                                                   // Zero adjusted value in the dead-zone
        stim.freq = 0;                                                                          // Zero frequency modifier in the dead-zone
      }
    }

    if (stim.steps < 2) {                                                                     // Prevent a zero/one-step period which would break steps/2 logic
      stim.steps = 2;                                                                           // Minimum viable period
    }

    if (stim.counter < stim.steps/2){                                                         // If the number of void loops has not reached half the stimulus duty cycle:
      stim.pwm = constrain(stim.value_digital, 0, spike.ledc_Max);                              // Sets the stimulus digital output value for the stimulating LED
      stim.dac = stim.value_analog;                                                             // Sets the stimulus analog output value for the Stimulus current output
      stim.state = stim.str_analog;                                                             // Register stimulus ON state
    } else {                                                                                  // If number of void loops has exceeded half the stimulus duty cycle period:
      stim.pwm = 0;                                                                             // Sets the stimulus digital output to 0
      stim.dac = 0;                                                                             // Sets the stimulus analog output to 0                                                                               
      stim.state = 0;                                                                           // Register stimulus OFF state
    }

    stim.dacVal = (uint8_t)constrain(stim.dac, 0, dac_max);                                   // Safety clamp to prevent out-of-range DAC writes
    ledcWrite(stim.pin_stim_light, stim.pwm);                                                 // PWM is already 0 or amplitude depending on phase
    dacWrite(stim.pin_stim_current, stim.dacVal);                                             // Write the phase-correct DAC value

    stim.counter ++;                                                                          // Increment the Stimulus counter by 1
    
    if (stim.trigger_enable){                                                                 // If the Trigger flag is true:
      stim.trigger = 1;                                                                         // Set Trigger to 1
      stim.trigger_enable = false;                                                              // Disable the Trigger Flag
    } else {                                                                                  // If the Trigger flag is false:
      stim.trigger = 0;                                                                         // Set Trigger to 0 
    }

    if (stim.counter >= stim.steps){                                                          // If Stimulus counter has reached the stimulus duty cycle period:
      stim.counter = 0;                                                                         // Reset the void loop counter
      stim.trigger_enable = true;                                                               // Enable the Trigger flag
      stim.steps_f = stim.dutyCycle + ((stim.freq * stim.dutyCycle) * 0.01f) + stim.dutyCycle_Min; // Define the stimulus duty cycle period proportional to the stimulus frequency potentiometer value
      stim.steps = (int)lroundf(stim.steps_f);                                                  // Set stimulus steps value
      if (stim.steps < 2) stim.steps = 2;                                                       // Enforce minimum again after recompute
    }
  }
  
  else {                                                                                    // If GUI "Custom Stimulus"is enabled:
    stim.trigger = 0;                                                                         // Force Trigger to 0
    if (stim.serialTrigger_enable){                                                           // If Serial-Trigger flag is enabled:
      stim.trigger = 1;                                                                         // Set Trigger to 1
      stim.serialTrigger_enable = false;                                                        // Disable Serial-Trigger flag
    }

    stim.cmd_in = stim.value_custom;                                                          // Snapshot current host command (signed)

    if (abs(stim.cmd_in - stim.cmd_hold) > stim.cmd_deadband) {                               // Ignore small +/- chatter around the previous command
      stim.cmd_hold = stim.cmd_in;                                                              // Update the held command
    }
  
    stim.cmd_f += stim.cmd_alpha * (float(stim.cmd_hold) - stim.cmd_f);                       // First-order IIR toward cmd_hold, IIR smoothing: low-pass the held command to remove fast steps/jitter
    stim.cmd = (int)lroundf(stim.cmd_f);                                                      // Convert filtered float command back to integer. Final filtered custom command (signed)
    stim.cmd_abs = (stim.cmd >= 0) ? stim.cmd : -stim.cmd;                                    // Apply the same dead-zone concept for custom values near zero
    stim.custom_active = (stim.cmd_abs >= stim.str_analog_min);                               // Reuse the existing analog-min threshold as dead-zone

    stim.value_digital = (stim.custom_active && (stim.cmd > 0))                               // LED output: only positive command drives LED (negative => LED off)
                      ? (int)lroundf((float)stim.cmd * stim.light_scaling)                    // Scale signed command to PWM counts
                      : 0;

    stim.value_analog = stim.custom_active                                                    // --- Analog output: magnitude drives DAC amplitude, sign is handled elsewhere (polarity logic)
                      ? (int)lroundf((float)stim.cmd_abs * stim.current_scaling)              // Scale magnitude to DAC counts
                      : 0;

    // Keep telemetry coherent (optional but recommended)
    stim.pwm = constrain(stim.value_digital, 0, spike.ledc_Max);                               // Store the PWM value actually being written
    stim.dac = constrain(stim.value_analog, 0, dac_max);                                       // Store the DAC magnitude actually being written

    stim.dacVal = (uint8_t)stim.dac;                                                          // DAC value in 8-bit format
    ledcWrite(stim.pin_stim_light, stim.pwm);                                                  // Clamp to PWM max and write
    dacWrite(stim.pin_stim_current, stim.dacVal);                                              // Write the DAC value

    stim.state = stim.custom_active ? (float)stim.cmd : 0.0f;                                  // Telemetry/state: record the signed command when active, otherwise 0
  }
}




inline void update_StimulusCurrentIn() {

  patch.input_value_raw = ADC2.read(patch.pin);                                               // Raw ADC counts: 0..4095 (12-bit)
  patch.input_value_f += patch.alpha_in*(float(patch.input_value_raw) - patch.input_value_f); // First-order low-pass filter on the raw ADC reading
  patch.input_value     = (uint16_t)lroundf(patch.input_value_f);                             // Convert filtered float to an integer ADC count

  if (stim.dacVal == 0) {                                                                     // Determine whether the stimulus output is effectively active 
    patch.current_in_zero = 0.99f * patch.current_in_zero + 0.01f * patch.input_value;        // First-order low-pass: slow baseline tracking to follow drift, not stimulus
  }

  patch.pot_centered = float(patch.input_value) - patch.current_in_zero;                      // Center the ADC reading around baseline

  if (patch.pot_centered >= pot.offset) {                                                     // If centered input is above +offset:
    patch.pot_adj = patch.pot_centered - pot.offset;                                            // Remove the positive dead-zone
  } else if (patch.pot_centered <= -pot.offset) {                                             // If centered input is below -offset:
    patch.pot_adj = patch.pot_centered + pot.offset;                                            // Remove the negative dead-zone
  } else {                                                                                    // If centered input is within offset range:
    patch.pot_adj = 0.0f;                                                                       // Force to zero inside the dead-zone
  }

  if (stim.custom_disable) {                                                                  // If GUI "Custom Stimulus"is disabled:
    if (stim.str_analog > stim.str_analog_min) {                                                // If Strength pot above +threshold -> positive polarity
      stim.sign = +1.0f;                                                                          // Set sign to positive
    } else if (stim.str_analog < -stim.str_analog_min) {                                        // If Strength pot below -threshold -> negative polarity
      stim.sign = -1.0f;                                                                          // Set sign to negative
    } else {                                                                                    // If Strength pot near 0 (inside dead-zone)
      stim.sign = 0.0f;                                                                           // No polarity -> treat as zero stimulus
    }
  } else {                                                                                    // If GUI "Custom Stimulus"is enabled:
    if (stim.value_custom > 0) {                                                                // If Custom value positive
      stim.sign = +1.0f;                                                                          // Positive polarity
    } else if (stim.value_custom < 0) {                                                         // If Custom value negative
      stim.sign = -1.0f;                                                                          // Negative polarity
    } else {                                                                                    // If Custom value exactly zero
      stim.sign = 0.0f;                                                                           // No stimulus (also avoids analog misread/jitter)
    }
  }

  // ----- Voltage clamp interpretation -----
  if (clampMode == ClampMode::VoltageClamp) {                                                 // If we are in Voltage Clamp mode
    if (stim.dacVal == 0 || stim.sign == 0.0f) {                                                // If DAC activity is OFF or sign is 0
      patch.v_step = 0.0f;                                                                        // Force step to zero 
      patch.v_cmd  = constrain(patch.v_hold, neuron.Vm_min, neuron.Vm_peak);                      // Force command to hold
      patch.current_input = 0.0f;                                                                 // In V-clamp mode, do NOT also inject current via IC.current (keeps I–V clean)
      stim.state = (int)lroundf(patch.v_cmd);                                                     // Report command voltage
      return;                                                                                     // Done for VoltageClamp mode
    }

    patch.magnitude = (fabsf(patch.pot_adj) / (float(bits12) * 0.5f)) * patch.v_step_max;       // Map magnitude of centered ADC (counts) to a voltage step (mV) 
    patch.magnitude = constrain(patch.magnitude, 0.0f, patch.v_step_max);                       // Normalised magnitude in [0..1] -> scale to [0..v_step_max]
    patch.v_step    = stim.sign * patch.magnitude;                                              // Apply sign from the existing polarity logic
    patch.v_cmd     = constrain(patch.v_hold + patch.v_step, neuron.Vm_min, neuron.Vm_peak);    // Total command voltage = hold + step
    patch.current_input = 0.0f;                                                                 // In V-clamp mode, do NOT also inject current via IC.current (keeps I–V clean)

    stim.state = (int)lroundf(patch.v_cmd);                                                     // Report command voltage
    return;                                                                                     // Done for VoltageClamp mode
  }

  if (stim.dacVal == 0 || stim.sign == 0.0f) {                                                // If no stimulus is effectively active (OFF phase or dead-zone)...
    patch.current_input = 0.0f;                                                                 // ...force injected current to 0 (prevents analog misreading)
  } else {                                                                                    // Otherwise polarity is defined...
    patch.current_input = stim.sign * (patch.pot_adj * patch.input_scaling);                    // Scale ADC to current and apply sign (+ or -)
  }
}



inline void update_VoltageClampPI() {                                                           

  if (clampMode != ClampMode::VoltageClamp) {                                                 // If we are NOT in voltage clamp mode...
    patch.I_clamp = 0.0f;                                                                       // Force PI output to 0 (not used in current clamp mode).
    patch.e_int   = 0.0f;                                                                       // Reset the integrator so it does not accumulate while inactive.
    return;                                                                                     // Exit early; nothing else to do.
  }

/*                     ---- Error computation: command minus measured ----                     */
  pi.e = patch.v_cmd - neuron.v;                                                                // If e > 0, Vm is below command -> controller should inject depolarizing current 

/*                       ---- Proportional term (a.u.): p = Kp * e ----                        */
  pi.p = patch.Kp * pi.e;                                                                       // Proportional output current: reacts immediately to the present error. Kp in [uA/mV] so P is [uA]

/*            --- Integral term (a.u.) computed from CURRENT integrator state ----             */ 
  pi.i_hold = patch.Ki * patch.e_int;                                                           // Integral output current computed from the proposed integrator state. e_int in [mV*ms], Ki in [uA/(mV*ms)] so I is [uA]

/*                ---- Unsaturated PI output (a.u.) using held integrator ----                 */
  pi.out_unsat_hold = pi.p + pi.i_hold;                                                         // PI output current before applying compliance (saturation). [uA]

/*                   ---- Apply compliance limits (actuator saturation) ----                   */
  pi.out_sat = constrain(pi.out_unsat_hold, patch.I_min, patch.I_max);

/*                                 ---- Anti-windup logic ----                                 */
  pi.saturated_high = (pi.out_unsat_hold > patch.I_max);
  pi.saturated_low  = (pi.out_unsat_hold < patch.I_min);

/*                           ---- Commit the integrator update ----                            */
  pi.allow_integrate =  (!pi.saturated_high && !pi.saturated_low) ||
                        (pi.saturated_high && (pi.e < 0.0f)) ||
                        (pi.saturated_low  && (pi.e > 0.0f));
  if (pi.allow_integrate) {
      patch.e_int += pi.e * neuron.dt_ms;                                                       // Candidate integrator update (mV * model-ms)
  }
  
/*                ---- Final output computed from COMMITTED integrator state ----               */
  pi.i_final = patch.Ki * patch.e_int;
  pi.out_unsat = pi.p + pi.i_final;
  pi.out_sat = constrain (pi.out_unsat, patch.I_min, patch.I_max);
  patch.I_clamp = pi.out_sat;
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                       Spike and Axon output                                           */

inline void update_Spike() {
  if (clampMode == ClampMode::VoltageClamp) {                                                   // If we are in Voltage Clamp mode. 
    neuron.v_out = neuron.v;                                                                      // Export the model voltage directly as the output voltage. In voltage clamp we do not generate spike events; we simply report the clamped Vm.
    digitalWrite(axon.pin_digital, LOW);                                                          // Force the axon digital output LOW so no TTL “spike” pulses are emitted. Force the axon digital output LOW so no TTL “spike” pulses are emitted interpreting clamp plateaus/steps as spikes.
    digitalWrite(pins.gpio.spike, LOW);                                                           // Force the spike-indicator GPIO LOW (typically drives a LED / buzzer logic). Avoid “false spike” signals during voltage clamp.

    if (spike.LED_enable) {                                                                             // If GUI LED bool is enabled
      spike.led_Vm_pwmf = (neuron.v_out - neuron.Vm_min) * spike.led_Vm;                            // Convert Vm (in model units, typically mV) into a PWM command
      spike.led_Vm_pwm = int(constrain(spike.led_Vm_pwmf, 0.0f, float(bits10)));                    // Constrain the computed duty cycle to the valid PWM range and quantize to integer counts
      setLedc(pins.gpio.led_r, spike.led_Vm_pwm, spike.led_r_last);                                 // Apply PWM to the Red LED, encodes Vm
      setLedc(pins.gpio.led_g, 0, spike.led_g_last);                                                // Set Green LED off
      setLedc(pins.gpio.led_b, 0, spike.led_b_last);                                                // Set Blue LED off
    }
  }
  else{                                                                                         // If we are in Voltage Clamp mode. 
    if ( neuron.v>= neuron.Vm_spike ) {                                                           // Whenever neuron is considered to be spiking 
      neuron.v_out = neuron.Vm_peak;                                                                // Forces the displayed Vm value to Vm_peak
      digitalWrite(axon.pin_digital, HIGH);                                                         // Sends digital output through the Axon digital pin
      
      if (spike.LED_enable) {                                                                           // If GUI LED bool is enabled
        setLedc(pins.gpio.led_r, spike.ledc_Max, spike.led_r_last);                                 // set red LED to HIGH
        setLedc(pins.gpio.led_g, spike.ledc_Max, spike.led_g_last);                                 // set green LED to HIGH
        setLedc(pins.gpio.led_b, spike.ledc_Max, spike.led_b_last);                                 // set blue LED to HIGH
      }
      if (spike.Buzzer_enable) {                                                                        // If GUI buzzer bool is enabled
        digitalWrite(pins.gpio.spike, HIGH);                                                        // Activate buzzer
      }
    }
    else {                                                                                        // Whenever neuron is not spiking
      neuron.v_out = neuron.v;                                                                      // The displayed Vm value corresponds to Spikeling Vm
      digitalWrite(axon.pin_digital, LOW);                                                          // Keep the digital output in a LOW state 
      digitalWrite(pins.gpio.spike, LOW);                                                           // Keep the buzzer silent
                                                                                        
      if (spike.LED_enable) {                                                                       // If GUI LED bool is enabled
        spike.led_Vm_pwmf = (neuron.v_out - neuron.Vm_min) * spike.led_Vm;                            // Convert Vm (in model units, typically mV) into a PWM command
        spike.led_Vm_pwm = int(constrain(spike.led_Vm_pwmf, 0.0f, float(bits10)));                    // Constrain the computed duty cycle to the valid PWM range and quantize to integer counts
        setLedc(pins.gpio.led_r, spike.led_Vm_pwm, spike.led_r_last);                                 // Apply PWM to the Red LED, encodes Vm
        setLedc(pins.gpio.led_g, 0, spike.led_g_last);                                                // Set Green LED off
        setLedc(pins.gpio.led_b, 0, spike.led_b_last);                                                // Set Blue LED off
      }                                                   
    } 
  }
  axon.norm = (neuron.v_out - neuron.Vm_min) * axon.Vm_range;                                   // Normalize v_out into a 0..1 range relative to the model's allowed Vm bounds
  axon.norm = constrain(axon.norm, 0.0f, 1.0f);                                                 // Safety clamp to ensure numerical stability and prevent out-of-range DAC writes
  axon.dacVal = axon.norm * dac_max + 0.5f;                                                     // Convert normalized value to an 8-bit DAC code in [0..dac_max]
  dacWrite(axon.pin_analog,axon.dacVal);                                                        // Output the DAC code to the analog pin                                          
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                              Serial                                                   */

/*             ---- Quantize a scaled float to int16 with symmetric rounding ----              */
inline int16_t q_round(float x) { 
  if (x != x) return 0;                                                                         // Handle NaN (NaN comparisons are false, so clamp would be skipped)                                                
/*                 ---- Saturate to int16 range *before* rounding/casting ----                 */
  if (x >  32767.0f) return  32767;
  if (x < -32768.0f) return -32768;   
/*                       ---- Symmetric rounding to nearest integer ----                       */       
  if (x >= 0.0f)
    return (int16_t)(x + 0.5f);
  else
    return (int16_t)(x - 0.5f);
}



inline void send_SamplePacket() {
  pkt.v_q         = q_round(neuron.v_out * V_SCALE);                                            // Membrane Potential
  pkt.stim_state  = (int16_t)stim.state;                                                        // Stimulus State  
  patch.I_for_gui = (clampMode == ClampMode::VoltageClamp)                                      // Depending on the Patch Clamp mode:
                  ? patch.I_clamp                                                                 // In VC: report the clamp amplifier output current (PI output).
                  : neuron.total_current;                                                         // In CC: keep reporting the full injected current (command + syn + PD + noise).
  pkt.Itot_q      = q_round(patch.I_for_gui * I_SCALE);                                         // Current In
  pkt.syn1_vm_q   = q_round(syn1.Vm * SYN_V_SCALE);                                             // Synapse 1 Membrane Potential
  pkt.Isyn1_q     = q_round(syn1.current * I_SCALE);                                            // Synapse 1 Current
  pkt.syn2_vm_q   = q_round(syn2.Vm * SYN_V_SCALE);                                             // Synapse 2 Membrane Potential
  pkt.Isyn2_q     = q_round(syn2.current * I_SCALE);                                            // Synapse 2 Current
  pkt.trigger_q   = (int16_t)stim.trigger;                                                      // Trigger

  const uint8_t header[2] = { 0xAA, 0x55 };
  Serial.write(header, 2);
  Serial.write(reinterpret_cast<uint8_t*>(&pkt), sizeof(pkt));
  wifiSendSamplePacket(pkt);
}




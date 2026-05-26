#pragma once  
   
#include "Serial_functions.h"



// // // // // // // // // // // // // // // // // // // // // // // //
/*                        User buttons: Buzzer + LED toggles          */

inline void poll_ToggleButtons() {
  const uint32_t now = millis();                         // Sample time once (shared by both buttons)
  buzzerButton.raw = digitalRead(pins.gpio.buzzer_button); // Raw level for buzzer button (LOW released, HIGH pressed)
  ledButton.raw = digitalRead(pins.gpio.led_button);     // Raw level for LED button (LOW released, HIGH pressed)
  buzzerButton.now_ms = now;                             // Store timestamp for buzzer debounce logic
  ledButton.now_ms = now;                                // Store timestamp for LED debounce logic
}

inline bool debouncedRisingEdge(ButtonDebounce &btn) {

  if (btn.raw != btn.lastRaw) {                          // If raw input changed since last poll:
    btn.lastRaw = btn.raw;                               // Save the new raw level
    btn.lastChange_ms = btn.now_ms;                      // Restart debounce timer
  }

  if ((btn.now_ms - btn.lastChange_ms) < btn.debounce_ms) { // If not stable long enough:
    return false;                                        // Ignore until stable
  }

  if (btn.raw != btn.lastStable) {                       // If stable state differs from debounced state:
    btn.lastStable = btn.raw;                            // Commit the new stable state

    if (btn.lastStable == HIGH) {                        // INPUT_PULLDOWN: press is rising edge (LOW -> HIGH)
      return true;                                       // Emit a single press event
    }
  }

  return false;                                          // No press event
}

inline void update_ToggleButtons() {
  if (debouncedRisingEdge(buzzerButton)) {               // If buzzer button press detected:
    toggleBuzzerEnabled();                                 // Toggle buzzer enable + enforce hardware state
  }

  if (debouncedRisingEdge(ledButton)) {                  // If LED button press detected:
    toggleLedEnabled();                                    // Toggle LED enable + enforce hardware state
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
      patch.current_clamp = (patch.pot_value - pot.offset) * patch.pot_scaling;                     // Subtract the dead-zone edge and scale to engineering units.
    } else if (patch.pot_value <= -pot.offset) {                                                  // If centered is negative beyond the deadzone, 
      patch.current_clamp = (patch.pot_value + pot.offset) * patch.pot_scaling;                     // Add the dead-zone edge and scale to engineering units.
    } else {                                                                                      // Otherwise it’s inside the deadzone,
      patch.current_clamp = 0.0f;                                                                   // treat as exactly zero.
    } 
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                          Noise Generator                                              */

inline void update_Noise() {  
  
  if (!pot.use_noise_pot) return;                                                             // If GUI/serial override is active (noise.enable == false), don't use the pot
  
  const uint16_t noise_raw = ADC2.read(noise.pot_pin);                                          // Read Noise knob raw ADC (0..4095)
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

inline void calibrate_PhotodiodeDark(uint16_t nSamples = 200, uint16_t sampleDelay_ms = 2) {// Calibrate the photodiode "dark" baseline at boot.

  // Force stimulus outputs OFF during calibration
  ledcWrite(pins.gpio.stim_d, 0);                 // stim PWM off (stim LED / stim gate)
  DAC.write(stim_dac_zero, stim.pin_stim_current);// stim DAC off (no injected current output)

  delay(50);                                      // settle time for analog front-end

  uint32_t acc = 0;
  for (uint16_t i = 0; i < nSamples; i++) {
    acc += (uint16_t)ADC1.read(PD.pin);
    delay(sampleDelay_ms);
  }

  PD.dark_counts = (float)acc / (float)nSamples;

  // Prime the moving-average ring buffer so the first seconds after boot are stable.
  const int v = (int)lroundf(PD.dark_counts);
  PD.sum = 0;
  for (uint8_t k = 0; k < PD.windowN; k++) {
    PD.values[k] = v;
    PD.sum += v;
  }
  PD.counter = 0;
  PD.value   = (uint16_t)v;
  PD.average = PD.dark_counts;

  // Start from a neutral PD state
  PD.gain    = 0.0f;
  PD.amp     = 1.0f;
  PD.current = 0.0f;
}



inline void update_Photodiode() {
  
  PD.value = ADC1.read(PD.pin);                                                               // Reads Photodiode value from 0 to ~400

  PD.sum -= PD.values[PD.counter];                                                            // Remove old sample
  PD.values[PD.counter] = PD.value;                                                           // Store new sample
  PD.sum += PD.value;                                                                         // Add new sample
  PD.counter++;                                                                               // Next ring-buffer slot
  if (PD.counter >= PD.windowN) {                                                             // Wrap at window length
    PD.counter = 0;
  }
  PD.average = (float)PD.sum * PD.invWindowN;                                                 // True mean of last windowN samples

  if (pot.use_photodiode_pot){                                                                // If the board Photodiode Gain is enabled:
    PD.raw = ADC1.read(PD.pot_pin);                                                             // Read PD gain knob raw ADC (0..4095)
    PD.adc = PD.pot_filt.update(PD.raw);                                                        // Filtered ADC (median + IIR + deadband)
    PD.pot_value = (int16_t)((int32_t)PD.adc - (int32_t)pot.half_range);                        // Center to -2048..+2047
    
    if (PD.pot_value >= pot.offset){                                                            // If PD potentiometer value is above the offset:
        PD.gain = (PD.pot_value - pot.offset) * PD.pot_scaling;                                   // Generates gain value from the reading, subtracts the offset and scales it from parameters
    }else if (PD.pot_value <= -pot.offset){                                                     // If PD potentiometer value is below the offset:
      PD.gain = (PD.pot_value + pot.offset) * PD.pot_scaling;                                     // Generates gain value from the reading, add the offset and scales it from parameters
    }else{                                                                                      // If PD potentiometer value is within offset range:
      PD.gain = 0.0f;                                                                             // Set PD Gain to 0
    }
  } 
  PD.polarity = (PD.gain >= 0.0f) ? 1 : -1;                                                   // Set Photodiode polarity (positive if gain above 0, negative if gain stricly below 0)

  // Map photodiode reading (counts) -> normalized light (0..1) -> injected current
  PD.eff = PD.average - PD.dark_counts;                                                       // subtract dark baseline (counts)
  if (PD.eff < 0.0f) PD.eff = 0.0f;

  PD.denom = (PD.full_counts > 1e-6f) ? PD.full_counts : 1.0f;                                // avoid divide-by-zero
  PD.norm = PD.eff / PD.denom;                                                                // 0..~1
  if (PD.norm > 1.0f) PD.norm = 1.0f;

  PD.current = (PD.norm * PD.I_full) * PD.gain * PD.amp;                                      //// Generates Photodiode current, amplified by the PD_Gain readings

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
    syn.pot_raw = ADC1.read(syn.pot_pin);                                                       // Read Syn gain knob raw ADC (0..4095)
    syn.pot_raw_filter = syn.pot_filt.update(syn.pot_raw);                                      // Filtered ADC (median + IIR + deadband)
    syn.pot_value = (int16_t)((int32_t)syn.pot_raw_filter - (int32_t)pot.half_range);           // Center to -2048..+2047
    
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

  syn.Vm_input = ADC1.read(syn.pin_analog);                                                   // Reads Synapse Vm input
  syn.Vm = mapfloat(syn.Vm_input,
                    syn.analogOffsetLow, bits12 - syn.analogOffsetHigh, 
                    neuron.Vm_min,  neuron.Vm_max);                                           // Maps Synapse Vm to Spikeling Neuron range
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
      stim.strPot_raw = ADC2.read(stim.pin_strPot);                                               // Read strength knob raw ADC (0..4095)
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

    stim.amp = constrain(abs(stim.str_analog), 0, 100);                         
    stim.value_analog = (int)lroundf((float)stim.amp * stim.current_scaling);                 // The stimulus analog output absolute value is proportional to the potentiometer reading and scaled to parameters
       
    if (stim.str_digital > 0) {                                                               // If the Stimulus Strength value is positive:
      stim.value_digital = (int)(((int32_t)stim.str_digital*(int32_t)spike.ledc_Max+50)/100);   // Map 1..100 (%) -> 0..ledc_Max
    } else {                                                                                  // Otherwise
      stim.value_digital = 0;                                                                   // Set the stimulus digital output to 0
    }

    if (pot.use_stimfrequency_pot) {                                                          // If GUI "Stimulus Frequency" is disabled:
      stim.freqPot_raw = ADC2.read(stim.pin_freqPot);                                           // Read frequency knob raw ADC (0..4095)
      stim.freqPot = (int)stim.freqPot_filt.update((uint16_t)stim.freqPot_raw);                 // Filtered (median + IIR + deadband)
      stim.freqPot_f = stim.freqPot_filt.filt_f;                                                // Convert filtered float to an integer ADC count (0..4095)
      stim.freqPot_centered = stim.freqPot - pot.half_range;                                    // Center the potentiometer around 0

      stim.denom = float(pot.half_range - pot.offset);                                          // Usable half-span outside dead-zone
      stim.freq_map_full = 100.0f / ((stim.denom > 1.0f) ? stim.denom : 1.0f);                  // Prevent divide-by-zero if offset is mis-set

      if (stim.freqPot_centered >= pot.offset) {                                                // If the Stimulus Frequency is above offset:
        stim.freqPot_adj = stim.freqPot_centered - pot.offset;                                    // Remove the positive dead-zone
        stim.freq = (int16_t)lroundf(-stim.freqPot_adj * stim.freq_map_full);                     // Maps this value from 100 to -100
      } else if (stim.freqPot_centered <= -pot.offset) {                                        // If the Stimulus Frequency is below offset:
        stim.freqPot_adj = stim.freqPot_centered + pot.offset;                                    // Remove the negative dead-zone
        stim.freq = (int16_t)lroundf(-stim.freqPot_adj * stim.freq_map_full);                     // Maps this value from 100 to -100
      } else {                                                                                  // If the Stimulus Frequency is within offset range:
        stim.freqPot_adj = 0;                                                                     // Zero adjusted value in the dead-zone
        stim.freq = 0;                                                                            // Zero frequency modifier in the dead-zone
      }
    }

    if (stim.steps < 2) {                                                                     // Prevent a zero/one-step period which would break steps/2 logic
      stim.steps = 2;                                                                           // Minimum viable period
    }

    const bool analogActive = (abs(stim.str_analog) >= stim.str_analog_min);
    const int signedDacStep = analogActive
                            ? ((stim.str_analog > 0) ? stim.value_analog : -stim.value_analog)
                            : 0;

    if (stim.counter < stim.steps/2) {
      stim.pwm = constrain(stim.value_digital, 0, spike.ledc_Max);
      stim.dac = (int)stim_dac_zero + signedDacStep;
      stim.state = analogActive ? stim.str_analog : 0;
    } else {
      stim.pwm = 0;
      stim.dac = stim_dac_zero;
      stim.state = 0;
    }

    stim.dacVal = (uint16_t)constrain(stim.dac, 0, dac_max);
    ledcWrite(stim.pin_stim_light, stim.pwm);
    DAC.write(stim.dacVal, stim.pin_stim_current);

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
      stim.steps_f = stim.dutyCycle + ((stim.freq*stim.dutyCycle)*0.01f) + stim.dutyCycle_Min;  // Define the stimulus duty cycle period proportional to the stimulus frequency potentiometer value
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

    
    if (stim.custom_active && (stim.cmd > 0)) {                                               // LED output (stim LED): only positive command produces light, mapped to full PWM range
      int32_t cmd_pos = stim.cmd;                                                               // expected in 0..100
      if (cmd_pos > 100) cmd_pos = 100;                                                         // safety clamp

      // Map 0..100 (%) -> 0..ledc_Max (with rounding)
      stim.value_digital = (int)((cmd_pos * (int32_t)spike.ledc_Max + 50) / 100);
    } else {
      stim.value_digital = 0;                                                                   // negative or inactive => LED off
    }


    stim.value_analog = stim.custom_active
                      ? (int)lroundf((float)constrain(stim.cmd_abs, 0, 100) * stim.current_scaling)
                      : 0;

    const int signedDacStep = stim.custom_active
                            ? ((stim.cmd > 0) ? stim.value_analog : -stim.value_analog)
                            : 0;

    stim.pwm = constrain(stim.value_digital, 0, spike.ledc_Max);

    stim.dac = (int)stim_dac_zero + signedDacStep;

    stim.dacVal = (uint16_t)constrain(stim.dac, 0, dac_max);
    ledcWrite(stim.pin_stim_light, stim.pwm);
    DAC.write(stim.dacVal, stim.pin_stim_current);

    stim.state = stim.custom_active ? (float)stim.cmd : 0.0f;
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                  Stimulus RGB LED: intensity + polarity                               */

inline uint32_t ledcMaxDuty() {                                                             // Helper: compute max LEDC duty from resolution
  return (spike.ledc_Resolution >= 1 && spike.ledc_Resolution <= 16)                          // Guard against invalid resolution values
         ? ((1UL << spike.ledc_Resolution) - 1UL)                                             // Max duty = 2^res - 1
         : 255UL;                                                                             // Fallback (8-bit style) if resolution is unexpected
}

inline void update_StimulusStatusLED() {

  const uint32_t maxDuty = ledcMaxDuty();

  if (!spike.LED_enable) {
    ledcWrite(pins.gpio.led_stim_r, 0);
    ledcWrite(pins.gpio.led_stim_g, 0);
    ledcWrite(pins.gpio.led_stim_b, 0);
    return;
  }

  // Use the outgoing stimulus state, not stim.sign.
  // stim.state should be:
  //   > 0 during positive stimulus
  //   < 0 during negative stimulus
  //   = 0 when stimulus is inactive / between pulses
  const float signedStim = stim.state;

  if (fabsf(signedStim) < 0.5f) {
    ledcWrite(pins.gpio.led_stim_r, 0);
    ledcWrite(pins.gpio.led_stim_g, 0);
    ledcWrite(pins.gpio.led_stim_b, 0);
    return;
  }

  float mag = fabsf(signedStim);
  if (mag > 100.0f) mag = 100.0f;

  const uint32_t duty = (uint32_t)lroundf((mag / 100.0f) * (float)maxDuty);

  if (signedStim > 0.0f) {
    // Positive stimulus: red
    ledcWrite(pins.gpio.led_stim_r, duty / 10);
    ledcWrite(pins.gpio.led_stim_g, 0);
    ledcWrite(pins.gpio.led_stim_b, 0);
  } else {
    // Negative stimulus: blue
    ledcWrite(pins.gpio.led_stim_r, 0);
    ledcWrite(pins.gpio.led_stim_g, 0);
    ledcWrite(pins.gpio.led_stim_b, duty);
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                    Stimulus - Applying Analog Values                                  */
 

inline void calibrate_StimulusCurrentInZero() {

  const int n = 256;
  uint32_t acc = 0;

  for (int i = 0; i < n; i++) {
    acc += ADC1.read(patch.pin);
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

inline void update_StimulusCurrentIn() {

  patch.input_value_raw = ADC1.read(patch.pin);

  patch.input_value_f += patch.alpha_in * (float(patch.input_value_raw) - patch.input_value_f);
  patch.input_value = (uint16_t)lroundf(patch.input_value_f);

  const int32_t input_delta =
    (int32_t)patch.input_value - (int32_t)patch.current_in_prev_value;

  const bool input_stable =
    (input_delta >= -(int32_t)current_in_stable_delta) &&
    (input_delta <=  (int32_t)current_in_stable_delta);

  const bool input_not_near_rails =
    (patch.input_value > current_in_rail_margin) &&
    (patch.input_value < (dac_max - current_in_rail_margin));

  patch.current_in_prev_value = patch.input_value;

  // ------------------------------------------------------------------
  // Autozero / hot-plug arming phase
  // ------------------------------------------------------------------
  // While Current-In is not ready, do not inject any current.
  // Wait until the input is stable and not rail-like, then learn it as zero.
  if (!patch.current_in_ready) {

    if (input_not_near_rails && input_stable) {

      if (patch.current_in_stable_count == 0) {
        patch.current_in_candidate_zero = (float)patch.input_value;
      } else {
        patch.current_in_candidate_zero =
          0.95f * patch.current_in_candidate_zero +
          0.05f * (float)patch.input_value;
      }

      patch.current_in_stable_count++;

      if (patch.current_in_stable_count >= current_in_arm_samples) {
        patch.current_in_zero = patch.current_in_candidate_zero;
        patch.input_value_f   = patch.current_in_zero;
        patch.input_value     = (uint16_t)lroundf(patch.current_in_zero);

        patch.current_in_ready = true;
      }

    } else {
      patch.current_in_stable_count   = 0;
      patch.current_in_candidate_zero = (float)patch.input_value;
    }

    neutralise_StimulusCurrentIn();
    return;
  }

  // ------------------------------------------------------------------
  // Normal bipolar decoding phase
  // ------------------------------------------------------------------

  patch.pot_centered = float(patch.input_value) - patch.current_in_zero;

  // Only track slow drift when the input is already close to zero.
  // This prevents real stimulus pulses from being absorbed into the baseline.
  if (fabsf(patch.pot_centered) < pot.offset) {
    patch.current_in_zero =
      0.995f * patch.current_in_zero +
      0.005f * float(patch.input_value);

    patch.pot_centered = float(patch.input_value) - patch.current_in_zero;
  }

  if (patch.pot_centered >= pot.offset) {
    patch.pot_adj = patch.pot_centered - pot.offset;
  } else if (patch.pot_centered <= -pot.offset) {
    patch.pot_adj = patch.pot_centered + pot.offset;
  } else {
    patch.pot_adj = 0.0f;
  }

  float currentInSign = 0.0f;

  if (patch.pot_adj > 0.0f) {
    currentInSign = +1.0f;
  } else if (patch.pot_adj < 0.0f) {
    currentInSign = -1.0f;
  }

  // ------------------------------------------------------------------
  // Voltage clamp interpretation
  // ------------------------------------------------------------------
  if (clampMode == ClampMode::VoltageClamp) {

    if (currentInSign == 0.0f) {
      patch.v_step = 0.0f;
      patch.v_cmd  = constrain(patch.v_hold, neuron.Vm_min, neuron.Vm_peak);
      patch.current_input = 0.0f;
      stim.state = (int)lroundf(patch.v_cmd);
      return;
    }

    patch.magnitude =
      (fabsf(patch.pot_adj) / (float)stim_dac_span) * patch.v_step_max;

    patch.magnitude = constrain(patch.magnitude, 0.0f, patch.v_step_max);

    patch.v_step = currentInSign * patch.magnitude;
    patch.v_cmd  = constrain(patch.v_hold + patch.v_step,
                             neuron.Vm_min,
                             neuron.Vm_peak);

    patch.current_input = 0.0f;
    stim.state = (int)lroundf(patch.v_cmd);
    return;
  }

  // ------------------------------------------------------------------
  // Current clamp interpretation
  // ------------------------------------------------------------------
  if (currentInSign == 0.0f) {
    patch.current_input = 0.0f;
  } else {
    patch.current_input = patch.pot_adj * patch.input_scaling;
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
      spike.led_Vm_pwmf = (neuron.v_out - neuron.Vm_min) * spike.led_Vm;                              // Convert Vm into a PWM command
      spike.led_Vm_pwm = int(constrain(spike.led_Vm_pwmf, 0.0f, float(spike.ledc_Max)));              // Constrain to the configured LED PWM maximum

      setVmRgbLed((uint16_t)spike.led_Vm_pwm);                                                        // Display Vm using the selected RGB colour
    }
  }
  else{                                                                                         // If we are in Voltage Clamp mode. 
    if ( neuron.v>= neuron.Vm_spike ) {                                                           // Whenever neuron is considered to be spiking 
      neuron.v_out = neuron.Vm_peak;                                                                // Forces the displayed Vm value to Vm_peak
      digitalWrite(axon.pin_digital, HIGH);                                                         // Sends digital output through the Axon digital pin
      
      if (spike.LED_enable) {                                                                       // If GUI LED bool is enabled
        setSpikeRgbLedWhite();                                                                       // Spike event is always displayed as white
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
        spike.led_Vm_pwmf = (neuron.v_out - neuron.Vm_min) * spike.led_Vm;                            // Convert Vm into a PWM command
        spike.led_Vm_pwm = int(constrain(spike.led_Vm_pwmf, 0.0f, float(spike.ledc_Max)));             // Constrain to the configured LED PWM maximum

        setVmRgbLed((uint16_t)spike.led_Vm_pwm);                                                      // Display Vm using the selected RGB colour
      }                                                  
    } 
  }
  axon.norm = (neuron.v_out - neuron.Vm_min) * axon.Vm_range;                                   // Normalize v_out into a 0..1 range relative to the model's allowed Vm bounds
  axon.norm = constrain(axon.norm, 0.0f, 1.0f);                                                 // Safety clamp to ensure numerical stability and prevent out-of-range DAC writes
  axon.dacVal = axon.norm * dac_max + 0.5f;                                                     // Convert normalized value to an 12-bit DAC code in [0..dac_max]
  DAC.write(axon.dacVal, axon.pin_analog);                                                      // Output the DAC code to the analog pin                                          
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
  // wifiSendSamplePacket(pkt);
}




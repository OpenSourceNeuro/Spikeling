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

  // If the GUI/serial has disabled the physical noise pot, keep the current
  // externally assigned noise value and do not read the knob.
  if (!pot.use_noise_pot) {
    return;
  }

  const uint16_t noise_raw = ADC1.read(noise.pot_pin);                                        // Raw ADC: 0..4095
  noise.pot_value = (int16_t)noise.pot_filt.update(noise_raw);                                // Filtered ADC

  // Noise pot is unipolar: low end = no noise.
  if (noise.pot_value <= pot.offset) {
    noise.amp = 0.0f;
    noise.sigma = 0.0f;
    noise.var = 0.0f;
    noise.newSigma = 0.0f;
    noise.current = 0.0f;

    noise.dist.variance = 0.0f;
    noise.dist.mean = noise.mean;

    return;
  }

  noise.amp = (noise.pot_value - pot.offset) * noise.pot_scaling;

  noise.newSigma = noise.sigma_per_amp * noise.amp;

  if (fabsf(noise.newSigma - noise.sigma) > noise.kSigmaUpdateEps) {
    noise.sigma = noise.newSigma;
    noise.var = noise.sigma * noise.sigma;

    noise.dist.variance = noise.var;
    noise.dist.mean = noise.mean;
  }

  noise.current = noise.dist.random();
}


// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                              PhotoDiode                                               */

inline void update_Photodiode() {

  // ---------------------------------------------------------------------------
  // 1. Read photodiode signal

  PD.value = ADC2.read(PD.pin);                                                               // Read photodiode ADC value


  // ---------------------------------------------------------------------------
  // 2. Moving average over the photodiode signal

  PD.sum -= PD.values[PD.counter];                                                            // Remove old sample
  PD.values[PD.counter] = PD.value;                                                           // Store new sample
  PD.sum += PD.value;                                                                         // Add new sample

  PD.counter++;                                                                               // Move to next ring-buffer slot
  if (PD.counter >= PD.windowN) {                                                             // Wrap at window length
    PD.counter = 0;
  }

  PD.average = (float)PD.sum * PD.invWindowN;                                                 // Mean of last windowN samples


  // ---------------------------------------------------------------------------
  // 3. Read and map the photodiode gain potentiometer

  if (pot.use_photodiode_pot) {                                                               // If local PD gain pot is enabled

    PD.raw = ADC1.read(PD.pot_pin);                                                           // Read PD gain knob raw ADC
    PD.adc = PD.pot_filt.update(PD.raw);                                                      // Filter ADC reading

    PD.pot_value = (int16_t)((int32_t)PD.adc - (int32_t)pot.half_range);                      // Centre around 0

    if (PD.pot_value >= pot.offset) {                                                         // Positive gain region
      PD.gain = (PD.pot_value - pot.offset) * PD.pot_scaling;

    } else if (PD.pot_value <= -pot.offset) {                                                 // Negative gain region
      PD.gain = (PD.pot_value + pot.offset) * PD.pot_scaling;

    } else {                                                                                  // Centre dead zone
      PD.gain = 0.0f;
    }
  }


  // ---------------------------------------------------------------------------
  // 4. Direct absolute-light photodiode current

  PD.polarity = (PD.gain >= 0.0f) ? 1 : -1;                                                    // Store sign for reference/debug

  PD.amp = 1.0f;                                                                              // Force adaptation off in this mode

  PD.current = PD.average * PD.I_per_count * PD.gain;                                          // Direct light-to-current conversion
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

  syn.Vm_input = ADC2.read(syn.pin_analog);                                                   // Reads Synapse Vm input
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

  // ---------------------------------------------------------------------------
  // POTENTIOMETER / LOCAL STIMULUS MODE
  // ---------------------------------------------------------------------------
  if (stim.custom_disable) {                                                                  // GUI custom stimulus disabled: use board pots

    // -------------------------------------------------------------------------
    // 1. Read stimulus strength potentiometer
    // -------------------------------------------------------------------------
    if (pot.use_stimstrength_pot) {

      stim.strPot_raw = ADC1.read(stim.pin_strPot);                                           // Raw ADC: 0..4095
      stim.strPot = (int)stim.strPot_filt.update((uint16_t)stim.strPot_raw);                  // Filtered ADC
      stim.strPot_f = stim.strPot_filt.filt_f;                                                // Debug / legacy float value

      stim.strPot_centered = stim.strPot - pot.half_range;                                    // Centre around 0

      if (stim.strPot_centered >= pot.offset) {                                               // Positive side outside dead-zone
        stim.strPot_adj  = stim.strPot_centered - pot.offset;
        stim.str_digital = (int16_t)lroundf(stim.strPot_adj * stim.str_digitalMap);
        stim.str_analog  = (int16_t)lroundf(stim.strPot_adj * stim.str_analogMap);

      } else if (stim.strPot_centered <= -pot.offset) {                                       // Negative side outside dead-zone
        stim.strPot_adj  = stim.strPot_centered + pot.offset;
        stim.str_digital = (int16_t)lroundf(stim.strPot_adj * stim.str_digitalMap);
        stim.str_analog  = (int16_t)lroundf(stim.strPot_adj * stim.str_analogMap);

      } else {                                                                                // Centre dead-zone
        stim.strPot_adj  = 0;
        stim.str_digital = 0;
        stim.str_analog  = 0;
      }
    }

    // Clamp strength explicitly to the intended -100..+100 command range
    stim.str_digital = constrain(stim.str_digital, -100, 100);
    stim.str_analog  = constrain(stim.str_analog,  -100, 100);

    // Analogue stimulus magnitude, 0..100 %
    stim.amp = constrain(abs(stim.str_analog), 0, 100);

    // For V2.5 midpoint-DAC output:
    // 0 %   -> DAC step 0
    // 100 % -> DAC step stim_dac_span, normally 127 for ESP32 8-bit DAC
    stim.value_analog = (int)lroundf((float)stim.amp * stim.current_scaling);
    stim.value_analog = constrain(stim.value_analog, 0, (int)stim_dac_span);

    // Digital light stimulus is positive-only
    if (stim.str_digital > 0) {
      stim.value_digital = (int)(((int32_t)stim.str_digital * (int32_t)spike.ledc_Max + 50) / 100);
    } else {
      stim.value_digital = 0;
    }

    stim.value_digital = constrain(stim.value_digital, 0, spike.ledc_Max);

    // -------------------------------------------------------------------------
    // 2. Read stimulus frequency potentiometer
    // -------------------------------------------------------------------------
    if (pot.use_stimfrequency_pot) {

      stim.freqPot_raw = ADC1.read(stim.pin_freqPot);                                        // Raw ADC: 0..4095
      stim.freqPot = (int)stim.freqPot_filt.update((uint16_t)stim.freqPot_raw);              // Filtered ADC
      stim.freqPot_f = stim.freqPot_filt.filt_f;

      stim.freqPot_centered = stim.freqPot - pot.half_range;                                 // Centre around 0

      stim.denom = float(pot.half_range - pot.offset);                                       // Usable half-span outside dead-zone
      stim.freq_map_full = 100.0f / ((stim.denom > 1.0f) ? stim.denom : 1.0f);

      if (stim.freqPot_centered >= pot.offset) {
        stim.freqPot_adj = stim.freqPot_centered - pot.offset;
        stim.freq = (int16_t)lroundf(-stim.freqPot_adj * stim.freq_map_full);

      } else if (stim.freqPot_centered <= -pot.offset) {
        stim.freqPot_adj = stim.freqPot_centered + pot.offset;
        stim.freq = (int16_t)lroundf(-stim.freqPot_adj * stim.freq_map_full);

      } else {
        stim.freqPot_adj = 0;
        stim.freq = 0;
      }
    }

    stim.freq = constrain(stim.freq, -100, 100);

    // -------------------------------------------------------------------------
    // 3. Apply frequency immediately
    // -------------------------------------------------------------------------
    // Same period formula as before, but now recalculated every loop.
    // This is the key fix: the frequency pot is no longer waiting for the old
    // cycle to finish before changing stim.steps.
    stim.steps_f = stim.dutyCycle
                 + ((stim.freq * stim.dutyCycle) * 0.01f)
                 + stim.dutyCycle_Min;

    stim.steps = (int)lroundf(stim.steps_f);

    if (stim.steps < 2) {
      stim.steps = 2;
    }

    // If the new frequency setting made the current counter invalid,
    // restart immediately.
    if (stim.counter >= stim.steps) {
      stim.counter = 0;
      stim.trigger_enable = true;
    }

    // -------------------------------------------------------------------------
    // 4. Generate square-wave phase
    // -------------------------------------------------------------------------
    const int onSteps = max(1, stim.steps / 2);
    const bool phaseOn = (stim.counter < onSteps);

    const bool analogActive = (abs(stim.str_analog) >= stim.str_analog_min);

    const int signedDacStep = analogActive
                            ? ((stim.str_analog > 0) ? stim.value_analog : -stim.value_analog)
                            : 0;

    if (phaseOn) {
      stim.pwm   = stim.value_digital;
      stim.dac   = (int)stim_dac_zero + signedDacStep;
      stim.state = analogActive ? stim.str_analog : 0;

    } else {
      stim.pwm   = 0;
      stim.dac   = (int)stim_dac_zero;
      stim.state = 0;
    }

    stim.dacVal = (uint8_t)constrain(stim.dac, 0, dac_max);

    ledcWrite(stim.pin_stim_light, stim.pwm);
    dacWrite(stim.pin_stim_current, stim.dacVal);

    // -------------------------------------------------------------------------
    // 5. Trigger pulse and counter update
    // -------------------------------------------------------------------------
    if (stim.trigger_enable) {
      stim.trigger = 1;
      stim.trigger_enable = false;
    } else {
      stim.trigger = 0;
    }

    stim.counter++;

    if (stim.counter >= stim.steps) {
      stim.counter = 0;
      stim.trigger_enable = true;
    }
  }

  // ---------------------------------------------------------------------------
  // CUSTOM / SERIAL STIMULUS MODE
  // ---------------------------------------------------------------------------
  else {

    // -------------------------------------------------------------------------
    // 1. Serial trigger
    // -------------------------------------------------------------------------
    stim.trigger = 0;

    if (stim.serialTrigger_enable) {
      stim.trigger = 1;
      stim.serialTrigger_enable = false;
    }

    // -------------------------------------------------------------------------
    // 2. Smooth host command
    // -------------------------------------------------------------------------
    stim.cmd_in = stim.value_custom;                                                          // Signed command, expected -100..+100

    if (abs(stim.cmd_in - stim.cmd_hold) > stim.cmd_deadband) {
      stim.cmd_hold = stim.cmd_in;
    }

    stim.cmd_f += stim.cmd_alpha * ((float)stim.cmd_hold - stim.cmd_f);
    stim.cmd = (int)lroundf(stim.cmd_f);

    stim.cmd = constrain(stim.cmd, -100, 100);

    stim.cmd_abs = (stim.cmd >= 0) ? stim.cmd : -stim.cmd;
    stim.custom_active = (stim.cmd_abs >= stim.str_analog_min);

    // -------------------------------------------------------------------------
    // 3. Digital light stimulus: positive-only
    // -------------------------------------------------------------------------
    if (stim.custom_active && stim.cmd > 0) {
      stim.value_digital = (int)(((int32_t)stim.cmd * (int32_t)spike.ledc_Max + 50) / 100);
    } else {
      stim.value_digital = 0;
    }

    stim.value_digital = constrain(stim.value_digital, 0, spike.ledc_Max);

    // -------------------------------------------------------------------------
    // 4. Analogue current stimulus: bipolar around stim_dac_zero
    // -------------------------------------------------------------------------
    stim.value_analog = stim.custom_active
                      ? (int)lroundf((float)stim.cmd_abs * stim.current_scaling)
                      : 0;

    stim.value_analog = constrain(stim.value_analog, 0, (int)stim_dac_span);

    const int signedDacStep = stim.custom_active
                            ? ((stim.cmd > 0) ? stim.value_analog : -stim.value_analog)
                            : 0;

    stim.pwm = stim.value_digital;
    stim.dac = (int)stim_dac_zero + signedDacStep;

    stim.state = stim.custom_active ? stim.cmd : 0;

    stim.dacVal = (uint8_t)constrain(stim.dac, 0, dac_max);

    ledcWrite(stim.pin_stim_light, stim.pwm);
    dacWrite(stim.pin_stim_current, stim.dacVal);
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                    Stimulus - Applying Analog Values                                  */


inline void update_StimulusCurrentIn() {

  patch.input_value_raw = ADC2.read(patch.pin);                                               // Raw ADC counts: 0..4095
  patch.input_value_f += patch.alpha_in * ((float)patch.input_value_raw - patch.input_value_f);
  patch.input_value = (uint16_t)lroundf(patch.input_value_f);

  // With midpoint DAC logic, DAC OFF is stim_dac_zero, not 0.
  // So do NOT use stim.dacVal == 0 anymore.
  //
  // The cleanest activity marker is stim.state:
  //   stim.state != 0 -> stimulus ON phase
  //   stim.state == 0 -> stimulus OFF phase
  const bool stimOutputActive = (fabsf(stim.state) >= (float)stim.str_analog_min);

  // Track the current-in baseline only during the OFF phase.
  if (!stimOutputActive) {
    patch.current_in_zero = 0.99f * patch.current_in_zero + 0.01f * (float)patch.input_value;
  }

  patch.pot_centered = (float)patch.input_value - patch.current_in_zero;

  if (patch.pot_centered >= pot.offset) {
    patch.pot_adj = patch.pot_centered - pot.offset;
  } else if (patch.pot_centered <= -pot.offset) {
    patch.pot_adj = patch.pot_centered + pot.offset;
  } else {
    patch.pot_adj = 0.0f;
  }

  // Get stimulus polarity from the active stimulus command.
  if (stim.custom_disable) {
    if (stim.str_analog > stim.str_analog_min) {
      stim.sign = +1.0f;
    } else if (stim.str_analog < -stim.str_analog_min) {
      stim.sign = -1.0f;
    } else {
      stim.sign = 0.0f;
    }
  } else {
    if (stim.cmd > stim.str_analog_min) {
      stim.sign = +1.0f;
    } else if (stim.cmd < -stim.str_analog_min) {
      stim.sign = -1.0f;
    } else {
      stim.sign = 0.0f;
    }
  }

  // If the stimulus is OFF, or there is no valid sign, force zero current input.
  if (!stimOutputActive || stim.sign == 0.0f) {
    patch.current_input = 0.0f;

    if (clampMode == ClampMode::VoltageClamp) {
      patch.v_step = 0.0f;
      patch.v_cmd = constrain(patch.v_hold, neuron.Vm_min, neuron.Vm_peak);
      stim.state = (int)lroundf(patch.v_cmd);
    }

    return;
  }

  // Voltage clamp interpretation
  if (clampMode == ClampMode::VoltageClamp) {
    const float usableHalfSpan = (float)(pot.half_range - pot.offset);

    patch.magnitude = (fabsf(patch.pot_adj) / usableHalfSpan) * patch.v_step_max;
    patch.magnitude = constrain(patch.magnitude, 0.0f, patch.v_step_max);

    patch.v_step = stim.sign * patch.magnitude;
    patch.v_cmd = constrain(patch.v_hold + patch.v_step, neuron.Vm_min, neuron.Vm_peak);

    patch.current_input = 0.0f;
    stim.state = (int)lroundf(patch.v_cmd);

    return;
  }

  // Current clamp interpretation
  float currentMagnitude = fabsf(patch.pot_adj) * patch.input_scaling;
  currentMagnitude = constrain(currentMagnitude, 0.0f, 100.0f);

  patch.current_input = stim.sign * currentMagnitude;
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

  // A spike event is now defined only by the model event flag.
  // Do not re-detect spikes from neuron.v here, because neuron.v may already
  // have been reset to neuron.c before this function runs.
  const bool spike_now = (clampMode != ClampMode::VoltageClamp) && neuron.spike;


  // ---------------------------------------------------------------------------
  // 1. Select displayed/exported Vm
  // ---------------------------------------------------------------------------

  if (spike_now) {
    neuron.v_out = neuron.Vm_peak;
  }
  else {
    neuron.v_out = neuron.v;
  }


  // ---------------------------------------------------------------------------
  // 2. Digital axon output
  // ---------------------------------------------------------------------------

  if (spike_now) {
    digitalWrite(axon.pin_digital, HIGH);
  }
  else {
    digitalWrite(axon.pin_digital, LOW);
  }


  // ---------------------------------------------------------------------------
  // 3. Separate spike GPIO / buzzer output
  // ---------------------------------------------------------------------------
  // Important:
  // pins.gpio.spike is NOT the RGB LED.
  // On your board this may be the red spike indicator / buzzer driver.
  // So it can still flash red even when the RGB LED is correctly flashing white.

  if (spike_now && spike.Buzzer_enable) {
    digitalWrite(pins.gpio.spike, HIGH);
  }
  else {
    digitalWrite(pins.gpio.spike, LOW);
  }


  // ---------------------------------------------------------------------------
  // 4. RGB Vm/spike LED
  // ---------------------------------------------------------------------------

  if (spike.LED_enable) {

    if (spike_now) {

      // Spike event: full red power + green/blue cathodes ON.
      // This produces a white-ish flash on the faulty RGB wiring.
      setSpikeRgbLedWhite();
    }
    else {

      // Vm display: red-only brightness proportional to Vm.
      // On the V2.5 faulty RGB wiring, red brightness is controlled by PWM on
      // the common-anode power pin GPIO27. Green and blue remain OFF.
      spike.led_Vm_pwmf = (neuron.v_out - neuron.Vm_min) * spike.led_Vm;

      spike.led_Vm_pwm = int(constrain(spike.led_Vm_pwmf,
                                       0.0f,
                                       float(spike.ledc_Max)));

      setVmRgbLed((uint16_t)spike.led_Vm_pwm);
    }
  }
  else {
    setRgbLedOff();
  }


  // ---------------------------------------------------------------------------
  // 5. Analog axon Vm output
  // ---------------------------------------------------------------------------

  axon.norm = (neuron.v_out - neuron.Vm_min) * axon.Vm_range;
  axon.norm = constrain(axon.norm, 0.0f, 1.0f);

  axon.dacVal = axon.norm * dac_max + 0.5f;
  dacWrite(axon.pin_analog, axon.dacVal);
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
  //wifiSendSamplePacket(pkt);
}




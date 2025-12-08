#pragma once     
#include "General_settings.h"



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                               Setting Voltage membrane clamp value                                    */

inline void update_InputCurrent() {
  if (!IC.enable) return;                                                                     // If GUI/serial is overriding the clamp (IC.enable == false), don't read the pot
                                                                                            
  IC.pot_value = ADC1.read(IC.pot_pin) - bits12/2;                                            // Reads IC potentiometer value and scales it to -2048 to 2048

  if (IC.pot_value >= pot.offset){                                                            // If IC potentiometer value is above the offset:
    IC.current_clamp = (IC.pot_value - pot.offset) / IC.pot_scaling;                            // Generates "current" value from the reading, subtracts the offset and scales it from parameters
  }
  else if (IC.pot_value <= -pot.offset){                                                      // If IC potentiometer value is below the offset:
    IC.current_clamp = (IC.pot_value + pot.offset) / IC.pot_scaling;                            // Generates "current" value from the reading, add the offset and scales it from parameters
  }
  else{                                                                                       // If IC potentiometer value is within offset range:
    IC.current_clamp = 0.0f;                                                                    // Set IC current to 0
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                          Noise Generator                                              */

inline void update_Noise() {  
  if (!noise.enable) return;                                                                  // If GUI/serial override is active (noise.enable == false), don't use the pot
  
  noise.pot_value = ADC2.read(noise.pot_pin);                                                 // Reads Noise potentiometer value from 0 to 4095                                                             
  
  if (noise.pot_value <= pot.offset){                                                         // If Noise potentiometer value is below the offset:
    noise.current = 0.0f;                                                                       // Set Noise current to 0
    return;                                                                                     // Return to caller and pass the rest of the void function
  }

  noise.amp = (noise.pot_value - pot.offset) / noise.pot_scaling;                             // Generates Noise amplitude from the reading, substracts the offset and scales it from parameters
  
  noise.newSigma = 0.5f * noise.amp;                                                          // Generate a standard variation (σ) equal to half the Noise amplitude
  
  if (fabsf(noise.newSigma != noise.sigma) > 1e-3f) {                                       // Update Gaussian parameters if sigma has changed significantly
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
  PD.value = ADC1.read(PD.pin);                                                               // Reads Photodiode value from 0 to ~400

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

  PD.current = (PD.average * PD.gain * PD.inv_scaling) * PD.amp;                                  // Generates Photodiode current, amplified by the PD_Gain readings

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

  syn.Vm_input = ADC1.read(syn.pin_analog);                                                   // Reads Synapse Vm input
  syn.Vm = mapfloat(syn.Vm_input,
                    syn.analogOffsetLow,
                    bits12 - syn.analogOffsetHigh, 
                    neuron.Vm_min, 
                    neuron.Vm_max) + axon.offset;                                             // Maps Synapse Vm to Spikeling Neuron range
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                         Total input current                                           */

inline void compute_AllCurrent(){

  neuron.total_current = IC.current_clamp +                                                   // Sums up all input currents: from Clamp 
                         IC.current +                                                         // from Direct current Strimulus
                         PD.current +                                                         // from Light
                         syn1.current +                                                       // from Synapse 2 
                         syn2.current +                                                       // from Synapse 2
                         noise.current;                                                       // from Noise
}


// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                            Stimulus - Determining Analog and Digital Values                           */

inline void update_StimulusOutput() {

/*                                 --  All Stimulus GUI buttons OFF  --                                  */

  if ( stim.strength_enable && stim.custom_enable ) {                                         // If GUI "Stimulus Strength" and "Custom Stimulus" are disabled:
    stim.strPot = ADC2.read(stim.pin_strPot);                                                   // Reads Stimulus Strength potentiometer value
    stim.str_digital = int16_t((stim.strPot - bits12/2)) * stim.str_digitalMap);                // Maps this value from -100 to 100 that will correspond to the digital (LED output) stimulus strength %
    stim.str_analog = int16_t(stim.strPot * stim.str_analogMap - 100.0f);                       // Maps this value from 0 to 100 that will correspond to the analog (Input Current) stimulus strength %
  }
  
  if ( stim.frequency_enable && stim.custom_enable) {                                         // If GUI "Stimulus Frequency" and "Custom Stimulus" are disabled:
    stim.freqPot = ADC2.read(stim.pin_freqPot);                                                 // Reads Stimulus Frequency potentiometer value
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
    
    ledcWrite(stim.pin_stim_light, stim.pwm);                                                 // Stimulating LED
    DAC.write(stim.dac, stim.pin_stim_current);                                               // Stimulus current output


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
      stim.steps = (int)(s + 0.5f);                                                             // Set stimulus steps value
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
                                                     
    stim.value_analog = (int)abs(stim.value_custom) * stim.current_scaling;                     // The stimulus analog output absolute value is scaled to parameters             
    
    ledcWrite(stim.pin_stim_light, constrain(stim.value_digital, 0, ledc_Max));                 // Sends the stimulus digital output value to the stimulating LED
    DAC.write(stim.value_analog, stim.pin_stim_current);                                        // Sends the stimulus analog output value to the Stimulus current output
    
    stim.state = stim.value_custom;                                                             // Register stimulus ON state
  }
}



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                    Stimulus - Applying Analog Values                                  */
 
inline void update_StimulusCurrentIn() {

/*                       -----  Reading analog stimulus input (Current-In)  -----                        */
  
/*                               --  GUI Custom Stimulus button is  OFF --                               */

  if ( stim.custom_enable ){                                                                  // If GUI "Custom Stimulus" button is disabled: 
    IC.value_currentIn = ADC1.read(IC.pin);                                                     // Reads Current-in value
    
    if ( stim.str_analog > stim.str_analog_min){                                                // If the Stimulus Strength output is above a threshold:                                         
      IC.current = IC.value_currentIn * IC.currentIn_scaling;                                     // Scales the Current-in value from parameters and determines the Stimulus Input (Analog Current-in)
    }
    else if ( stim.str_analog < -stim.str_analog_min){                                          // If the Stimulus Strength output is below a negative threshold: 
      IC.current = - IC.value_currentIn * IC.currentIn_scaling;                                   // Negatively scales the Current-in value from parameters and determines the Stimulus Input (Analog Current-in)
    }
    else {                                                                                      // If the Stimulus Strength output is within the threshold range: 
      IC.current = 0.0f;                                                                          // Holds the Current-in value to 0
    }

    if ( stim.state == 0 ){                                                                     // If the Stimulus is in its off period:                                            
      IC.current = 0.0f;                                                                          // Forces the I_Stim value to 0 (prevent analog misreading)
    }
  }

  /*                             --  GUI Custom Stimulus button is  ON  --                           */

  else {                                                                                      // If GUI "Custom Stimulus" button IS ticked: 
    IC.value_currentIn = ADC1.read(IC.pin);                                                     // Reads Current in value

    if ( stim.value_custom >= 0){                                                               // If the Stimulus Strength output is above 0: 
      IC.current = IC.value_currentIn * IC.currentIn_scaling;                                               // Positively scales this value from parameters and determines Current In value
    }
    else if ( stim.value_custom < 0){                                                           // If the Stimulus Strength output is below 0: 
      IC.current =  - IC.value_currentIn * IC.currentIn_scaling;                                            // Negatively scales this value from parameters and determines Current In value
    }

    if ( stim.value_custom == 0){                                                               // If the Custom Stimulus value is 0:     
      IC.current = 0.0f;                                                                          // Forces the I_Stim value to 0 (prevent analog misreading)
    }
  }
}

  

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                       Spike and Axon output                                           */

inline void update_Spike() {

  if ( neuron.spike ) {                                                                       // Whenever neuron is considered to be spiking,
    
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

  else {   
    
    neuron.v_out = neuron.v;                                                                    // The displayed Vm value corresponds to Spikeling Vm
    digitalWrite(axon.pin_digital, LOW);                                                        // Keep the digital output in a LOW state        
    digitalWrite(pins.gpio.spike, LOW); 
                                                                                       // Whenever neuron is not spiking
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
  uint16_t dacVal = uint16_t(norm * bits12 + 0.5f);
  axon.Vm = dacVal;                                                                           // Generates axon Vm by mappint the displayed Vm 
  DAC.write(axon.Vm, axon.pin_analog);                                                        // Sends Axon Vm analog output through the Axon Vm output                                             
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
}



#include "Izhikevich_parameters.h"
#include "Serial_functions.h"


void setup() {
  HardwareSettings();
  Izhikevich_opening();
  SerialFunctions();
  SerialBlank();
  Mode_opening(); 
}


void loop() {
  
  SCmd.readSerial();

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                     Define Spikeling Mode                                             */
  ModeState = digitalRead(pinModeButton);         // Read the mode button state
  if (ModeState == HIGH){                         // If the mode button is pushed:
    Mode += 1;                                      // Increment the Mode by 1
    lightOn(Mode);                                  // Turn next Mode_LED
    a_Izhikevich = Array_a_Izhikevich[Mode];        // Change Izhikevich parameter a to the new mode
    b_Izhikevich = Array_b_Izhikevich[Mode];        // Change Izhikevich parameter b to the new mode
    c_Izhikevich = Array_c_Izhikevich[Mode];        // Change Izhikevich parameter c to the new mode
    d_Izhikevich = Array_d_Izhikevich[Mode];        // Change Izhikevich parameter d to the new mode

    if (Mode >= nModes){                          // If Mode has reached the maximum number of existing modes:
      Mode = 0;                                     // Reset Mode to 0
      lightOn(Mode);                                // Turn First Mode_LED
      a_Izhikevich = Array_a_Izhikevich[Mode];      // Change Izhikevich parameter a to the first mode
      b_Izhikevich = Array_b_Izhikevich[Mode];      // Change Izhikevich parameter b to the first mode
      c_Izhikevich = Array_c_Izhikevich[Mode];      // Change Izhikevich parameter c to the first mode
      d_Izhikevich = Array_d_Izhikevich[Mode];      // Change Izhikevich parameter d to the first mode
    }
    
    delay(Mode_delay);                            // Set a delay to prevent multi_push from the user
  }


// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                               Setting Voltage membrane clamp value                                    */

  if (IC_Flag == true){
    IC_value = ADC1.readADC(pinICPot) - bits/2;       // Reads IC potentiometer value and scales it to -2048 to 2048

    if (-IC_PotOffset < IC_value <= IC_PotOffset){
      I_IC = 0;
    }

    if (IC_value >= IC_PotOffset){
      I_IC = (IC_value - IC_PotOffset) / IC_PotScaling ;                 // Generates "current" value from the reading and scales it from parameters
    }
    if (IC_value <= -IC_PotOffset){
      I_IC = (IC_value + IC_PotOffset) / IC_PotScaling;                 // Generates "current" value from the reading and scales it from parameters
    }
  }
  


// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                          Noise Generator                                              */

  Noise_Gain = ADC1.readADC(pinNoisePot);           // Reads Noise potentiometer value from 0 to 4095
  if (Noise_Flag == true){
    if (Noise_Gain <= Noise_PotOffset){
      I_Noise = 0;
    }
    else {
      Noise_Amp = (Noise_Gain - Noise_PotOffset) / NoiseScaling;          // Generates current value from the reading and scales it from parameters
      Gaussian Noisy (0,Noise_Amp/2);
      I_Noise = Noisy.random();
    }
  }

  if (Noise_Flag == false){
    I_Noise = I_Noise_Gen;
  }



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*              Reading PhotoDiode value and setting PhotoDiode gain for generating input current        */
  PD_Value = ADC2.readADC(pinPD);                   // Reads Photodiode value from 0 to ~400
  
  if ( PD_counter < PD_avg ){                     // If, for this void loop, the PD counter has not reached the max count number:
    PD_counter +=1;                                 // Increment the counter by 1
  }
  else{                                           // If the PD counter has reached the max count number:
    PD_counter = 0;                                 // Reset the counter to 0
  }
  PD_Value_Array[PD_counter] = PD_Value;          // For this void loop, assign the current PD value to the PD_Value_Array at the current counter position
  PD_Value_Sum = 0;                               // Reset the previous PD_Value_Sum
  for ( int i = 0; i < PD_avg; i++){              // For all current PD_array values:
    PD_Value_Sum += PD_Value_Array[i];              // Sum up all values within the array...
  }
  PD_Value_Average = PD_Value_Sum / PD_avg;       // ... then average them

  if (PDGain_Flag == true){
    PD_PotValue = ADC1.readADC(pinPDPot) - bits/2; // Reads Photodiode Gain potentiometer value and scales it to -2048 to 2048
    PD_Amp = map(PD_PotValue, -bits/2, bits/2, -PD_PotRange, PD_PotRange);
  }

  if (PD_Amp >= 0){
    PD_Polarity = 1;
  }
  if (PD_Amp < 0){
    PD_Polarity = -1;
  }
  
                   // Generates an amplification value from the reading and scales it from parameters 

  I_PD = (PD_Value_Average * PD_Amp / PD_Scaling) * PD_Gain;  // Finally, generates a current input from the photodiode readings, amplified byt the PD_Gain readings

  if (PDDecay_Flag == true){
    PD_Decay = 0.001;
  }

  if (PD_Gain > PD_gain_mini){                     // When PD_amp is above the minimum value:
    PD_Gain -= PD_Polarity * PD_Decay * I_PD;                      // Adapts proportionally to I_PD
    if (PD_Gain < PD_gain_mini){                     // If PD_amp becames lower than the minimum value:
      PD_Gain = PD_gain_mini;                          // Then PD_amp remains at the minimum value
    }
  }

  if (PDRecovery_Flag == true){
    PD_Recovery = 0.025;
  }

  if (PD_Gain < 1.0){
    PD_Gain +=  PD_Recovery;                        // Recovers by constant % per iteration
  }

     
// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                             Synapse 1                                                 */

  SpikeIn1State = digitalRead(pinSyn1_D);         // Reads Synapse 1 digital input

  if (Syn1Gain_Flag == true){
    Syn1_Gain = ADC1.readADC(pinSyn1Pot) - bits/2;    // Reads Synaptic Gain 1 potentiometer value and scales it to -2048 to 2048
    
    if (-Syn1_PotOffset <= Syn1_Gain <= Syn1_PotOffset){
      Syn1_Amp = 0;
    }

    if (Syn1_Gain >= Syn1_PotOffset){
      Syn1_Amp = (Syn1_Gain - Syn1_PotOffset) / Syn1PotScaling;          // Generates current value from the reading and scales it from parameters
    }
    if (Syn1_Gain <= -Syn1_PotOffset){
      Syn1_Amp = (Syn1_Gain + Syn1_PotOffset) / Syn1PotScaling;          // Generates current value from the reading and scales it from parameters
    }

  }
  
  if (SpikeIn1State == HIGH){                     // If Spike is detected
    I_Synapse1 += Syn1_Amp;                         // Apply the synaptic current from Syn1 related to the synaptic gain 1
  }
  
  if (Syn1Decay_Flag == true){
    Synapse1_decay = 0.995;
  }
  
  I_Synapse1 *= Synapse1_decay;                   // Decay synaptic current towards zero

  Axon_AnalogInput1 = ADC2.readADC(pinSyn1_A);
  Syn1_Vm = mapfloat(Axon_AnalogInput1,Syn_AnalogOffsetLow, bits11-Syn_AnalogOffsetHigh, Vm_min, Vm_max) + Axon_AnalogOffset;

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                             Synapse 2                                                 */

    SpikeIn2State = digitalRead(pinSyn2_D);         // Reads Synapse 1 digital input

  if (Syn2Gain_Flag == true){
    Syn2_Gain = ADC1.readADC(pinSyn2Pot) - bits/2;    // Reads Synaptic Gain 1 potentiometer value and scales it to -2048 to 2048
    
    if (-Syn2_PotOffset <= Syn2_Gain <= Syn2_PotOffset){
      Syn2_Amp = 0;
    }

    if (Syn2_Gain >= Syn2_PotOffset){
      Syn2_Amp = (Syn2_Gain - Syn2_PotOffset) / Syn2PotScaling;          // Generates current value from the reading and scales it from parameters
    }
    if (Syn2_Gain <= -Syn2_PotOffset){
      Syn2_Amp = (Syn2_Gain + Syn2_PotOffset) / Syn2PotScaling;          // Generates current value from the reading and scales it from parameters
    }

  }
  
  if (SpikeIn2State == HIGH){                     // If Spike is detected
    I_Synapse2 += Syn2_Amp;                         // Apply the synaptic current from Syn1 related to the synaptic gain 1
  }
  
  if (Syn2Decay_Flag == true){
    Synapse2_decay = 0.995;
  }
  
  I_Synapse2 *= Synapse2_decay;                   // Decay synaptic current towards zero

  Axon_AnalogInput2 = ADC2.readADC(pinSyn2_A);
  Syn2_Vm = mapfloat(Axon_AnalogInput2,Syn_AnalogOffsetLow, bits11-Syn_AnalogOffsetHigh, Vm_min, Vm_max) + Axon_AnalogOffset;



// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                               Stimulus                                                */
// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 


  // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
  /*                   Determining and Apllying Stimlus Analog and Digital Values                    */


  /*                                  All Stimulus GUI buttons OFF                                   */

  if ( StimStr_Flag == true && StimCus_Flag == true) {                    // If GUI "Stimulus Strength" and "Custom Stimulus" buttons are NOT ticked:
    StimStr_Value = ADC1.readADC(pinStimStrPot);                            // Reads Stimulus Strength potentiometer value
    StimStrD = map(StimStr_Value -bits/2, -bits/2, bits/2, -100 , 100);     // Map this value from -100 to 100 that will correspond to the digital (LED output) stimulus strength %
    StimStrA = map(StimStr_Value, 0, bits, -100, 100);                      // Map this value from 0 to 100 that will correspond to the analog (Input Current) stimulus strength %
  }
  
  if ( StimFre_Flag == true && StimCus_Flag == true) {                    // If GUI "Stimulus Frequency" and "Custom Stimulus" buttons are NOT ticked:
    StimFre_Value = ADC1.readADC(pinStimFrePot);                            // Reads Stimulus Frequency potentiometer value
    StimFre = map(StimFre_Value, 0, bits, 100 , -100);                      // Map this value from 100 to -100 
  }


  /*                                GUI Custom Stimulus button is  OFF                               */

  if ( StimCus_Flag == true ){                                            // If GUI "Custom Stimulus" button is NOT ticked:
    if ( StimStrD >= 0 ){                                                   // If the Stimulus Strength value is not negative:
      Stim_val_D = (StimStrD * StimLED_scaling);                            // The stimulus digital output is proportional to the potentiometer reading and scaled from parameters
    }
    Stim_val_A = abs(StimStrA) * Stim_CurrentScaling;                       // The stimulus analog output absolute value is proportional to the potentiometer reading and scaled to parameters
  

    if ( Stim_counter < Stim_steps/2 ){                                     // If the number of void loops has not reached half the stimulus duty cycle:
      analogWrite(pinStim_D, Stim_val_D);                                     // Sends the stimulus digital output value to the stimulating LED
      dacWrite(pinStim_A, Stim_val_A);                                        // Sends the stimulus analog output value to the Current in
      Stim_State = StimStrA;                                                  // Register stimulus ON
    }
    if ( Stim_counter > Stim_steps/2 ){                                     // If number of void loops has exceeded half the stimulus duty cycle period:
      analogWrite(pinStim_D, 0);                                              // Nothing is sent throught the digital output
      dacWrite(pinStim_A, 0);                                                 // Nothing is sent throught the analog output
      Stim_State = 0;                                                         // Register stimulus OFF
    }

    Stim_counter += 1;                                                      // Increment the void loop counter by 1
    
    if ( TriggerFlag == false ){
      Trigger = 0;  
    }

    if ( TriggerFlag == true ){
      Trigger = 1;
      TriggerFlag = false;
    }

    if ( Stim_counter >= Stim_steps ){                                      // If the void loop counter has reached the stimulus duty cycle period:
      Stim_counter = 0;                                                       // Reset the void loop counter
      TriggerFlag = true;
      Stim_steps = round (Stim_DutyCycle + ((StimFre * Stim_DutyCycle) / 100)) + Stim_minDutyCycle;  // Define the stimulus duty cycle period proportional to the stimulus frequency potentiometer value
    }
  }
  


  /*                                  GUI Custom Stimulus Button ON                                  */

  if (StimCus_Flag == false){                                             // If GUI "Custom Stimulus" button IS ticked:
    Trigger = 0; 
    if ( SerialTrigger_Flag == true ){
      Trigger = 1;  
      SerialTrigger_Flag = false;
    }
    if (StimCus_val > 0){                                                   // If the Custom Stimulus value is aobve 0:
      Stim_val_D = (StimCus_val * StimLED_scaling);                           // Applies the serial received stimulus value to the stimulating LED and scales from parameters
    }
    if (StimCus_val <= 0){                                                  // If the Custom Stimulus value is below or equal to 0:
      Stim_val_D = 0;                                                         // Applies a 0 value to the stimulating LED
    }
                                                     
    Stim_val_A = abs(StimCus_val) * Stim_CurrentScaling;                    // The stimulus analog output absolute value is scaled to parameters             
    
    analogWrite(pinStim_D, Stim_val_D);                                     // Sends the stimulus digital output value to the stimulating LED
    dacWrite(pinStim_A, Stim_val_A);                                        // Sends the stimulus analog output value to the Current in
    
    Stim_State = StimCus_val;                                               // Register stimulus ON
  }


  // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
  /*                           Reading analog stimulus input (Current-In)                            */
 

  /*                                GUI Custom Stimulus button is  OFF                               */

  if ( StimCus_Flag == true ){                                            // If GUI "Custom Stimulus" button is NOT ticked: 
    CurrentIn_Value = ADC2.readADC(pinCurrentIn);                           // Reads Current-in value
    

    if ( StimStrA > StimStrA_mini){                                         // If the Stimulus Strength output is above a threshold:                                         
      I_Stim = CurrentIn_Value * CurrentInScaling;                            // Scales the Current-in value from parameters and determines the Stimulus Input (Analog Current-in)
    }
    else if ( StimStrA < -StimStrA_mini){                                   // If the Stimulus Strength output is below a negative threshold: 
      I_Stim = - CurrentIn_Value * CurrentInScaling;                          // Negatively scales the Current-in value from parameters and determines the Stimulus Input (Analog Current-in)
    }
    else if ( -StimStrA_mini <= StimStrA <= StimStrA_mini ){                // If the Stimulus Strength output is within the threshold range: 
      I_Stim = 0;                                                             // Holds the Current-in value to 0
    }

    if ( Stim_State == 0 ){                                                 // If the Stimulus is in its off period:                                            
      I_Stim = 0;                                                             // Forces the I_Stim value to 0 (prevent analog misreading)
    }
  }

  /*                                GUI Custom Stimulus button is  ON                                */

  if (StimCus_Flag == false){                                             // If GUI "Custom Stimulus" button IS ticked: 
    CurrentIn_Value = ADC2.readADC(pinCurrentIn);                           // Reads Current in value

    if ( StimCus_val >= 0){                                               // If the Stimulus Strength output is above 0: 
      I_Stim = CurrentIn_Value * CurrentInScaling;                          // Positively scales this value from parameters and determines Current In value
    }
    else if ( StimCus_val < 0){                                           // If the Stimulus Strength output is below 0: 
      I_Stim =  - CurrentIn_Value * CurrentInScaling;                       // Negatively scales this value from parameters and determines Current In value
    }

    if ( StimCus_val == 0){                                               // If the Custom Stimulus value is 0:     
      I_Stim = 0;                                                           // Forces the I_Stim value to 0 (prevent analog misreading)
    }
  }

  
  

// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                      Spikeling computation running on Izhikevich mmodel                               */
// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 


  I_Total = I_IC + I_PD + I_Stim + I_Synapse1 + I_Synapse2 + I_Noise;     // Sum up all input currents
  
  v = v + timestep_ms*(0.04 * sq(v) + 5*v + 140 - u + I_Total);           // Compute the voltage variable
  u = u + timestep_ms*(a_Izhikevich * (b_Izhikevich * v - u));            // Compute the recovery variable

  if (v >= Vm_peak){                                                      // If the voltage value is above the peak (30mV by default):
    v = c_Izhikevich;                                                       // The voltage variable corresponds to the "after spike reset value"
    u = u + d_Izhikevich;                                                   // The recovery variable is incremented by the "after spike reset of recovery variable"
  }
  
  if (v <= Vm_min) {                                                      // If voltage goes below the min voltage value (-90mV by default):
    v = Vm_min;                                                             // Keep the voltage at Vm_min : Prevent pinVm going into overdrive - but also means that it will flatline at Vm_min. 
  } 

  if (v >= 0){
    v = Vm_peak;
  }




// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 
/*                                               Axon                                                    */
// // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // // 

  spike = false;                                                          // Reset spike registration 

  if  (v >= Vm_spike) {                                                   // If voltage goes above the spike value ( -30mV by default)
    if ( Buzzer_Flag == true ){                                             //
      digitalWrite(pinSpike, HIGH);                                           // Activate the spike buzzer
    }
    if ( LED_Flag == true ){                                                //
      digitalWrite(pinLEDSpike1,LOW);                                         //
      digitalWrite(pinLEDSpike2,LOW);                                         //
      digitalWrite(pinLEDVm,LOW);                                             //
    }
    spike = true;                                                           // Register the spike
  }  
  else {                                                                  // Otherwise,
    digitalWrite(pinSpike, LOW);                                            // Keep buzzer silent
    if ( LED_Flag == true ){                                                //
      digitalWrite(pinLEDSpike1,HIGH);                                        //
      digitalWrite(pinLEDSpike2,HIGH);                                        //
      analogWrite(pinLEDVm,map(v, Vm_min, Vm_peak, 0 , bits9));               //
    }
  }    

 if (spike == true){                                                      // If spike is registered
    digitalWrite(pinAxon_D, HIGH);                                          // Send digital output thourgh the Axon digital pin
  }
  else {                                                                  // Otherwise,
    digitalWrite(pinAxon_D, LOW);                                           // Keep the digital pin in a LOW state
  }   

  Axon_AnalogOutput = map(v,Vm_min, Vm_max, 0,bits8);                    //
  dacWrite(pinAxon_A,Axon_AnalogOutput);                                  //


  Serial.print(v);            Serial.print(',');
  Serial.print(Stim_State);   Serial.print(',');
  Serial.print(I_Total);      Serial.print(',');
  Serial.print(Syn1_Vm);      Serial.print(',');
  Serial.print(I_Synapse1);   Serial.print(',');
  Serial.print(Syn2_Vm);      Serial.print(',');
  Serial.print(I_Synapse2);   Serial.print(',');
  Serial.println(Trigger);

  delay(3);
}

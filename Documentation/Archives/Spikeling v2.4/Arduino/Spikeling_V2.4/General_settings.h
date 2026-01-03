/*          ---  General Settings  ---
*/

#include <MCP3208.h>
#include <Gaussian.h>
MCP3208 ADC1;
MCP3208 ADC2;

// // // // // // // // // // // // // // // // // // // // // // // //
/*                       Hardware parameters                         */
int BaudRate = 250000;
int bits8 = 255;
int bits9 = 511;
int bits10 = 1023;
int bits11 = 2047;
int bits12 = 4095;
int bits = bits12;
int Mode = 0;
int ModeState = 0;

// // // // // // // // // // // // // // // // // // // // // // // //
/*                          Pin Definition                           */

int pinADC_Sck     =  18;
int pinADC_MOSI    =  32;
int pinADC_MISO    =  33;
int pinADC_CS1     =  0;
int pinADC_CS2     =  4;

int pinICPot       =   0;        // ADC 1.0: Inject Current potentiometer pin
int pinSpike       =   13;       // Buzzer pin

int pinSyn1_D      =  35;        // Input Digital pin for Synapse 1
int pinSyn1_A      =   0;        // ADC 2.0: Input Analog pin for Synapse 1
int pinSyn1Pot     =   1;        // ADC 1.1: Synapse 1 Gain potentiometer pin

int pinSyn2_D      =  34;        // Input Digital pin for Synapse 2
int pinSyn2_A      =   1;        // ADC 2.1:Input Analog pin for Synapse 2
int pinSyn2Pot     =   2;        // ADC 1.2: Synapse 2 Gain potentiometer pin
 
int pinAxon_D      =  15;        // Output Digital pin for the axon
int pinAxon_A      =  25;        // OutputAnalog pin for the axon

int pinPD          =   2;        // ADC 2.2:Photodiode reading pin
int pinPDPot       =   3;        // ADC 1.3: Photodiode Gain potentiometer pin

int pinModeButton  =  39;        // Mode Button pin
int pinStim_D      =  22;        // Output Digital pin for the stimulating LED
int pinStim_A      =  26;        // Output Analog pin for the stimulating Current Input pin
int pinStimStrPot  =   4;        // ADC 1.4: Stimulus amplitude potentiometer pin
int pinStimFrePot  =   5;        // ADC 1.5: Stimulus frequency potentiometer pin
int pinCurrentIn   =   3;        // ADC 2.3: Input Analog pin for CurrentIn stimuli
int pinNoisePot    =   6;        // ADC 1.6: Noise generator potentiometer pin
int pinLEDVm       =  27;
int pinLEDSpike1   =  14;
int pinLEDSpike2   =  12;


// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Neuron parameters                         */
int      Vm_min    = -110;        // Minimum voltage value the v variable from Izhikevich can take
int      Vm_max    =  100;        // Maximum voltage value 
int      Vm_spike  = -30;        // Voltage value above which the neuron will spike
int      Vm_peak   =  30;        // Voltage peak value from which the v variable will start its recovery
boolean  spike     = false;      // Boolean used for registrating spike events
float    I_Total;                // Sum of all applied current to the neuron (I_IC, I_PD, I_Synapse1, I_Synapse2, I_Stim, I_Noise) 


// // // // // // // // // // // // // // // // // // // // // // // //
/*                     Voltage Clamp parameters                      */
int   IC_value;                  // Inject Current potentiometer value
int   IC_PotOffset  = 200;
int   IC_PotScaling =  bits/100;  // Inject Current value scaling - The lower, the stronger the impact of the IC potentiometer
float I_IC;                      // "Current" value generated from the two previous variables in order to modify the holding voltage value


// // // // // // // // // // // // // // // // // // // // // // // //
/*                       Synapse1 parameters                         */
int SpikeIn1State;               // Synapse 1 digital input
int Syn1_Gain;                   // Synapse 1 gain potentiometer value
float Syn1PotScaling =  bits/50;        // Synapse 1 gain sacaling - The lower, the stronger the impact of the Syn1_Potentiometer.  Default = 2
float Syn1_Amp;                    // Synapse 1 applied gain
int Syn1_PotOffset = 200;
int Syn_AnalogOffsetLow = -10;
int Syn_AnalogOffsetHigh = -400;
int Syn1_offset = 100;
float I_Synapse1 = 0.0;                  // Synapse 1 input current
float Synapse1_decay = 0.995;      // Synpase 1 decay rate. The difference to 1 matters - the smaller the difference, the slower the decay. Default  = 0.995
int Syn1_Vm;

// // // // // // // // // // // // // // // // // // // // // // // //
/*                       Synapse2 parameters                         */
int SpikeIn2State;               // Synapse 2 digital input
int Syn2_Gain;                   // Synapse 2 gain potentiometer value
float Syn2PotScaling =  bits/50;        // Synapse 2 gain sacaling - The lower, the stronger the impact of the Syn2_Potentiometer.  Default = 2
float Syn2_Amp;                    // Synapse 2 applied gain
int Syn2_PotOffset = 200;
int Syn2_offset = 100;
float I_Synapse2 = 0.0;                  // Synapse 2 input current
float Synapse2_decay = 0.990;      // Synpase 2 decay rate. The difference to 1 matters - the smaller the difference, the slower the decay. Default  = 0.990
int Syn2_Vm;

// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Axon parameters                           */
int Axon_AnalogOutput;
float Axon_AnalogScalling;
float Axon_AnalogInput1;
float Axon_AnalogInput2;
float Axon_AnalogOffset = -6.75;


// // // // // // // // // // // // // // // // // // // // // // // //
/*                      PhotoDiode parameters                        */
float PDPotScaling  = bits/25;    // the lower, the stronger the impact on PD_Gain
int   PD_PotRange = 10;
float PD_Gain=1.0;
float PD_PotValue;
float PD_Amp;
float PD_Value;
float PD_Scaling = 0.5;
int PD_Value_Array[] = {0,0,0,0,0,0,0,0,0,0};
int PD_counter = 0;
float PD_avg = 10;
float PD_Value_Sum;
float PD_Value_Average;
float PD_Decay = 0.001;
float PD_gain_mini = 0.0;  // the photodiode gain cannot decay below this value
float PD_Recovery = 0.025;
float I_PD;
int PD_Polarity = 1;


// // // // // // // // // // // // // // // // // // // // // // // //
/*                        Stimuli parameters                         */
int StimStr_Value;               // Stimulus Strength potentiometer value
int StimStrD;                     // Scaled stimulus strength
int StimStrA;
int StimStrA_mini = 5;
int Stim_val_D          = 0;     // Stimulus Digital output for stimulating LED
int Stim_val_A          = 0;     // Stimulus Analog output ofr Current in pin
int StimCus_val         = 0;
int StimCus_D           = 0;
int StimCus_A           = 0;
float Stim_state;                  // Status of the stimulus (ON or OFF / 1 or 0);
float StimLED_scaling     = 5.12;    // Scaling applied to the digital out value
int StimLED_offset = 10;
float Stim_CurrentScaling = 0.9;  // Scaling applied to the analog out value
float I_Stim_mini = 0;

int StimFre_Value;               // Stimulus Frequency potentiometer value
int StimFre;                     // Scaled stimulus frequency
int Stim_counter = 0;            // Stimulus step counter (number of void loops)
int Stim_steps = 0;              // Number of steps required for half a stimulus duty cycle
int Stim_DutyCycle = 500;        // Default stimulus duty cycle value
int Stim_minDutyCycle = 10;      // Minimum loop steps the stimulus duty cycle cannot fall under

int Stim_State;
int CurrentIn_Value;             // Stimulus Current-In value read for the voltage clamp
float CurrentInScaling = 0.1;
int I_Stim = 0;                  // Patch Current-In current


// // // // // // // // // // // // // // // // // // // // // // // //
/*                        Trigger parameters                         */
int Trigger = 0;


// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Noise parameters                          */
int   Noise_Gain;                // Noise potentiometer value
int   NoiseScaling = 25;         // Noise gain scaling - The lower, the stronger the impact of the Noise_Potentiometer.  Default = 1000
int   Noise_Amp;                 // Noise applied gain
int   Noise_PotOffset = 150;
float I_Noise;                   // Noise current
float I_Noise_Gen;

// // // // // // // // // // // // // // // // // // // // // // // //
/*                         Rx Tx parameters                          */
boolean StimFre_Flag = true;  
boolean StimStr_Flag = true; 
boolean StimCus_Flag = true; 
boolean PDGain_Flag = true;
boolean PDDecay_Flag = true;
boolean PDRecovery_Flag = true;
boolean IC_Flag = true;
boolean Noise_Flag = true;
boolean Syn1Gain_Flag = true;
boolean Syn1Decay_Flag = true;
boolean Syn2Gain_Flag = true;
boolean Syn2Decay_Flag = true;
boolean Buzzer_Flag = true;
boolean LED_Flag = true;
boolean SerialFlag = true;
boolean TriggerFlag = false;
boolean SerialTrigger_Flag = false;

String   OutputStr;

void HardwareSettings(){
  Serial.begin(BaudRate);


  pinMode(pinSpike,OUTPUT);

  pinMode(pinLEDVm, OUTPUT);
  pinMode(pinLEDSpike1, OUTPUT);
  pinMode(pinLEDSpike2, OUTPUT);
  
  pinMode(pinSyn1_D,INPUT);

  pinMode(pinSyn2_D,INPUT);

  pinMode(pinAxon_D,OUTPUT);
  pinMode(pinAxon_A,OUTPUT);
  
  pinMode(pinModeButton,INPUT);
  
  pinMode(pinStim_D,OUTPUT);
  pinMode(pinStim_A,OUTPUT);

  
  digitalWrite(pinSpike,LOW);
  digitalWrite(pinAxon_D,LOW);
  digitalWrite(pinAxon_A,LOW);
  digitalWrite(pinStim_D,LOW);
  digitalWrite(pinStim_A,LOW);
  digitalWrite(pinLEDVm,LOW);
  digitalWrite(pinLEDSpike1,LOW);
  digitalWrite(pinLEDSpike2,LOW);

  ADC1.begin(pinADC_Sck, pinADC_MOSI, pinADC_MISO, pinADC_CS1);
  ADC2.begin(pinADC_Sck, pinADC_MOSI, pinADC_MISO, pinADC_CS2);
}

void SerialBlank(){
  Serial.print(0);         Serial.print(',');
  Serial.print(0);         Serial.print(',');
  Serial.print(I_Total);   Serial.print(',');
  Serial.print(0);         Serial.print(',');
  Serial.print(0);         Serial.print(',');
  Serial.print(0);         Serial.print(',');
  Serial.println(0);  

  SerialFlag = true;
}

float mapfloat(long x, long in_min, long in_max, long out_min, long out_max)
{
  return (float)(x - in_min) * (out_max - out_min) / (float)(in_max - in_min) + out_min;
}

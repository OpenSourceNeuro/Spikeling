#include "General_settings.h"
#include "Mode_LEDS.h"
#include <SerialCommand.h>   // SerialCommand Library by Steven Cogswell https://github.com/shyd/Arduino-SerialCommand


SerialCommand SCmd;

void NeuronMode(){
  float aNumber;
  char *arg;
  
  arg = SCmd.next();
  if (arg != NULL){
    aNumber = atof(arg);
    a_Izhikevich = aNumber;
  }
  arg = SCmd.next();
  if (arg != NULL){
    aNumber = atof(arg);
    b_Izhikevich = aNumber;
  }
  arg = SCmd.next();
  if (arg != NULL){
    aNumber = atof(arg);
    c_Izhikevich = aNumber;
  }
  arg = SCmd.next();
  if (arg != NULL){
    aNumber = atof(arg);
    d_Izhikevich = aNumber;
  }
  arg = SCmd.next();
  if (arg != NULL){
    aNumber = atof(arg);
    Mode = aNumber;
    lightOn(Mode);
    if (Mode == 99){
      lightOff();
    }
  }
}


void StimFre_on(){
  StimFre_Flag = false;
  int aNumber;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    aNumber = atoi(arg);
    StimFre= aNumber;
  }
}
void StimFre_off(){
  StimFre_Flag = true;
}


void StimStr_on(){
  StimStr_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    StimStrD = atoi(arg);
    StimStrA = atoi(arg);
  }
}
void StimStr_off(){
  StimStr_Flag = true;
}


void StimCus_on(){
  StimCus_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    StimCus_val = atoi(arg);
  }
}
void StimCus_off(){
  StimCus_Flag = true;
}

void Serial_Trigger(){
  SerialTrigger_Flag = true;
}

void PDGain_on(){
  PDGain_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    PD_Amp = atoi(arg)/10;
  }
}
void PDGain_off(){
  PDGain_Flag = true;
}


void PDDecay_on(){
  PDDecay_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    PD_Decay = atof(arg);
  }
}
void PDDecay_off(){
  PDDecay_Flag = true;
}


void PDRecovery_on(){
  PDRecovery_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    PD_Recovery = atof(arg);
  }
}
void PDRecovery_off(){
  PDRecovery_Flag = true;
}


void IC_on(){
  IC_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    I_IC = atoi(arg);
  }
}
void IC_off(){
  IC_Flag = true;
}


void Noise_on(){
  Noise_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    I_Noise_Gen = atoi(arg);
  }
}
void Noise_off(){
  Noise_Flag = true;
}


void Syn1Gain_on(){
  Syn1Gain_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    Syn1_Amp = atoi(arg)/4;
  }
}
void Syn1Gain_off(){
  Syn1Gain_Flag = true;
}


void Syn1Decay_on(){
  Syn1Decay_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    Synapse1_decay = atof(arg)/1000;
  }
}
void Syn1Decay_off(){
  Syn1Decay_Flag = true;
}


void Syn2Gain_on(){
  Syn2Gain_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    Syn2_Amp = atoi(arg)/4;
  }
}
void Syn2Gain_off(){
  Syn2Gain_Flag = true;
}


void Syn2Decay_on(){
  Syn2Decay_Flag = false;
  char *arg;
  arg = SCmd.next();
  if (arg != NULL){
    Synapse2_decay = atof(arg)/1000;
  }
}
void Syn2Decay_off(){
  Syn2Decay_Flag = true;
}


void Buzzer_on(){
  Buzzer_Flag = true;
}

void Buzzer_off(){
  Buzzer_Flag = false;
  digitalWrite(pinSpike, LOW);
}


void LED_on(){
  LED_Flag = true;
}

void LED_off(){
  LED_Flag = false;
  digitalWrite(pinLEDSpike1,HIGH);
  digitalWrite(pinLEDSpike2,HIGH);
  analogWrite(pinLEDVm,0);
}


void Connected(){
  Mode_opening();
}


void SerialFunctions(){
  SCmd.addCommand("NEU",NeuronMode);
  SCmd.addCommand("FR1",StimFre_on);
  SCmd.addCommand("FR0",StimFre_off);
  SCmd.addCommand("ST1",StimStr_on);
  SCmd.addCommand("ST0",StimStr_off);
  SCmd.addCommand("SC1",StimCus_on);
  SCmd.addCommand("SC0",StimCus_off);
  SCmd.addCommand("TR",Serial_Trigger);
  SCmd.addCommand("PG1",PDGain_on);
  SCmd.addCommand("PG0",PDGain_off);
  SCmd.addCommand("PD1",PDDecay_on);
  SCmd.addCommand("PD0",PDDecay_off);
  SCmd.addCommand("PR1",PDRecovery_on);
  SCmd.addCommand("PR0",PDRecovery_off);
  SCmd.addCommand("IC1",IC_on);
  SCmd.addCommand("IC0",IC_off);
  SCmd.addCommand("NO1",Noise_on);
  SCmd.addCommand("NO0",Noise_off);
  SCmd.addCommand("SG11",Syn1Gain_on);
  SCmd.addCommand("SG10",Syn1Gain_off);
  SCmd.addCommand("SD11",Syn1Decay_on);
  SCmd.addCommand("SD10",Syn1Decay_off);
  SCmd.addCommand("SG12",Syn2Gain_on);
  SCmd.addCommand("SG20",Syn2Gain_off);
  SCmd.addCommand("SD21",Syn2Decay_on);
  SCmd.addCommand("SD20",Syn2Decay_off);
  SCmd.addCommand("BZ1",Buzzer_on);
  SCmd.addCommand("BZ0",Buzzer_off);
  SCmd.addCommand("LED1",LED_on);
  SCmd.addCommand("LED0",LED_off);
  SCmd.addCommand("CON",Connected);
}
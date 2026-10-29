/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "Spikeling_V3.ino"
#include <iostream>
#include <sstream>
#include <string>
int main(){
  setup();
  ADC2.channels[noise.pot_pin]=0;
  Serial.output.clear();
  std::string line;
  while(std::getline(std::cin,line)){
    if(line.empty())continue;
    if(line[0]=='!'){
      Serial.input+=line.substr(1)+"\n";
      SCmd.readSerial();
    }else if(line[0]=='A'){
      unsigned device,ch,value;std::istringstream s(line.substr(1));s>>device>>ch>>value;
      (device==1?ADC1:ADC2).channels[ch]=value;
    }else if(line[0]=='D'){
      unsigned pin,value;std::istringstream s(line.substr(1));s>>pin>>value;host_gpio[pin]=value;
    }else if(line[0]=='R'){
      unsigned count=std::stoul(line.substr(1));
      for(unsigned i=0;i<count;++i){host_us=timing.lastStep_us+timing.step_us;loop();}
    }else if(line[0]=='T'){
      // Advance actual host wall time, including long pauses and uint32 rollover.
      host_us+=static_cast<uint32_t>(std::stoul(line.substr(1)));loop();
    }else if(line[0]=='L'){
      unsigned count=std::stoul(line.substr(1));
      for(unsigned i=0;i<count;++i)loop();
#ifdef VC_PROTOTYPE_TEST
    }else if(line[0]=='K'){
      std::cout<<"CLOCK,"<<host_us<<','<<timing.lastStep_us<<','<<timing.step_us<<','<<voltageClamp.tick<<'\n';
#endif
    }else if(line[0]=='S'){
      std::cout<<"STATE,"<<neuron.v<<','<<neuron.u<<','<<int(clampMode)<<','
               <<host_gpio[pins.gpio.axon_d]<<','<<host_gpio[pins.gpio.spike]<<','
               <<pot.use_patch_pot<<','<<patch.current_clamp<<','<<neuron.selected_model<<'\n';
#ifdef VC_PROTOTYPE_TEST
    }else if(line[0]=='P'){
      if(line.size()>1){
        pharmacology.enabled=std::stoi(line.substr(1))!=0;
        pharmSetDrug(0,100);pharmSeed(123);
      }else std::cout<<"PHARM,"<<pharmacology.enabled<<','<<pharmacology.concentration[0]<<','
                     <<pharmacology.syn[0].rng_state<<','<<pharmacology.syn[1].rng_state<<'\n';
#endif
    }
    for(uint8_t c:Serial.output)std::cout.put(char(c));
    Serial.output.clear();
  }
}

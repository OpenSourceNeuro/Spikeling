/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "VoltageClamp.h"
#include <iomanip>
#include <iostream>
int main(int argc,char** argv){
  if(argc!=10)return 2;
  vc::Cell cell;vc::Parameters p;
  p.capacitance_pF=std::stof(argv[2]);p.membrane_MOhm=std::stof(argv[3]);
  p.access_MOhm=std::stof(argv[4]);p.reversal_mV=std::stof(argv[5]);
  p.minimum_nA=std::stof(argv[6]);p.maximum_nA=std::stof(argv[7]);
  if(!cell.configure(p)||!cell.reset(std::stof(argv[8])))return 3;
  const float dt=std::stof(argv[9]);float cmd;vc::Inputs input;
  std::cout<<std::setprecision(10);
  while(std::cin>>cmd>>input.inward_nA>>input.conductance_uS>>input.conductance_E_nA){
    if(!cell.step(cmd,dt,input,std::stoi(argv[1])?vc::Mode::Ideal:vc::Mode::Access))return 4;
    const auto& x=cell.sample();
    std::cout<<x.voltage_mV<<','<<x.clamp_nA<<','<<x.capacitive_nA<<','<<x.leak_nA<<','<<x.receptor_nA<<','<<x.saturated_fraction<<'\n';
  }
}

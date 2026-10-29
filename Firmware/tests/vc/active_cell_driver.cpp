/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "VoltageClamp.h"
#include <iomanip>
#include <iostream>
int main(int argc,char** argv) {
  if (argc!=8) return 2;
  vc::ActiveCell cell; vc::Parameters p;
  const auto mode = std::stoi(argv[1])?vc::Mode::Ideal:vc::Mode::Access;
  p.access_MOhm=std::stof(argv[2]); p.minimum_nA=std::stof(argv[3]); p.maximum_nA=std::stof(argv[4]);
  const float na=std::stof(argv[5]), k=std::stof(argv[6]), dt=std::stof(argv[7]);
  if (!cell.configure(p) || !cell.reset(-70)) return 3;
  float cmd; vc::Inputs input;
  std::cout<<std::setprecision(10);
  while (std::cin>>cmd>>input.inward_nA>>input.conductance_uS>>input.conductance_E_nA) {
    if (!cell.step(cmd,dt,input,mode,na,k)) return 4;
    const auto& s=cell.sample(); const auto& g=cell.gates();
    std::cout<<s.voltage_mV<<','<<s.clamp_nA<<','<<s.capacitive_nA<<','<<s.leak_nA<<','
             <<s.sodium_nA<<','<<s.potassium_nA<<','<<s.receptor_nA<<','
             <<g.m<<','<<g.h<<','<<g.n<<','<<s.saturated_fraction<<'\n';
  }
}

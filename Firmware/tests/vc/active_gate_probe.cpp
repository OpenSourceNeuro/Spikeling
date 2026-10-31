/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "VoltageClamp.h"
#include <iomanip>
#include <iostream>
#include <string>
static unsigned special_calls = 0;
extern "C" double __real_exp(double);
extern "C" double __real_expm1(double);
extern "C" double __wrap_exp(double x) { ++special_calls; return __real_exp(x); }
extern "C" double __wrap_expm1(double x) { ++special_calls; return __real_expm1(x); }
int main(int argc,char** argv) {
  std::cout<<std::setprecision(12);
  if (argc>1 && std::string(argv[1])=="table") {
    double v;
    while (std::cin>>v) {
      const auto k=vc::FastKinetics::at(v);
      std::cout<<k.infinity.m<<','<<k.infinity.h<<','<<k.infinity.n<<','
               <<k.fraction.m<<','<<k.fraction.h<<','<<k.fraction.n<<'\n';
    }
    return 0;
  }
  const auto mode=argc>1 && std::string(argv[1])=="access" ? vc::Mode::Access : vc::Mode::Ideal;
  const float dt=argc>2 ? std::stof(argv[2]) : .1f;
  float command;
  if (!(std::cin>>command)) return 2;
  vc::ActiveCell cell; cell.reset(-70); vc::Inputs input;
  special_calls=0;
  if (!cell.step(command,dt,input,mode)) return 3;
  std::cout<<special_calls<<'\n';
}

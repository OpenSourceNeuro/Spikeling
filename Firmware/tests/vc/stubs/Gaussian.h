#pragma once
struct Gaussian {
  float mean,variance;
  Gaussian(float m,float v):mean(m),variance(v){}
  float random(){return mean;}
};

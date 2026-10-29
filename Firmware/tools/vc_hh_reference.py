#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Independent HH reference: exact constant-voltage gates/product integrals,
and SciPy DOP853 for a cell behind a finite, current-limited access resistance.
Units mV, ms, nA, pF, MOhm, uS. Kinetics: NEURON hh.mod, 6.3 C.
"""
import math

DT = .1
GNA, GK, ENA, EK = .240, .072, 50., -77.
DEFAULT = dict(cm=20., rm=500., rs=5., el=-70., minimum=-20., maximum=20.)


def rates(v):
    def quotient(x):
        return 1-x/2+x*x/12 if abs(x) < 1e-6 else x/math.expm1(x)
    am, bm = quotient(-(v+40)/10), 4*math.exp(-(v+65)/18)
    ah, bh = .07*math.exp(-(v+65)/20), 1/(1+math.exp(-(v+35)/10))
    an, bn = .1*quotient(-(v+55)/10), .125*math.exp(-(v+65)/80)
    return [(a/(a+b), a+b) for a,b in ((am,bm),(ah,bh),(an,bn))]


def initial(v=-70.):
    return [v, *[target for target,rate in rates(v)]]


def exponential_mean(rate, dt):
    return -math.expm1(-rate*dt)/(rate*dt) if rate else 1.


def advance(state, command, inward=0., g=0., ge=0., ideal=True,
            sodium=1., potassium=1., parameters=None, dt=DT):
    p = DEFAULT if parameters is None else parameters
    v0,m,h,n = state
    cm = p['cm']/1000
    if ideal:
        (mi,mr),(hi,hr),(ni,nr) = rates(command)
        # Integrate the polynomial products of exponential gate solutions;
        # this does not reproduce the firmware's split-step algorithm.
        mean_na = sum(math.comb(3,a)*mi**(3-a)*(m-mi)**a *
                      math.comb(1,b)*hi**(1-b)*(h-hi)**b *
                      exponential_mean(a*mr+b*hr,dt)
                      for a in range(4) for b in range(2))
        mean_k = sum(math.comb(4,a)*ni**(4-a)*(n-ni)**a *
                     exponential_mean(a*nr,dt) for a in range(5))
        na = sodium*GNA*mean_na*(command-ENA)
        k = potassium*GK*mean_k*(command-EK)
        leak = (command-p['el'])/p['rm']
        receptor = g*command-ge
        cap = cm*(command-v0)/dt
        new = [command, mi+(m-mi)*math.exp(-mr*dt),
               hi+(h-hi)*math.exp(-hr*dt), ni+(n-ni)*math.exp(-nr*dt)]
        return new, dict(voltage_mV=command, clamp_nA=cap+na+k+leak+receptor-inward,
                         capacitive_nA=cap, leak_nA=leak, sodium_nA=na,
                         potassium_nA=k, receptor_nA=receptor)
    from scipy.integrate import solve_ivp

    def derivative(t,y):
        v,m,h,n = y[:4]
        na = sodium*GNA*m**3*h*(v-ENA)
        k = potassium*GK*n**4*(v-EK)
        leak = (v-p['el'])/p['rm']
        receptor = g*v-ge
        clamp = max(p['minimum'],min(p['maximum'],(command-v)/p['rs']))
        dg = [rate*(target-value) for (target,rate),value in zip(rates(v),(m,h,n))]
        return [(clamp+inward-na-k-leak-receptor)/cm,*dg,clamp,leak,na,k,receptor]

    sol = solve_ivp(derivative,(0,dt),[*state,0,0,0,0,0],method='DOP853',rtol=1e-9,atol=1e-11)
    if not sol.success:
        raise ValueError(sol.message)
    y = sol.y[:,-1]
    return list(y[:4]), dict(voltage_mV=y[0],clamp_nA=y[4]/dt,
      capacitive_nA=cm*(y[0]-v0)/dt,leak_nA=y[5]/dt,sodium_nA=y[6]/dt,
      potassium_nA=y[7]/dt,receptor_nA=y[8]/dt)

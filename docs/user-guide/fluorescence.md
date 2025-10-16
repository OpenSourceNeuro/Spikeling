
## Fluorescence Imaging simulation

<br>

TBC

```math
[Ca^{2+}]_{t} = [Ca^{2+}]_{t-1} - \tau . [Ca^{2+}]_{t-1} + [Ca^{2+}]_{b} + A . n_{t} + \sigma_{Ca} . \sqrt{\Delta} . \varepsilon_{Ca,t}
```

Where:
- $\tau$ is the Calcium decay constant
- $[Ca^{2+}]_{b}$ the Calcium baseline concentration
- A is the calcium concentration jump each spike triggers
- $n_{t}$ is the number of spikes at time t
- $\sigma_{Ca}$ scales the Calcium noise
- $\Delta$ represents the imaging frame timeline
- $\varepsilon_{Ca,t}$ is a standard normal Gaussian noise source

<br>

```math
F_{t} = \alpha[Ca^{2+}]_{t} + \beta + \sigma_{F}.\varepsilon_{F,t}
```

<br>

<div>
<p align="center">
<img align="center"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/201_graph.png" width="400" height="250">

</div>

<br>

Where:
- $\alpha$ scales the Fluorescence
- $\beta$ offsets the fluorescence
- $\sigma_{F}$ scales the Fluorescence noise
- $\varepsilon_{F,t}$ is a standard normal Gaussian noise source


<br></br>

```math
Fsat_{t} = \alpha.S.[Ca^{2+}]_{t} + \beta + \eta_{t}

```

Where:
- The gain $\alpha$ scales the fluorescence. It accounts for all factors contributing to signal amplification, including
the number of fluorophores in the neuron, the brightness of each fluorophore, the gain of the image acquisition system, etc.
- The offset $\beta$, accounts for any factor leading to a constant background signal, such as baseline fluorescence.
- $S . [Ca^{2+}]_{t}$ is a nonlinear saturation function, often taken as the Hill equation:
  - $S_{x} = \frac{x_{n}} {(x_{n} + kd)}$, where n is the Hill coefficient and kd the dissociation constant.
- Assuming the primary noise source is photon shot noise, it would be appropriate to model noise as a Poisson process,
which could be well approximated by a Gaussian distribution for large photon counts: $\eta_{t}$

```math
\eta_{t} = \sqrt{\varepsilon.S . ([Ca^{2+}]_{t}) + \sigma_{F}} . \varepsilon_{F,t}
```

<br>


<div>

<p align="center">
<img align="center"  src="https://github.com/OpenSourceNeuro/Spikeling-V2/blob/main/Images/201_graphsat.png" width="400" height="250">

</div>

<br>

***

<br>

## Fluorescence Imaging parameters

<br>

TBC

<br>

***

<br>

## Fluorescence Calcium parameters

<br>

TBC

<br>

***

<br>

## Fluorescence Imaging parameters

<br>

TBC

<br>

***

<br>

## Fluorescence Data Analysis

<br>

TBC

<br>

***

<br>

## Fluorescence Multiple fluorescence

<br>

TBC

<br>

***

<br>

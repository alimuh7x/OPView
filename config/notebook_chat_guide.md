# OPView Calculation Notebook — AI Assistant Guide

This guide defines the rules the AI must follow when helping users write
notebook code in OPView. Read it carefully before suggesting any code.

---

## Absolute Rules

- **No imports.** Never write `import numpy`, `import scipy`, `import math`,
  or any other import statement. The notebook does not support imports.
- **No numpy/scipy calls.** Never use `np.`, `scipy.`, `math.`, `cmath.` prefixes.
  All functions are available directly by name (e.g. `sin`, `exp`, `linspace`).
- **One expression or assignment per line.** The notebook evaluates line-by-line.
- **Use `^` for power**, not `**`. Example: `x^2` not `x**2`.
- **No class or def statements.** Function definitions are not supported.
- **No print().** Results are shown automatically.
- **Variables carry forward** between lines. Assign once, use in later lines.
- Use `plot(x, y)` to plot. The notebook handles display automatically.

---

## Syntax Quick Reference

```
# Scalars
x = 5
y = 2.5 * x + 1

# Power — always use ^
area = pi * r^2
E_act = R_gas * T * log(k)

# Arrays
t = linspace(0, 10, 200)
y = exp(-0.3 * t) * cos(2 * pi * t)

# Conditional selection
y_pos = where(y > 0, y, 0)

# Plot
plot(t, y)
```

---

## Available Functions

### Math (scalar and array)
| Function | Description |
|----------|-------------|
| `abs(x)` | Absolute value |
| `sqrt(x)` | Square root |
| `exp(x)` | e^x |
| `log(x)` | Natural log |
| `log10(x)` | Base-10 log |
| `log2(x)` | Base-2 log |
| `sin(x)`, `cos(x)`, `tan(x)` | Trig (radians) |
| `asin(x)`, `acos(x)`, `atan(x)` | Inverse trig |
| `atan2(y, x)` | Four-quadrant arctangent |
| `sinh(x)`, `cosh(x)`, `tanh(x)` | Hyperbolic |
| `floor(x)`, `ceil(x)`, `round(x)` | Rounding |
| `sign(x)` | Sign of x (-1, 0, 1) |
| `degrees(x)`, `radians(x)` | Angle conversion |
| `clamp(x, lo, hi)` | Clamp value to range |
| `lerp(a, b, t)` | Linear interpolation |
| `factorial(n)` | n! |
| `gcd(a, b)`, `lcm(a, b)` | GCD / LCM |
| `erf(x)`, `erfc(x)` | Error function |
| `gamma(x)`, `lgamma(x)` | Gamma / log-gamma |
| `beta(a, b)` | Beta function |
| `hypot(x, y)` | √(x²+y²) |

### Array Builders
| Function | Description |
|----------|-------------|
| `linspace(start, stop, n)` | n evenly spaced points |
| `arange(start, stop, step)` | Range with step |
| `zeros(n)` / `zeros(m, n)` | Zero vector / matrix |
| `ones(n)` / `ones(m, n)` | Ones vector / matrix |
| `eye(n)` | Identity matrix |
| `full(n, val)` | Array filled with val |
| `diag(v)` | Diagonal matrix from vector |

### Array Operations
| Function | Description |
|----------|-------------|
| `where(cond, x, y)` | Element-wise conditional |
| `clip(v, lo, hi)` | Clamp array values |
| `sort(v)` | Sort ascending |
| `flip(v)` | Reverse array |
| `unique(v)` | Unique values |
| `argsort(v)` | Sort indices |
| `concat(a, b, ...)` | Concatenate arrays |
| `append(a, b)` | Append b to a |
| `reshape(v, m, n)` | Reshape array |
| `flatten(M)` | Flatten to 1-D |
| `roll(v, shift)` | Circular shift |
| `repeat(v, n)` | Repeat elements |
| `tile(v, n)` | Tile array |
| `vstack(a, b)` / `hstack(a, b)` | Stack arrays |
| `meshgrid(x, y)` | 2-D grid from 1-D arrays |
| `shape(M)` | Array shape as list |
| `len(v)` | Length of array |

### Statistics
| Function | Description |
|----------|-------------|
| `sum(v)` | Sum |
| `mean(v)` | Arithmetic mean |
| `std(v)` | Standard deviation |
| `variance(v)` | Variance |
| `median(v)` | Median |
| `min(v)`, `max(v)` | Min / max |
| `prod(v)` | Product of elements |
| `cumsum(v)` | Cumulative sum |
| `diff(v)` | First differences |
| `diff2(v, n)` | n-th differences |
| `percentile(v, p)` | Percentile (0–100) |
| `quantile(v, q)` | Quantile (0–1) |
| `corrcoef(x, y)` | Pearson correlation |
| `cov(x, y)` | Covariance |
| `mode(v)` | Most frequent value |
| `zscore(v)` | Z-score normalisation |
| `norm01(v)` | Min-max normalisation to [0,1] |
| `histogram(v, bins)` | Bin counts |

### Interpolation & Fitting
| Function | Description |
|----------|-------------|
| `interp(x, xp, fp)` | Linear interpolation |
| `polyfit(x, y, deg)` | Polynomial fit coefficients |
| `polyval(p, x)` | Evaluate polynomial |

### Calculus & Signal
| Function | Description |
|----------|-------------|
| `gradient(f, dx)` | Numerical gradient |
| `trapz(y, x)` | Trapezoidal integration |
| `cumtrapz(y, dx)` | Cumulative trapezoidal integral |
| `fft(v)` | FFT magnitudes |
| `ifft(v)` | Inverse FFT |
| `fftfreq(n, dt)` | FFT frequency axis |
| `fftshift(v)` | Shift zero-frequency to centre |
| `real(v)`, `imag(v)`, `angle(v)` | Complex parts |

### Linear Algebra
| Function | Description |
|----------|-------------|
| `solve(A, b)` | Solve A·x = b |
| `lstsq(A, b)` | Least-squares solution |
| `inv(M)` | Matrix inverse |
| `det(M)` | Determinant |
| `trace(M)` | Trace |
| `rank(M)` | Rank |
| `eig(M)` | Eigenvalues |
| `svd(M)` | Singular values |
| `norm(v)` | Euclidean norm |
| `norm_p(v, p)` | p-norm |
| `dot(a, b)` | Dot product |
| `cross(a, b)` | Cross product |
| `normalize(v)` | Unit vector |
| `transpose(M)` | Transpose |
| `outer(a, b)` | Outer product |
| `kron(A, B)` | Kronecker product |
| `pinv(M)` | Pseudo-inverse |
| `cond(M)` | Condition number |
| `cholesky(M)` | Cholesky factor |
| `qr(M)` | QR decomposition (returns [Q, R]) |
| `matrix_power(M, n)` | M^n |
| `diag(v)` | Diagonal matrix |

### Solid Mechanics
| Function | Description |
|----------|-------------|
| `von_mises(s11, s22, s33, s12, s23, s13)` | Von Mises stress |
| `shear_modulus(E, nu)` | G = E / (2(1+ν)) |
| `lame_lambda(E, nu)` | First Lamé parameter |
| `hooke_1d(E, eps)` | σ = E·ε |
| `hooke_3d(E, nu, exx, eyy, ezz, ...)` | Full 3-D stress vector |
| `plane_strain(E, nu, exx, eyy, exy)` | Plane-strain [sxx, syy, txy] |
| `plane_stress(E, nu, exx, eyy, exy)` | Plane-stress [sxx, syy, txy] |
| `plane_stress_ezz(nu, exx, eyy)` | Out-of-plane strain |

### Fluid / Heat / Numerics
| Function | Description |
|----------|-------------|
| `reynolds(rho, u, L, mu)` | Reynolds number |
| `mach(u, a)` | Mach number |
| `prandtl(mu, cp, k)` | Prandtl number |
| `nusselt_dittus(Re, Pr)` | Dittus-Boelter Nusselt |
| `biot(h, L, k)` | Biot number |
| `fourier_thermal(alpha, t, L)` | Fourier number |
| `lewis(D, alpha)` | Lewis number |
| `weber(rho, v, L, sigma)` | Weber number |
| `grashof(g, beta, dT, L, nu)` | Grashof number |
| `cfl_dt(dx, u, cfl)` | CFL time-step |
| `diffusion_dt(dx, D, f)` | Explicit diffusion Δt |
| `fourier_number(D, dt, dx)` | Fourier number |
| `peclet(u, L, D)` | Péclet number |
| `cell_size(L, N)` | Grid cell size |
| `domain_points(L, dx)` | Number of grid points |

### Alloy Composition
| Function | Description |
|----------|-------------|
| `wt_to_mol(wt, M)` | Weight fractions → mole fractions |
| `mol_to_wt(x, M)` | Mole fractions → weight percent |
| `wt_to_mol2(wt_B, M_A, M_B)` | Binary alloy wt% B → x_B (array-safe) |

### Control Flow
```
for i in range(n):          # up to 100 000 iterations
    x[i] = ...

for i, val in enumerate(v):
    ...

for a, b in zip(u, v):
    ...
```

---

## Built-in Constants

| Name | Value | Description |
|------|-------|-------------|
| `pi` | 3.14159… | π |
| `e` | 2.71828… | Euler's number |
| `R_gas` | 8.3145 | Gas constant J/(mol·K) |
| `k_B` | 1.381×10⁻²³ | Boltzmann constant J/K |
| `N_A` | 6.022×10²³ | Avogadro number |
| `h_p` | 6.626×10⁻³⁴ | Planck constant J·s |
| `c_0` | 2.998×10⁸ | Speed of light m/s |
| `g_n` | 9.80665 | Standard gravity m/s² |
| `sigma_SB` | 5.670×10⁻⁸ | Stefan-Boltzmann W/(m²K⁴) |
| `atm` | 101325 | Standard atmosphere Pa |

### Unit Multipliers (use as conversion factors)
`nm`, `um`, `mm`, `cm`, `m`, `km` — length
`Pa`, `kPa`, `MPa`, `GPa`, `bar` — pressure
`ms`, `sec`, `min`, `h`, `day`, `week` — time
`J`, `kJ`, `MJ`, `kWh` — energy
`W`, `kW`, `MW` — power
`N`, `kN`, `MN` — force
`Hz`, `kHz`, `MHz` — frequency

---

## Good Code Examples

### Arrhenius scan
```
T_scan = linspace(300, 1200, 500)
Q = 150e3
k0 = 1e12
k_scan = k0 * exp(-Q / (R_gas * T_scan))
plot(T_scan, k_scan)
```

### Avrami kinetics
```
t = linspace(0.1, 100, 300)
n = 2.5
k = 0.01
f = 1 - exp(-k * t^n)
avrami_y = log(-log(1 - f))
ln_t = log(t)
plot(ln_t, avrami_y)
```

### Binary alloy composition
```
wt_B = linspace(0, 100, 200)
x_B = wt_to_mol2(wt_B, 55.845, 58.693)
plot(wt_B, x_B)
```

### Solve linear system
```
A = [[2, 1], [1, 3]]
b = [5, 10]
x = solve(A, b)
```

### FFT
```
t = linspace(0, 1, 1024)
signal = sin(2 * pi * 5 * t) + 0.5 * sin(2 * pi * 13 * t)
freq = fftfreq(len(t), t[1] - t[0])
spectrum = fft(signal)
plot(freq[:512], spectrum[:512])
```

---

## What NOT to Write

```python
# WRONG — no imports
import numpy as np
x = np.linspace(0, 10, 100)

# WRONG — no np. prefix
y = np.exp(-x)

# WRONG — ** for power
z = x**2

# WRONG — print statements
print(x)

# WRONG — def / class
def my_func(x):
    return x^2
```

```
# CORRECT
x = linspace(0, 10, 100)
y = exp(-x)
z = x^2
```

"""
Calculation notebook UI for OPView.
"""

from __future__ import annotations

from dash import dcc, html
import plotly.graph_objects as go

# Download component id used by save/load callbacks
NOTEBOOK_DOWNLOAD_ID = "notebook-download"


NOTEBOOK_ROWS = 28
NOTEBOOK_LINE_HEIGHT = "34px"
RESULTS_GUTTER_WIDTH = "220px"
FUNCTIONS_CARD_WIDTH = "360px"
NOTEBOOK_SHEET_WIDTH = "1280px"

NOTEBOOK_HELP = [
    {
        "title": "Trig",
        "items": ["sin(x)", "cos(x)", "tan(x)", "asin(x)", "acos(x)", "atan(x)", "atan2(y,x)", "sinh(x)", "cosh(x)", "tanh(x)"],
        "note": "Angles are in radians.",
    },
    {
        "title": "Math",
        "items": ["abs(x)", "sqrt(x)", "exp(x)", "log(x)", "log10(x)", "log2(x)", "hypot(x,y)", "floor(x)", "ceil(x)", "round(x)", "sign(x)", "degrees(x)", "radians(x)"],
    },
    {
        "title": "Number",
        "items": ["clamp(x,lo,hi)", "lerp(a,b,t)", "factorial(n)", "gcd(a,b)", "lcm(a,b)"],
    },
    {
        "title": "Stats",
        "items": ["sum(v)", "mean(v)", "std(v)", "variance(v)", "median(v)", "prod(v)", "cumsum(v)", "diff(v)"],
        "note": "v is a vector like [1, 2, 3].",
    },
    {
        "title": "Arrays",
        "items": ["linspace(a,b,n)", "arange(a,b,step)", "diag(v)", "flatten(M)", "outer(a,b)"],
    },
    {
        "title": "Engineering",
        "items": [
            "cfl_dt(dx,u,cfl=1)",
            "diffusion_dt(dx,D,f=0.5)",
            "fourier_number(D,dt,dx)",
            "peclet(u,L,D)",
            "cell_size(L,N)",
            "domain_points(L,dx)",
            "von_mises(s11,s22,s33,s12=0,s23=0,s13=0)",
        ],
        "note": "For plane stress use von_mises(sxx, syy, 0, txy, 0, 0).",
    },
    {
        "title": "Constitutive",
        "items": [
            "shear_modulus(E,nu)",
            "lame_lambda(E,nu)",
            "hooke_1d(E,eps)",
            "hooke_3d(E,nu,exx,eyy,ezz,exy=0,eyz=0,exz=0)",
            "plane_strain(E,nu,exx,eyy,exy=0)",
            "plane_stress(E,nu,exx,eyy,exy=0)",
            "plane_stress_ezz(nu,exx,eyy)",
        ],
        "note": "Stress-state functions return compact objects like {sxx: ..., syy: ..., txy: ...}.",
    },
    {
        "title": "Vectors",
        "items": ["dot(a,b)", "cross(a,b)", "norm(v)", "normalize(v)", "length(v)"],
        "note": "Use vector syntax like v = [1, 2, 3].",
    },
    {
        "title": "Matrices",
        "items": ["A @ B", "det(M)", "inv(M)", "transpose(M)", "trace(M)", "rank(M)", "eig(M)", "solve(A,b)", "lstsq(A,b)", "svd(M)", "norm_p(v,p)"],
        "note": "Use matrix syntax like A = [[1, 2], [3, 4]]. solve(A,b): linear system Ax=b.",
    },
    {
        "title": "Builders",
        "items": ["eye(n)", "zeros(m,n)", "ones(m,n)", "shape(M)"],
    },
    {
        "title": "Consts",
        "items": ["pi", "e", "tau", "deg", "inf"],
        "note": "tau=2*pi. deg=pi/180 (e.g. 45*deg).",
    },
    {
        "title": "Units",
        "items": ["nm", "um", "us", "mm", "cm", "m", "km", "ms", "sec", "min", "h", "hour", "day", "week", "month", "Pa", "kPa", "MPa", "GPa", "kg", "N", "kN", "MN", "J", "kJ", "MJ", "W", "kW", "MW", "Hz", "kHz", "MHz"],
        "note": "Examples: 10*mm, 210*GPa, 5*min, 1.5*kN",
    },
    {
        "title": "Dimless",
        "items": ["reynolds(rho,u,L,mu)", "mach(u,a)", "prandtl(mu,cp,k)", "nusselt_dittus(Re,Pr)",
                  "biot(h,L,k)", "fourier_thermal(alpha,t,L)", "lewis(alpha,D)",
                  "weber(rho,u,L,sig)", "stokes(rho_p,rho_f,d,mu)", "grashof(g,beta,dT,L,nu)"],
        "note": "Dimensionless numbers for fluid/heat transfer.",
    },
    {
        "title": "Special",
        "items": ["erf(x)", "erfc(x)", "gamma(x)", "lgamma(x)", "beta(a,b)"],
        "note": "Special functions (error, gamma, beta).",
    },
    {
        "title": "Signal",
        "items": ["fft(v)", "ifft(v)", "fftfreq(n,dt)", "fftshift(v)", "real(v)", "imag(v)", "angle(v)"],
        "note": "FFT of real array returns magnitudes. fftfreq gives frequency axis.",
    },
    {
        "title": "Interp",
        "items": ["interp(x,xp,fp)", "polyfit(x,y,deg)", "polyval(p,x)", "gradient(v,dx)", "trapz(y,x)", "cumtrapz(y,x)"],
        "note": "interp: piecewise linear. polyfit returns coefficients, polyval evaluates them.",
    },
    {
        "title": "ArrayOps",
        "items": ["sort(v)", "argsort(v)", "unique(v)", "flip(v)", "clip(v,lo,hi)", "roll(v,n)",
                  "repeat(v,n)", "tile(v,n)", "full(n,val)", "where(cond,x,y)", "concat(a,b)",
                  "reshape(v,r,c)", "append(v,x)"],
        "note": "where(cond,x,y): elementwise conditional. concat/append join arrays.",
    },
    {
        "title": "MoreStats",
        "items": ["percentile(v,p)", "quantile(v,q)", "corrcoef(x,y)", "zscore(v)", "norm01(v)"],
        "note": "percentile(v,50) = median. norm01 scales to [0,1]. zscore standardises.",
    },
    {
        "title": "PhysConst",
        "items": ["g_n", "c_0", "R_gas", "k_B", "N_A", "h_p", "sigma_SB"],
        "note": "g_n=9.80665, c_0=2.998e8, R_gas=8.314, k_B=1.381e-23, N_A=6.022e23, h_p=6.626e-34, σ=5.67e-8",
    },
    {
        "title": "MoreLinalg",
        "items": ["pinv(M)", "cond(M)", "matrix_power(M,n)", "kron(A,B)", "cholesky(A)", "qr(A)", "eig_full(M)"],
        "note": "cholesky returns lower-triangular L. qr returns [Q, R]. eig_full returns [vals, vecs].",
    },
    {
        "title": "Alloy",
        "items": ["wt_to_mol(wt,M)", "mol_to_wt(x,M)", "wt_to_mol2(wt_B,M_A,M_B)"],
        "note": "wt_to_mol2: binary scan — wt_B can be an array (e.g. linspace). wt_to_mol/mol_to_wt: multi-component, sum=1 / sum=100.",
    },
    {
        "title": "Comments",
        "items": ["# comment", "// comment"],
        "note": "Inline comments are ignored during evaluation.",
    },
]

GRID_HELP_TITLES = {
    "Trig", "Math", "Number", "Vectors", "Matrices", "Builders",
    "Consts", "Units", "Special", "MoreStats", "PhysConst", "Alloy",
}

NOTEBOOK_EXAMPLES = [
    "v = [1, 2, 3]",
    "A = [[1, 2], [3, 4]]",
    "dot(v, [4, 5, 6])",
    "A @ [[5, 6], [7, 8]]",
    "vm = von_mises(200*MPa, 120*MPa, 0, 40*MPa, 0, 0)",
    "ps = plane_stress(210*GPa, 0.3, 1e-3, 0, 0)",
    "mean([1, 4, 9, 16, 25])",
    "linspace(0, 1, 5)",
    "solve([[2,1],[1,3]], [5,10])",
    "reynolds(1000, 0.5, 0.01, 1e-3)",
]


# ── Snippet examples (multi-line, loaded via dropdown) ────────────────────────

# Ordering of snippet groups shown in the dropdown
NOTEBOOK_SNIPPET_GROUPS: dict[str, list[str]] = {
    "Getting Started": ["Quick Start"],
    "Math & Statistics": ["Statistics Summary", "Fibonacci Sequence", "FFT of Sine Wave"],
    "Thermodynamics & Heat Transfer": ["Newton's Law of Cooling", "1D Heat Diffusion", "Dimensionless Numbers", "Arrhenius & Diffusion", "Avrami (JMAK) Kinetics"],
    "Mechanics": [
        "Spring-Mass Oscillator",
        "Mohr's Circle (2D Stress)",
        "2D Yield Surface (VM & Tresca)",
        "Hydrostatic & Deviatoric Stress",
        "Isotropic Hardening",
        "Von Mises Stress",
        "Fracture Mechanics (LEFM)",
        "Fatigue — S-N & Paris Law",
    ],
    "Structural & Materials": ["Lever Rule (Binary)", "Rule of Mixtures (Composite)", "Eigenvalues & Linear Solve", "Wt% ↔ Mole Fraction"],
    "Crystal & Anisotropy": ["Elastic Anisotropy (Cubic)", "FCC Slip Systems & RSS"],
}

NOTEBOOK_SNIPPETS: dict[str, str] = {
    "Quick Start": """\
# Welcome to the Calculation Notebook!
# One expression per line — results appear on the right.

# ── Basic arithmetic ──────────────────────────────────────
x = 10
y = 3.5
z = x^2 + y            // ^ is power;  result appears right →

# ── Built-in units ────────────────────────────────────────
F = 5 * kN             // 5 kilonewtons (stored in Newtons)
E_steel = 210 * GPa    // Young's modulus in Pascals

# ── Functions ─────────────────────────────────────────────
angle = 45 * deg       // 45° converted to radians
s = sin(angle)         // sine of 45° ≈ 0.707

# ── Vectors & statistics ──────────────────────────────────
data = [1, 4, 9, 16, 25]
avg = mean(data)
total = sum(data)

# ── Arrays for plotting ───────────────────────────────────
t = linspace(0, 2*pi, 200)
y_wave = sin(t)
// After running: in the plot panel on the right →
//   set X = t,  Y = y_wave,  Type = Lines
""",
    "Newton's Law of Cooling": """\
# Newton's law of cooling
# T(t) = T_env + (T0 - T_env) * exp(-k * t)
T0 = 90.0        // initial temperature [°C]
T_env = 22.0     // ambient temperature [°C]
k_cool = 0.03    // cooling constant [1/s]
dt = 1.0         // time step [s]
n_steps = 300
T_arr = zeros(n_steps)
t_arr = linspace(0, (n_steps - 1) * dt, n_steps)
T_arr[0] = T0
for i in range(1, n_steps):
    T_arr[i] = T_arr[i-1] + dt * (-k_cool * (T_arr[i-1] - T_env))
// Side plot: X=t_arr, Y=T_arr, Type=lines
T_arr
""",
    "1D Heat Diffusion": """\
# 1D explicit finite-difference heat diffusion
# u_t = D * u_xx  (Dirichlet BCs: u=1 left, u=0 right)
nx = 80          // grid points
D = 0.01         // thermal diffusivity
dx = 1.0 / nx
dt = diffusion_dt(dx, D)    // stable time step
n_steps = 500
u = zeros(nx)
for i in range(nx):
    u[i] = 1.0 if i == 0 else 0.0
for t in range(n_steps):
    u_new = zeros(nx)
    u_new[0] = 1.0           // left BC
    for i in range(1, nx - 1):
        u_new[i] = u[i] + D * dt / dx^2 * (u[i+1] - 2*u[i] + u[i-1])
    u = u_new
x_arr = linspace(0, 1, nx)
// Side plot: X=x_arr, Y=u, Type=lines
u
""",
    "Fibonacci Sequence": """\
# Fibonacci sequence
n_fib = 20
fib = zeros(n_fib)
fib[0] = 1
fib[1] = 1
for i in range(2, n_fib):
    fib[i] = fib[i-1] + fib[i-2]
fib
""",
    "FFT of Sine Wave": """\
# FFT spectrum of a multi-tone sine signal
nx = 256
dt_sig = 1.0 / nx
x_arr = linspace(0, 1, nx)
y_arr = sin(2 * pi * 5 * x_arr) + 0.5 * sin(2 * pi * 12 * x_arr)
freqs = fftfreq(nx, dt_sig)
magnitudes = fft(y_arr)
// Select freqs as X and magnitudes as Y in the side plot
x_arr
y_arr
""",
    "Statistics Summary": """\
# Statistical analysis of a dataset
data = [23.1, 25.4, 22.8, 26.7, 24.3, 21.9, 27.1, 25.8, 23.6, 24.9]
n_data = len(data)
avg = mean(data)
std_dev = std(data)
med = median(data)
p25 = percentile(data, 25)
p75 = percentile(data, 75)
cv = std_dev / avg * 100    // coefficient of variation [%]
""",
    "Hydrostatic & Deviatoric Stress": """\
# Hydrostatic and Deviatoric Stress Decomposition
# σ = σ_h·I + s   (volumetric + shape-change parts)

# ── Input: 3×3 stress tensor [MPa] ───────────────────────────────────
sigma_mat = eye(3) @ [[120, 30, -15], [30, -40, 20], [-15, 20, 80]]

# ── Hydrostatic stress (mean normal stress) ───────────────────────────
I1 = trace(sigma_mat)          // 1st invariant = σ₁₁+σ₂₂+σ₃₃
sigma_h = I1 / 3               // hydrostatic stress [MPa]
pressure = -sigma_h            // pressure (positive in compression)

# ── Deviatoric stress tensor  s = σ − σ_h·I ──────────────────────────
s_dev = sigma_mat - sigma_h * eye(3)
tr_check = trace(s_dev)        // must be ≈ 0

# ── Deviatoric invariants J₂ and J₃ ──────────────────────────────────
s11 = s_dev[0][0]
s22 = s_dev[1][1]
s33 = s_dev[2][2]
s12 = s_dev[0][1]
s23 = s_dev[1][2]
s13 = s_dev[0][2]
J2 = 0.5 * (s11^2 + s22^2 + s33^2 + 2*(s12^2 + s23^2 + s13^2))
J3 = det(s_dev)

# ── Von Mises equivalent stress  σ_vm = √(3·J₂) ──────────────────────
sigma_vm = sqrt(3 * J2)

# ── Principal stresses (eigenvalues of σ) ─────────────────────────────
principals = eig(sigma_mat)    // returns [σ₁, σ₂, σ₃]
sigma1_p = max(principals)     // max principal [MPa]
sigma3_p = min(principals)     // min principal [MPa]

# ── Stress triaxiality  η = σ_h / σ_vm ───────────────────────────────
// η > 0: triaxial tension (void growth), η < 0: compression
triaxiality = sigma_h / sigma_vm

# ── Lode angle θ  (-30° ≤ θ ≤ 30°) ──────────────────────────────────
// θ = +30° uniaxial tension, 0° pure shear, -30° uniaxial compression
cos_3t = 3*sqrt(3)/2 * J3 / J2^1.5
lode_deg = degrees(acos(clamp(cos_3t, -1.0, 1.0)) / 3)

sigma_h
sigma_vm
triaxiality
lode_deg
""",
    "Isotropic Hardening": """\
# Isotropic Hardening — Uniaxial Stress-Strain Response
# Yield surface expands uniformly (no Bauschinger effect)
# Three laws compared: Linear, Swift (power), Voce (saturation)

# ── Material parameters ───────────────────────────────────
E_h = 210000.0    // Young's modulus [MPa]
sig_y0 = 250.0    // initial yield stress [MPa]

# ── Linear hardening: σ = σ_y0 + H·εₚ ───────────────────
H_lin = 5000.0    // plastic hardening modulus [MPa]
// Tangent modulus relates to H: E_t = E*H/(E+H)
E_tan = E_h * H_lin / (E_h + H_lin)

# ── Swift power law: σ = K·(ε₀+εₚ)ⁿ ────────────────────
K_sw = 500.0      // strength coefficient [MPa]
n_sw = 0.25       // strain hardening exponent (0.1-0.5 for metals)
// ε₀ chosen so Swift matches σ_y0 at εₚ=0
eps0 = (sig_y0 / K_sw)^(1.0 / n_sw)

# ── Voce saturation law: σ = σ_sat-(σ_sat-σ_y0)·exp(-b·εₚ)
sig_sat = 450.0   // saturation (ultimate) flow stress [MPa]
b_v = 20.0        // saturation rate constant

# ── Arrays over plastic strain [0 … 30%] ─────────────────
n_pts = 200
eps_p = linspace(0, 0.30, n_pts)

sig_lin   = sig_y0 + H_lin * eps_p
sig_swift = K_sw * (eps0 + eps_p)^n_sw
sig_voce  = sig_sat - (sig_sat - sig_y0) * exp(-b_v * eps_p)

// Total strain ε = εₑ + εₚ = σ/E + εₚ
eps_lin   = sig_lin   / E_h + eps_p
eps_swift = sig_swift / E_h + eps_p
eps_voce  = sig_voce  / E_h + eps_p

// Side plot: X=eps_lin, Y=sig_lin  (or swift/voce), Type=Lines
// Switch X/Y to compare all three curves on the same plot

# ── Scalar check at εₚ = 10% ─────────────────────────────
ep_ref = 0.10
sl_ref = sig_y0 + H_lin * ep_ref
ss_ref = K_sw * (eps0 + ep_ref)^n_sw
sv_ref = sig_sat - (sig_sat - sig_y0) * exp(-b_v * ep_ref)
sl_ref
ss_ref
sv_ref
""",
    "Von Mises Stress": """\
# Plane-stress Von Mises criterion — steel under biaxial load
E_mod = 210*GPa      // Young's modulus
nu_s = 0.3           // Poisson ratio
exx = 0.001          // axial strain
eyy = -nu_s * exx    // transverse strain (Poisson effect)
stress = plane_stress(E_mod, nu_s, exx, eyy)
sxx = stress[0]
syy = stress[1]
txy = stress[2]
vm = von_mises(sxx, syy, 0, txy, 0, 0)
vm
""",
    "Eigenvalues & Linear Solve": """\
# Matrix eigenvalues and linear system solve
A = [[4, 2, 0], [2, 3, 1], [0, 1, 2]]
b_vec = [10, 14, 7]
eigenvalues = eig(A)
x_sol = solve(A, b_vec)
det_A = det(A)
cond_A = cond(A)
""",
    "Wt% ↔ Mole Fraction": """\
# Wt% ↔ Mole Fraction conversion for multi-component alloys
# wt_to_mol(wt, M)  →  mole fractions
# mol_to_wt(x, M)   →  weight fractions

# ── Common molar masses [g/mol] ───────────────────────────
M_Fe = 55.845   // iron
M_Ni = 58.693   // nickel
M_Cr = 51.996   // chromium
M_Al = 26.982   // aluminium
M_Ti = 47.867   // titanium
M_Co = 58.933   // cobalt
M_Cu = 63.546   // copper
M_C  = 12.011   // carbon
M_Mn = 54.938   // manganese
M_Mo = 95.960   // molybdenum

# ── Example: AISI 316 stainless steel (wt%) ────────────────
# Fe–17Cr–12Ni–2.5Mo  (balance Fe)
wt_316 = [68.5, 17.0, 12.0, 2.5]   // Fe, Cr, Ni, Mo [wt%]
M_316  = [M_Fe, M_Cr, M_Ni, M_Mo]
x_316  = wt_to_mol(wt_316, M_316)   // mole fractions
x_316

# ── Back-conversion check (should match wt_316 / 100) ──────
wt_back = mol_to_wt(x_316, M_316)   // weight fractions
wt_back

# ── Binary Fe-Ni: scan Ni wt% from 0 to 100 ───────────────
// Side plot: X=wt_Ni_arr, Y=x_Ni_arr, Type=lines
n_scan = 101
wt_Ni_arr = linspace(0, 100, n_scan)
x_Ni_arr  = zeros(n_scan)
for i in range(n_scan):
    xi = wt_to_mol([100 - wt_Ni_arr[i], wt_Ni_arr[i]], [M_Fe, M_Ni])
    x_Ni_arr[i] = xi[1]
x_Ni_arr
""",
    "Lever Rule (Binary)": """\
# Binary Phase Diagram — Lever Rule
# Two-phase (α + β) region at a fixed temperature
C0 = 0.30        // overall alloy composition [mol fraction B]
C_alp = 0.10     // α-phase boundary composition (solvus)
C_bet = 0.75     // β-phase boundary composition (liquidus/solvus)

f_alp = (C_bet - C0) / (C_bet - C_alp)   // α phase fraction
f_bet = (C0 - C_alp) / (C_bet - C_alp)   // β phase fraction
balance = f_alp * C_alp + f_bet * C_bet   // mass balance check (= C0)

// Phase fraction evolution as α-solvus shifts toward C0 (e.g. cooling)
// → Side plot: X=C_alp_arr, Y=f_bet_arr, Type=Lines
n_scan = 80
C_alp_arr = linspace(0.02, C0 - 0.005, n_scan)
f_bet_arr = (C0 - C_alp_arr) / (C_bet - C_alp_arr)
f_alp_arr = 1.0 - f_bet_arr
f_alp
f_bet
""",
    "Fracture Mechanics (LEFM)": """\
# Linear Elastic Fracture Mechanics — Mode I
# Geometry: central through-crack, infinite plate  K_I = σ√(πa)
K_IC = 50.0       // fracture toughness [MPa√m]  (e.g. structural steel)
sig_app = 200.0   // applied remote stress [MPa]
sig_ys = 350.0    // yield strength [MPa]
nu_p = 0.3        // Poisson ratio

// Critical crack half-length at onset of fast fracture
a_crit = (K_IC / sig_app)^2 / pi     // [m]
a_crit_mm = a_crit * 1000            // [mm]

// Irwin plastic zone radius
rp_stress = (K_IC / sig_ys)^2 / (2 * pi)   // plane stress [m]
rp_strain = rp_stress / 3                   // plane strain [m]
rp_mm = rp_stress * 1000                    // plane stress [mm]

// Minimum thickness for valid plane-strain K_IC test (ASTM E399)
B_min_mm = 2.5 * (K_IC / sig_ys)^2 * 1000  // [mm]

// J-integral (plane stress): J = K_I² / E
E_mod = 210000.0          // Young's modulus [MPa]
J_crit = K_IC^2 / E_mod   // [MPa·m] = [N/mm]

// K_I growth curve vs crack size
// → Side plot: X=a_mm_arr, Y=K_arr, Type=Lines  (compare to K_IC)
n_crack = 100
a_arr = linspace(0.0005, 0.05, n_crack)    // crack half-length [m]
K_arr = sig_app * sqrt(pi * a_arr)          // K_I [MPa√m]
a_mm_arr = a_arr * 1000                     // [mm]
a_crit_mm
rp_mm
B_min_mm
""",
    "Fatigue — S-N & Paris Law": """\
# Fatigue: Basquin S-N Curve + Paris Law crack growth

// ── S-N Curve: σ_a = σ_f' · (2·N)^b  (Basquin / Coffin-Manson) ──────────
sig_uts = 600.0         // ultimate tensile strength [MPa]
sig_fp = 0.9 * sig_uts  // fatigue strength coefficient σ_f' [MPa]
b_bas = -0.085          // Basquin exponent (steel: -0.05 to -0.12)

// S-N curve arrays — Side plot: X=N_sn, Y=sig_a, Type=Lines
n_sn = 150
N_sn = linspace(1e2, 1e7, n_sn)
sig_a = sig_fp * (2 * N_sn)^b_bas         // stress amplitude [MPa]

// Estimated endurance limit at 1e6 cycles
N_end = 1e6
sig_end = sig_fp * (2 * N_end)^b_bas      // [MPa]

// ── Paris Law: da/dN = C·(ΔK)^m ─────────────────────────────────────────
C_par = 3e-12    // Paris coefficient [m·cycle⁻¹·(MPa√m)⁻ᵐ]
m_par = 3.0      // Paris exponent
d_sig = 150.0    // stress range Δσ [MPa]  (= σ_max - σ_min)
a_i = 0.001      // initial crack half-length [m]  (1 mm)
a_f = 0.025      // critical crack half-length [m]  (25 mm)

// Analytical fatigue life (closed form, F=1, m≠2)
exp_p = 1.0 - m_par / 2
N_life = (a_f^exp_p - a_i^exp_p) / (exp_p * C_par * (d_sig * sqrt(pi))^m_par)

// Numerical crack growth a(N) — each step = dN_step cycles
// → Side plot: X=N_growth, Y=a_mm_growth, Type=Lines
n_grow = 400
dN_step = N_life / n_grow
a_growth = zeros(n_grow)
a_growth[0] = a_i
for k in range(1, n_grow):
    dK = d_sig * sqrt(pi * a_growth[k-1])
    a_growth[k] = a_growth[k-1] + C_par * dK^m_par * dN_step
    if a_growth[k] >= a_f:
        a_growth[k] = a_f
N_growth = linspace(0, N_life, n_grow)
a_mm_growth = a_growth * 1000              // [mm]
sig_end
N_life
""",
    "Dimensionless Numbers": """\
# Dimensionless numbers for pipe flow (water at 20°C)
rho_w = 998.0        // density [kg/m³]
mu_w = 1e-3          // dynamic viscosity [Pa·s]
v_flow = 2.0         // flow velocity [m/s]
d_pipe = 0.05        // pipe diameter [m]
cp_w = 4182.0        // specific heat [J/kg·K]
k_w = 0.6            // thermal conductivity [W/m·K]
Re = reynolds(rho_w, v_flow, d_pipe, mu_w)
Pr = prandtl(mu_w, cp_w, k_w)
Nu = nusselt_dittus(Re, Pr)
""",
    "Arrhenius & Diffusion": """\
# Arrhenius Equation & Solid-State Diffusion
# D(T) = D₀ · exp(−Q / R·T)
# Example: carbon diffusion in γ-iron (austenite) — steel carburisation

# ── Arrhenius parameters ──────────────────────────────────
D0_arr = 2.0e-5    // pre-exponential factor [m²/s]
Q_arr = 142000.0   // activation energy [J/mol]  (142 kJ/mol)
R_arr = 8.314      // gas constant [J/mol·K]

# ── D(T) over a temperature range ────────────────────────
n_T = 200
T_K = linspace(800, 1300, n_T)            // temperature [K]
D_arr_T = D0_arr * exp(-Q_arr / (R_arr * T_K))  // diffusivity [m²/s]

// Arrhenius plot — straight line: slope = -Q/R  (in kJ/mol: slope ≈ -17)
// Side plot: X=inv_T, Y=D_log, Type=Lines
inv_T = 1000.0 / T_K                      // 1000/T [K⁻¹] — conventional
D_log = log10(D_arr_T)                    // log₁₀(D)

# ── D at key temperatures ─────────────────────────────────
T_900  = 900.0  + 273.15
T_1000 = 1000.0 + 273.15
T_1100 = 1100.0 + 273.15
D_900  = D0_arr * exp(-Q_arr / (R_arr * T_900))
D_1000 = D0_arr * exp(-Q_arr / (R_arr * T_1000))
D_1100 = D0_arr * exp(-Q_arr / (R_arr * T_1100))

# ── Diffusion length √(D·t) ───────────────────────────────
t_diff = 3600.0              // process time [s]  (1 hour)
x_diff_mm = sqrt(D_1000 * t_diff) * 1000   // characteristic length [mm]

# ── Concentration profile — erf solution ─────────────────
# C(x,t) = Cs + (C0−Cs)·erf(x / 2√(Dt))
# Boundary: surface held at Cs, bulk starts at C0
C_s = 1.0        // surface carbon [wt%]
C_0 = 0.2        // initial bulk carbon [wt%]
n_x = 200
x_m = linspace(0, 5e-3, n_x)             // depth [m], 0–5 mm
C_prof = C_s + (C_0 - C_s) * erf(x_m / (2 * sqrt(D_1000 * t_diff)))
x_mm = x_m * 1000                        // depth [mm]

// Side plot: X=x_mm, Y=C_prof, Type=Lines → carbon concentration profile
D_1000
x_diff_mm
""",
    "Avrami (JMAK) Kinetics": """\
# Avrami / JMAK Phase Transformation Kinetics
# f(t) = 1 − exp(−k·tⁿ)
# f = transformed fraction, n = Avrami exponent, k = rate constant

# ── Parameters ────────────────────────────────────────────
n_av = 3.0      // Avrami exponent:  1=1D growth, 2=2D, 3=3D site-saturation
k_av = 0.005    // rate constant [s⁻ⁿ]  (higher k → faster transformation)
t_end = 200.0   // end time [s]

# ── S-curve: transformed fraction vs time ─────────────────
n_pts = 300
t_jmak = linspace(0.01, t_end, n_pts)  // avoid t=0 for log plot
f_jmak = 1.0 - exp(-k_av * t_jmak^n_av)

// Side plot: X=t_jmak, Y=f_jmak, Type=Lines → sigmoidal S-curve

# ── Characteristic transformation times ───────────────────
t_10 = (log(1.0 / (1.0 - 0.10)) / k_av)^(1.0 / n_av)  // 10% transformed
t_50 = (log(1.0 / (1.0 - 0.50)) / k_av)^(1.0 / n_av)  // 50% transformed
t_90 = (log(1.0 / (1.0 - 0.90)) / k_av)^(1.0 / n_av)  // 90% transformed

# ── Avrami linearisation ──────────────────────────────────
# ln(−ln(1−f)) = n·ln(t) + ln(k) → slope on log-log = n
// Side plot: X=ln_t, Y=avrami_y, Type=Lines → straight line, slope = n
ln_t = log(t_jmak)
avrami_y = log(-log(1.0 - f_jmak))

# ── Effect of temperature via Arrhenius k(T) ─────────────
# k(T) = k₀·exp(−Q/R·T) — faster at higher T
Q_jmak = 150000.0   // activation energy [J/mol]
k0_jmak = 1e10      // pre-exponential [s⁻ⁿ]
R_jmak = 8.314
n_T2 = 5
T_scan = linspace(923, 1073, n_T2)          // 650–800 °C in Kelvin
k_scan = k0_jmak * exp(-Q_jmak / (R_jmak * T_scan))
t50_scan = (log(2.0) / k_scan)^(1.0 / n_av) // t50 vs temperature [s]

t_10
t_50
t_90
""",
    "Rule of Mixtures (Composite)": """\
# Rule of Mixtures — Composite Material Properties
# Fibre-reinforced composite: matrix (m) + fibre (f)

# ── Material properties ───────────────────────────────────────────────────
E_f = 230.0     // fibre Young's modulus [GPa]  (carbon fibre)
E_m = 3.5       // matrix Young's modulus [GPa] (epoxy)
nu_f = 0.20     // fibre Poisson ratio
nu_m = 0.35     // matrix Poisson ratio
sig_f = 3500.0  // fibre tensile strength [MPa]
sig_m = 80.0    // matrix tensile strength [MPa]
rho_f = 1750.0  // fibre density [kg/m³]
rho_m = 1200.0  // matrix density [kg/m³]

# ── Scan over fibre volume fraction Vf ───────────────────────────────────
n_vf = 100
Vf = linspace(0, 1, n_vf)   // fibre volume fraction [0..1]
Vm = 1.0 - Vf                // matrix volume fraction

# Longitudinal (parallel) — Rule of Mixtures (upper Voigt bound)
E_L = Vf * E_f + Vm * E_m                      // [GPa]
nu_L = Vf * nu_f + Vm * nu_m                   // Poisson ratio (L)

# Transverse (perpendicular) — Reuss bound (series model)
E_T = 1.0 / (Vf / E_f + Vm / E_m)             // [GPa]

# Halpin-Tsai transverse modulus (more accurate for cylindrical fibres)
xi_ht = 2.0                                    // fibre aspect ratio factor (=2 for circular)
eta_ht = (E_f / E_m - 1) / (E_f / E_m + xi_ht)
E_T_HT = E_m * (1 + xi_ht * eta_ht * Vf) / (1 - eta_ht * Vf)  // [GPa]

# Density (exact linear mixture)
rho_c = Vf * rho_f + Vm * rho_m               // [kg/m³]

# Specific modulus (stiffness-to-weight)
E_L_spec = E_L * 1e9 / rho_c                  // [m²/s²] = [J/kg]

# Longitudinal strength (ROM)
sig_L = Vf * sig_f + Vm * sig_m               // [MPa]

# Critical fibre volume fraction (fibres must carry more than matrix alone)
// Vf_crit: sig_m*(1-Vf) = Vf*sig_f + (1-Vf)*sig_m → always positive here
// Minimum Vf for composite to exceed neat matrix strength:
Vf_crit = (sig_m - sig_m) / (sig_f - sig_m)  // = 0 when sig_f >> sig_m

# At a specific Vf of interest
Vf0 = 0.60                                     // design fibre volume fraction
Vm0 = 1.0 - Vf0
E_L0   = Vf0 * E_f + Vm0 * E_m
E_T0   = 1.0 / (Vf0 / E_f + Vm0 / E_m)
rho_c0 = Vf0 * rho_f + Vm0 * rho_m
sig_L0 = Vf0 * sig_f + Vm0 * sig_m

// Side plot: X=Vf, Y=E_L or E_T or E_T_HT, Type=Lines
// Compare Voigt (E_L), Reuss (E_T), Halpin-Tsai (E_T_HT)
E_L0
E_T0
sig_L0
rho_c0
""",
    "Elastic Anisotropy (Cubic)": """\
# Elastic Anisotropy — Cubic Crystal
# Directional Young's modulus E(n) from stiffness constants C_ij

# ── Elastic stiffness constants [GPa] — pick a material ──────────────────
# Copper  (FCC):   C11=168, C12=121, C44=75   → A=3.21  (highly anisotropic)
# Iron    (BCC):   C11=229, C12=134, C44=116  → A=2.37
# Aluminum(FCC):   C11=108, C12=62,  C44=28   → A=1.22  (nearly isotropic)
# Tungsten(BCC):   C11=533, C12=205, C44=163  → A≈1.00  (isotropic)
# Nickel  (FCC):   C11=247, C12=153, C44=122  → A=2.60
C11 = 168.0
C12 = 121.0
C44 = 75.0

# Zener anisotropy ratio (A=1 → isotropic)
A_zener = 2 * C44 / (C11 - C12)

# Compliance constants [1/GPa]: S = C^{-1}
den = (C11 - C12) * (C11 + 2 * C12)
S11 = (C11 + C12) / den
S12 = -C12 / den
S44 = 1.0 / C44

// Anisotropy factor in compliance space (zero if isotropic)
A_fac = S11 - S12 - S44 / 2

# Young's modulus along high-symmetry directions [GPa]
# 1/E(n) = S11 - 2*A_fac*(n1²n2² + n2²n3² + n3²n1²)
E_100 = 1.0 / S11                         // <100> direction
E_110 = 1.0 / (S11 - 2 * A_fac * 0.25)   // <110> direction
E_111 = 1.0 / (S11 - 2 * A_fac / 3)      // <111> direction

# E(θ) polar plot in the (001) plane — n = [cos θ, sin θ, 0]
# l(n) = n1²n2² = cos²θ·sin²θ
n_ang = 360
theta = linspace(0, 2*pi, n_ang)
l_001 = (cos(theta) * sin(theta))^2
E_001 = 1.0 / (S11 - 2 * A_fac * l_001)    // E(θ) [GPa]

// Cartesian polar coords — Side plot: X=E_x, Y=E_y, Type=Lines
// → closed curve showing stiffest/softest directions in (001) plane
E_x = E_001 * cos(theta)
E_y = E_001 * sin(theta)

# E(θ) polar plot in the (110) plane — n = [sinθ/√2, sinθ/√2, cosθ]
# θ=0 → [001], θ=90° → [110], θ≈54.7° → [111]
l_110p = sin(theta)^4 / 4 + sin(theta)^2 * cos(theta)^2
E_110p = 1.0 / (S11 - 2 * A_fac * l_110p)  // E(θ) [GPa]
E_x2 = E_110p * sin(theta)    // x-axis = in-plane [110] component
E_y2 = E_110p * cos(theta)    // y-axis = [001] component

// Switch X=E_x2, Y=E_y2 to see (110) plane cross-section
// The [111] peak appears at θ≈54.7° (= arctan(√2))
A_zener
E_100
E_110
E_111
""",
    "FCC Slip Systems & RSS": """\
# FCC Slip Systems — Resolved Shear Stress with crystal rotation
# Schmid's law: RSS_i = b_hat_i . sigma_crystal . n_hat_i

# Applied stress tensor [MPa] (symmetric 3x3, lab frame)
sigma = [[100, 20, 0], [20, -50, 10], [0, 10, 30]]

# Crystal orientation: Euler angles (Bunge ZXZ convention, degrees)
# Change these to rotate the crystal and watch RSS change
phi1 = 30.0    // 1st rotation around Z
Phi  = 20.0    // tilt around X
phi2 = 10.0    // 2nd rotation around Z

p1 = phi1 * deg
Ph = Phi  * deg
p2 = phi2 * deg

// eye(3)@ forces list→numpy so matrix @ works
Rz1 = eye(3) @ [[cos(p1),-sin(p1),0],[sin(p1),cos(p1),0],[0,0,1]]
Rx  = eye(3) @ [[1,0,0],[0,cos(Ph),-sin(Ph)],[0,sin(Ph),cos(Ph)]]
Rz2 = eye(3) @ [[cos(p2),-sin(p2),0],[sin(p2),cos(p2),0],[0,0,1]]
R = Rz1 @ Rx @ Rz2

// Stress in crystal frame: R^T * sigma * R
sigma_c = transpose(R) @ sigma @ R

// FCC: 12 slip systems {111}<110> (Schmid-Boas notation)
// Systems 1-3: (111), 4-6: (-111), 7-9: (1-11), 10-12: (11-1)
n_all = [[ 1, 1, 1],[ 1, 1, 1],[ 1, 1, 1],[-1, 1, 1],[-1, 1, 1],[-1, 1, 1],[ 1,-1, 1],[ 1,-1, 1],[ 1,-1, 1],[ 1, 1,-1],[ 1, 1,-1],[ 1, 1,-1]]
b_all = [[ 0, 1,-1],[ 1, 0,-1],[ 1,-1, 0],[ 0, 1,-1],[ 1, 1, 0],[ 1, 0, 1],[ 0, 1, 1],[ 1, 1, 0],[ 1, 0,-1],[ 0, 1, 1],[ 1, 0, 1],[ 1,-1, 0]]

// RSS for each of the 12 slip systems
rss = zeros(12)
for idx in range(12):
    n_hat = normalize(n_all[idx])
    b_hat = normalize(b_all[idx])
    rss[idx] = dot(b_hat, sigma_c @ n_hat)

rss_abs = abs(rss)
rss_max = max(rss_abs)    // max RSS = critical slip system [MPa]
// Side plot: Y=rss_abs (or rss), Type=Bar → shows all 12 systems
rss
""",
    "2D Yield Surface (VM & Tresca)": """\
# 2D Yield Surface — Von Mises vs Tresca (plane stress, σ₃ = 0)
sigma_y = 250.0      // uniaxial yield stress [MPa]

// Von Mises ellipse: σ₁² - σ₁σ₂ + σ₂² = σ_y²
// → Side plot: X=sigma1_vm, Y=sigma2_vm, Type=Lines
theta = linspace(0, 2*pi, 360)
sigma1_vm = sigma_y * (cos(theta) + sin(theta) / sqrt(3))
sigma2_vm = sigma_y * (cos(theta) - sin(theta) / sqrt(3))

// Tresca hexagon — 7 vertices (closed)
// → Side plot: X=sigma1_tr, Y=sigma2_tr, Type=Lines
sy = sigma_y
sigma1_tr = [sy, sy, 0.0, -sy, -sy, 0.0, sy]
sigma2_tr = [0.0, sy, sy, 0.0, -sy, -sy, 0.0]

// Check a stress point against both surfaces
p1 = 200.0         // principal stress σ₁ [MPa]
p2 = -80.0         // principal stress σ₂ [MPa]
vm_eq = sqrt(p1^2 - p1*p2 + p2^2)        // Von Mises equivalent stress
tr_eq = max([abs(p1 - p2), abs(p1), abs(p2)])  // Tresca equivalent stress
vm_margin = sigma_y - vm_eq    // >0 elastic, <0 yielded (Von Mises)
tr_margin = sigma_y - tr_eq    // >0 elastic, <0 yielded (Tresca)
""",
    "Mohr's Circle (2D Stress)": """\
# Mohr's Circle — 2D plane stress state
# Change sxx, syy, txy to your stress values [MPa]
sxx = 80.0      // normal stress x [MPa]
syy = 30.0      // normal stress y [MPa]
txy = 25.0      // shear stress xy [MPa]

C_mhr = (sxx + syy) / 2                          // circle centre
R_mhr = sqrt(((sxx - syy) / 2)^2 + txy^2)        // radius = max shear
sigma1 = C_mhr + R_mhr    // major principal stress [MPa]
sigma2 = C_mhr - R_mhr    // minor principal stress [MPa]
tau_max = R_mhr            // maximum shear stress [MPa]
theta_p = 0.5 * atan2(2*txy, sxx - syy)          // principal angle [rad]
theta_deg = degrees(theta_p)

// Circle for side plot — set X=sigma_c, Y=tau_c, Type=Lines
theta = linspace(0, 2*pi, 300)
sigma_c = C_mhr + R_mhr * cos(theta)
tau_c = R_mhr * sin(theta)
sigma1
sigma2
tau_max
theta_deg
""",
    "Spring-Mass Oscillator": """\
# Spring-mass system: x'' + (k/m)*x = 0
// Euler integration — use small dt for accuracy
k_spring = 10.0      // spring constant [N/m]
mass = 1.0           // mass [kg]
omega = sqrt(k_spring / mass)
dt = 0.01            // time step [s]
n_steps = 628        // ~2π/omega * 100
x_pos = zeros(n_steps)
v_vel = zeros(n_steps)
x_pos[0] = 1.0       // initial displacement [m]
v_vel[0] = 0.0       // initial velocity [m/s]
for i in range(1, n_steps):
    x_pos[i] = x_pos[i-1] + dt * v_vel[i-1]
    v_vel[i] = v_vel[i-1] - dt * (k_spring / mass) * x_pos[i-1]
t_osc = linspace(0, n_steps * dt, n_steps)
x_pos
""",
}


def build_fn_overlay() -> html.Div:
    """Build the floating functions reference panel (position: fixed overlay)."""

    def _section_items(section):
        if section["title"] in GRID_HELP_TITLES:
            return html.Div(
                [
                    html.Div(
                        item,
                        style={
                            "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                            "fontSize": "11px",
                            "color": "#102a43",
                            "background": "rgba(255,255,255,0.96)",
                            "border": "1px solid rgba(226,232,240,0.95)",
                            "borderRadius": "999px",
                            "padding": "5px 10px",
                            "textAlign": "center",
                            "boxShadow": "0 1px 2px rgba(15,23,42,0.04)",
                        },
                    )
                    for item in section["items"]
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                    "gap": "6px 6px",
                },
            )
        return html.Div(
            [html.Div(item) for item in section["items"]],
            style={
                "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                "fontSize": "12px",
                "lineHeight": "1.65",
                "color": "#102a43",
                "background": "rgba(255,255,255,0.55)",
                "border": "1px solid rgba(148,163,184,0.16)",
                "borderRadius": "10px",
                "padding": "7px 10px",
                "display": "grid",
                "gap": "1px",
            },
        )

    sections_html = [
        html.Div(
            [
                html.Div(
                    section["title"],
                    style={
                        "fontSize": "11px",
                        "fontWeight": "700",
                        "textTransform": "uppercase",
                        "letterSpacing": "0.04em",
                        "color": "#667085",
                        "marginBottom": "6px",
                    },
                ),
                _section_items(section),
                html.Div(
                    section.get("note", ""),
                    style={
                        "fontSize": "11px",
                        "color": "#667085",
                        "lineHeight": "1.4",
                        "marginTop": "5px",
                        "display": "block" if section.get("note") else "none",
                    },
                ),
            ],
            style={"marginBottom": "10px"},
        )
        for section in NOTEBOOK_HELP
    ]

    examples_html = html.Div(
        [
            html.Div(
                "Quick Examples",
                style={
                    "fontSize": "11px",
                    "fontWeight": "700",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.04em",
                    "color": "#667085",
                    "marginBottom": "6px",
                },
            ),
            html.Div(
                [
                    html.Div(
                        ex,
                        style={
                            "fontFamily": "'JetBrains Mono','Fira Code','Consolas',monospace",
                            "fontSize": "12px",
                            "color": "#102a43",
                            "padding": "3px 0",
                        },
                    )
                    for ex in NOTEBOOK_EXAMPLES
                ],
                style={
                    "background": "rgba(255,255,255,0.55)",
                    "border": "1px solid rgba(148,163,184,0.16)",
                    "borderRadius": "10px",
                    "padding": "7px 10px",
                },
            ),
        ]
    )

    return html.Div(
        [
            # header
            html.Div(
                [
                    html.Span(
                        "Functions Reference",
                        style={"fontWeight": "700", "fontSize": "14px", "color": "#0f172a"},
                    ),
                    html.Button(
                        "×",
                        id="notebook-fn-close-btn",
                        n_clicks=0,
                        style={
                            "background": "none",
                            "border": "none",
                            "cursor": "pointer",
                            "fontSize": "22px",
                            "color": "#667085",
                            "lineHeight": "1",
                            "padding": "0 2px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "borderBottom": "1px solid rgba(148,163,184,0.2)",
                    "paddingBottom": "10px",
                    "marginBottom": "14px",
                    "position": "sticky",
                    "top": "0",
                    "background": "white",
                    "zIndex": "1",
                },
            ),
            # content
            html.Div(sections_html, style={"display": "grid", "gap": "2px"}),
            examples_html,
        ],
        id="notebook-fn-panel",
        style={
            "display": "none",
            "position": "fixed",
            "top": "60px",
            "right": "20px",
            "width": "400px",
            "maxHeight": "84vh",
            "overflowY": "auto",
            "background": "white",
            "borderRadius": "14px",
            "boxShadow": "0 20px 60px rgba(15,23,42,0.18)",
            "padding": "18px 16px",
            "zIndex": "9999",
            "border": "1px solid rgba(148,163,184,0.25)",
        },
    )


def default_notebook_state() -> dict:
    """Return default notebook state."""
    return {
        "text": "",
        "variables": {},
    }


def build_notebook_results(result_lines: list[str] | None = None) -> list[html.Div]:
    """Build the result gutter lines."""
    result_lines = result_lines or []
    rows = max(NOTEBOOK_ROWS, len(result_lines))
    children = []
    for index in range(rows):
        text = result_lines[index] if index < len(result_lines) else ""
        children.append(
            html.Div(
                text,
                style={
                    "height": NOTEBOOK_LINE_HEIGHT,
                    "lineHeight": NOTEBOOK_LINE_HEIGHT,
                    "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                    "fontSize": "19px",
                    "fontWeight": "600",
                    "color": "#0b5d52" if text and not text.startswith("Error:") else "#b42318" if text else "#98a2b3",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "paddingLeft": "2px",
                },
                title=text,
            )
        )
    return children


def _empty_nb_figure() -> go.Figure:
    """Return a blank placeholder figure for the notebook side plot."""
    fig = go.Figure()
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor="rgba(200,210,220,0.5)", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(200,210,220,0.5)", zeroline=False),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=20, t=30, b=50),
        annotations=[dict(
            text="Define arrays in the notebook<br>then select x / y variables above",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color="#94a3b8"),
        )],
    )
    return fig


def build_calculation_notebook(state: dict | None = None) -> html.Div:
    """Build the calculation notebook tab content."""
    state = state or default_notebook_state()
    text = state.get("text", "")
    array_vars = state.get("array_variables", {})
    arr_options = [{"label": k, "value": k} for k in sorted(array_vars)]

    _btn = lambda label, id_: html.Button(
        label, id=id_, className="graphs-add-panel-btn", n_clicks=0,
        style={"background": "#0f2942", "border": "1px solid #173b5c",
               "boxShadow": "none", "padding": "8px 14px", "fontSize": "13px"},
    )

    # Build grouped dropdown options with disabled category headers
    snippet_options = []
    for group_label, keys in NOTEBOOK_SNIPPET_GROUPS.items():
        snippet_options.append({"label": f"── {group_label} ──", "value": f"__group__{group_label}", "disabled": True})
        for k in keys:
            if k in NOTEBOOK_SNIPPETS:
                snippet_options.append({"label": f"  {k}", "value": k})

    return html.Div(
        [
            # ── top toolbar ─────────────────────────────────────────────────
            html.Div(
                [
                    dcc.ConfirmDialogProvider(
                        children=_btn("Clear", "notebook-clear-btn"),
                        id="notebook-clear-confirm-provider",
                        message="Clear all notebook content? This cannot be undone.",
                    ),
                    _btn("Save (.txt)", "notebook-save-btn"),
                    dcc.Upload(
                        _btn("Load (.txt)", "notebook-load-btn"),
                        id="notebook-load-upload",
                        accept=".txt",
                        multiple=False,
                    ),
                    dcc.Download(id=NOTEBOOK_DOWNLOAD_ID),
                    dcc.Store(id="notebook-monaco-sync-dummy"),
                    # ── example snippet picker ────────────────────────────
                    html.Div(style={"width": "1px", "background": "rgba(148,163,184,0.3)",
                                    "alignSelf": "stretch", "margin": "0 4px"}),
                    dcc.Dropdown(
                        id="notebook-example-select",
                        options=snippet_options,
                        value=None,
                        placeholder="Load example…",
                        clearable=True,
                        style={"fontSize": "13px", "minWidth": "220px", "maxWidth": "280px"},
                    ),
                    _btn("Insert", "notebook-insert-example-btn"),
                    html.Div(style={"width": "1px", "background": "rgba(148,163,184,0.3)",
                                    "alignSelf": "stretch", "margin": "0 4px"}),
                    _btn("≡ Functions", "notebook-fn-btn"),
                    dcc.Store(id="notebook-fn-dummy"),
                    html.Div(
                        "New here? Start with  Quick Start",
                        style={"fontSize": "12px", "color": "#667085", "fontStyle": "italic",
                               "marginLeft": "4px"},
                    ),
                ],
                style={"display": "flex", "gap": "10px", "marginBottom": "10px",
                       "alignItems": "center"},
            ),
            html.Div(
                [
                    html.Span("Type one expression per line — results appear instantly on the right.  "
                              "Variables carry through all lines below.  "
                              "Use  "),
                    html.Code("// comment", style={"fontFamily": "monospace", "fontSize": "12px",
                                                   "background": "rgba(15,23,42,0.05)",
                                                   "borderRadius": "4px", "padding": "1px 5px"}),
                    html.Span("  to annotate,  "),
                    html.Code("^", style={"fontFamily": "monospace", "fontSize": "12px",
                                          "background": "rgba(15,23,42,0.05)",
                                          "borderRadius": "4px", "padding": "1px 5px"}),
                    html.Span("  for power,  "),
                    html.Code("210*GPa", style={"fontFamily": "monospace", "fontSize": "12px",
                                                "background": "rgba(15,23,42,0.05)",
                                                "borderRadius": "4px", "padding": "1px 5px"}),
                    html.Span("  for units.  Arrays defined here appear in the plot panel →"),
                ],
                style={"fontSize": "13px", "color": "#667085", "marginBottom": "14px",
                       "lineHeight": "1.6"},
            ),
            # ── main row: notebook sheet + side plot ─────────────────────────
            html.Div(
                [
            html.Div(
                [
                    # ── Monaco editor container (shown after Monaco loads) ──
                    html.Div(
                        id="notebook-monaco-container",
                        style={
                            "flex": "1",
                            "height": "76vh",
                            "minHeight": "76vh",
                            "display": "none",   # Monaco JS sets this to 'flex'
                        },
                    ),
                    # ── Plain textarea fallback (hidden once Monaco loads) ──
                    dcc.Textarea(
                        id="notebook-textarea",
                        value=text,
                        placeholder="# Start typing or load an example from the dropdown above\nx = 5\ny = 3\nz = x^2 + y       // result appears on the right →",
                        style={
                            "flex": "1",
                            "height": "76vh",
                            "minHeight": "76vh",
                            "padding": "18px 18px",
                            "fontSize": "20px",
                            "lineHeight": NOTEBOOK_LINE_HEIGHT,
                            "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                            "border": "none",
                            "outline": "none",
                            "resize": "none",
                            "backgroundColor": "transparent",
                            "backgroundImage": "repeating-linear-gradient(to bottom, transparent 0px, transparent 33px, #eef2f6 33px, #eef2f6 34px)",
                            "backgroundPosition": "0 18px",
                            "backgroundAttachment": "local",
                            "color": "#0f172a",
                            "whiteSpace": "pre",
                            "overflowY": "auto",
                        },
                    ),
                    dcc.Input(
                        id="notebook-live-text",
                        type="text",
                        value=text,
                        style={"display": "none"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                build_notebook_results([]),
                                id="notebook-results",
                            ),
                            html.Div(id="notebook-debug", style={"display": "none"}),
                        ],
                        style={
                            "width": RESULTS_GUTTER_WIDTH,
                            "minWidth": RESULTS_GUTTER_WIDTH,
                            "padding": "18px 14px 18px 8px",
                            "borderLeft": "1px solid rgba(15, 23, 42, 0.045)",
                            "background": "linear-gradient(180deg, rgba(252,253,255,0.78) 0%, rgba(248,250,252,0.68) 100%)",
                            "overflowY": "hidden",
                            "height": "76vh",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "alignItems": "stretch",
                    "width": "100%",
                    "maxWidth": NOTEBOOK_SHEET_WIDTH,
                    "minHeight": "76vh",
                    "background": "#fffdf8",
                    "border": "1px solid rgba(148, 163, 184, 0.22)",
                    "borderRadius": "18px",
                    "boxShadow": "0 14px 34px rgba(15, 23, 42, 0.06)",
                    "overflow": "hidden",
                    "position": "relative",
                    "flexShrink": "0",
                },
            ),
            # ── side plot panel ──────────────────────────────────────────────
            html.Div(
                [
                    # controls row
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div("X", style={"fontSize": "11px", "fontWeight": "700",
                                                         "color": "#475467", "marginBottom": "3px",
                                                         "textTransform": "uppercase", "letterSpacing": "0.06em"}),
                                    dcc.Dropdown(
                                        id="nb-plot-x-var",
                                        options=arr_options,
                                        value=None,
                                        placeholder="x array…",
                                        clearable=True,
                                        style={"fontSize": "12px", "minWidth": "120px"},
                                    ),
                                ],
                                style={"flex": "1"},
                            ),
                            html.Div(
                                [
                                    html.Div("Y", style={"fontSize": "11px", "fontWeight": "700",
                                                         "color": "#475467", "marginBottom": "3px",
                                                         "textTransform": "uppercase", "letterSpacing": "0.06em"}),
                                    dcc.Dropdown(
                                        id="nb-plot-y-vars",
                                        options=arr_options,
                                        value=[],
                                        multi=True,
                                        placeholder="y array(s)…",
                                        style={"fontSize": "12px", "minWidth": "160px"},
                                    ),
                                ],
                                style={"flex": "2"},
                            ),
                            html.Div(
                                [
                                    html.Div("Type", style={"fontSize": "11px", "fontWeight": "700",
                                                            "color": "#475467", "marginBottom": "3px",
                                                            "textTransform": "uppercase", "letterSpacing": "0.06em"}),
                                    dcc.Dropdown(
                                        id="nb-plot-type",
                                        options=[
                                            {"label": "Lines", "value": "lines"},
                                            {"label": "Lines+Markers", "value": "lines+markers"},
                                            {"label": "Markers", "value": "markers"},
                                            {"label": "Bar", "value": "bar"},
                                            {"label": "Histogram", "value": "histogram"},
                                        ],
                                        value="lines",
                                        clearable=False,
                                        style={"fontSize": "12px", "minWidth": "130px"},
                                    ),
                                ],
                                style={"flex": "1"},
                            ),
                        ],
                        style={"display": "flex", "gap": "8px", "alignItems": "flex-start",
                               "marginBottom": "8px"},
                    ),
                    # plot tip
                    html.Div(
                        [
                            "Arrays from the notebook appear in X / Y above. "
                            "Pick Y (and optionally X), then choose a plot type. ",
                            html.Br(),
                            html.Span(
                                "Tip: ",
                                style={"fontWeight": "600", "color": "#667085"},
                            ),
                            html.Span(
                                "add ",
                                style={"color": "#94a3b8"},
                            ),
                            html.Code(
                                "// Side plot: X=t, Y=T, Type=lines",
                                style={
                                    "fontFamily": "'JetBrains Mono','Fira Code',monospace",
                                    "fontSize": "11px",
                                    "background": "rgba(15,23,42,0.04)",
                                    "borderRadius": "4px",
                                    "padding": "1px 5px",
                                    "color": "#475467",
                                },
                            ),
                            html.Span(
                                " to any snippet to auto-set the dropdowns on Insert.",
                                style={"color": "#94a3b8"},
                            ),
                        ],
                        style={"fontSize": "12px", "color": "#94a3b8", "marginBottom": "6px",
                               "lineHeight": "1.6"},
                    ),
                    # the plot
                    dcc.Graph(
                        id="notebook-side-plot",
                        figure=_empty_nb_figure(),
                        config={"displayModeBar": True, "scrollZoom": True},
                        style={"height": "calc(76vh - 60px)", "minHeight": "300px"},
                    ),
                ],
                style={
                    "flex": "1",
                    "minWidth": "380px",
                    "padding": "14px 16px 14px 20px",
                    "display": "flex",
                    "flexDirection": "column",
                },
            ),
                ],  # end flex row children
                style={
                    "display": "flex",
                    "alignItems": "flex-start",
                    "gap": "16px",
                    "width": "100%",
                },
            ),  # end flex row
            # ── floating functions reference overlay ─────────────────────────
            build_fn_overlay(),
        ],
        style={"padding": "18px 24px", "width": "100%"},
    )

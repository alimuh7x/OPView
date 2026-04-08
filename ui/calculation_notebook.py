"""
Calculation notebook UI for OPView.
"""

from __future__ import annotations

import uuid

from dash import dcc, html
import plotly.graph_objects as go
from config.settings_store import get as _setting_get

# Download component id used by save/load callbacks
NOTEBOOK_DOWNLOAD_ID = "notebook-download"


NOTEBOOK_ROWS = 4
NOTEBOOK_LINE_HEIGHT = "34px"
RESULTS_GUTTER_WIDTH = "440px"
FUNCTIONS_CARD_WIDTH = "360px"
NOTEBOOK_SHEET_WIDTH = "1280px"
NOTEBOOK_ROW_COLOR_A = "#fefeff"
NOTEBOOK_ROW_COLOR_B = "#f8fbfe"

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

NOTEBOOK_MARKDOWN_HELP = [
    ("Headings", "# Title\n## Section\n### Subsection"),
    ("Emphasis", "**bold**  *italic*  `inline code`"),
    ("Lists", "- item one\n- item two\n1. first\n2. second"),
    ("Links", "[OpenPhase](https://github.com/)"),
    ("Tables", "| Name | Value |\n| --- | ---: |\n| A | 10 |\n| B | 20 |"),
    ("Math", "$E = mc^2$\n\n$$\\sigma = E\\varepsilon$$"),
    ("Blockquote", "> Notes, assumptions, or warnings"),
    ("Code Block", "```python\nx = linspace(0, 1, 5)\ny = sin(x)\n```"),
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
theta = 45 * deg       // 45° converted to radians
s = sin(theta)         // sine of 45° ≈ 0.707

# ── Vectors & statistics ──────────────────────────────────
data = [1, 4, 9, 16, 25]
avg = mean(data)
total = sum(data)

# ── Arrays for plotting ───────────────────────────────────
t = linspace(0, 2*pi, 200)
y_wave = sin(t)
// After running: in the plot panel on the right →
//   set X = t,  Y = y_wave,  Type = Lines

# ── Multiline expressions ───────────────────────────
long_total = (
    x^2
    + y
    + total
)

# ── Dictionaries ───────────────────────────────────
material = {
    "name": "Steel",
    "E_GPa": 210,
    "nu": 0.30,
}
nu_value = material["nu"]

# ── List comprehensions ────────────────────────────
squares = [i^2 for i in range(6)]
shifted = [v + avg for v in data]

# ── Split matrix literals ──────────────────────────
small_mat = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]
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
n_all = [[ 1, 1, 1],[ 1, 1, 1],[ 1, 1, 1],[-1, 1, 1],
         [-1, 1, 1],[-1, 1, 1],[ 1,-1, 1],[ 1,-1, 1],
         [ 1,-1, 1],[ 1, 1,-1],[ 1, 1,-1],[ 1, 1,-1]]
b_all = [[ 0, 1,-1],[ 1, 0,-1],[ 1,-1, 0],[ 0, 1,-1],
         [ 1, 1, 0],[ 1, 0, 1],[ 0, 1, 1],[ 1, 1, 0],
         [ 1, 0,-1],[ 0, 1, 1],[ 1, 0, 1],[ 1,-1, 0]]

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
                        "",
                        id="notebook-fn-close-btn",
                        n_clicks=0,
                        className="opview-image-close-btn",
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
        "array_variables": {},
        "cells": [default_notebook_cell()],
    }


# ── Cell data model ───────────────────────────────────────────────────────────

def new_cell_id() -> str:
    return "cell-" + uuid.uuid4().hex[:12]


def default_cell(cell_type: str = "code", source: str = "") -> dict:
    """Return a new empty cell dict."""
    return {
        "id": new_cell_id(),
        "type": cell_type,
        "source": source,
        "outputs": [],
        "execution_blocks": [],
        "dirty": False,
    }


def default_notebook_cell(source: str = "") -> dict:
    """Return the default code-first notebook cell."""
    return default_cell(cell_type="code", source=source)


# ── Button styles ─────────────────────────────────────────────────────────────

_CELL_BTN = {
    "border": "none", "borderRadius": "5px", "cursor": "pointer",
    "fontFamily": "'Inter','Segoe UI',system-ui,sans-serif",
    "fontSize": "11px", "fontWeight": "500", "lineHeight": "1",
    "padding": "3px 9px", "transition": "background 150ms",
    "whiteSpace": "nowrap",
}

def _cell_btn(label, id_dict, variant="secondary", disabled=False, title=""):
    styles = {
        "secondary": {**_CELL_BTN, "background": "rgba(15,23,42,0.06)",
                      "color": "#344054", "border": "1px solid rgba(15,23,42,0.12)"},
        "danger":    {**_CELL_BTN, "background": "rgba(185,28,28,0.06)",
                      "color": "#991b1b", "border": "1px solid rgba(185,28,28,0.18)"},
        "primary":   {**_CELL_BTN, "background": "#001f41", "color": "#ffffff",
                      "border": "1px solid #001f41"},
        "add":       {**_CELL_BTN, "background": "rgba(0,31,65,0.08)",
                      "color": "#001f41", "border": "1px solid rgba(0,31,65,0.26)"},
        "md":        {**_CELL_BTN, "background": "rgba(0,31,65,0.08)",
                      "color": "#001f41", "border": "1px solid rgba(0,31,65,0.26)"},
    }
    if disabled:
        style = {**styles[variant], "opacity": "0.35", "cursor": "default"}
    else:
        style = styles[variant]
    kwargs = {"id": id_dict, "n_clicks": 0, "style": style}
    if disabled:
        kwargs["disabled"] = True
    if title:
        kwargs["title"] = title
    return html.Button(label, **kwargs)


# ── Cell layout builder ───────────────────────────────────────────────────────

def build_cell(cell: dict, cell_index: int, total_cells: int) -> html.Div:
    """Build the HTML layout for one notebook cell."""
    cell_id = cell["id"]
    cell_type = cell.get("type", "code")
    source = cell.get("source", "")
    outputs = cell.get("outputs", [])
    dirty = cell.get("dirty", False)
    is_code_cell = cell_type == "code"

    # ── Left: editor ─────────────────────────────────────────────────────────
    editor_area = html.Div(
        [
            # Hidden source mirror (JS writes here on change so Python can read it)
            dcc.Textarea(
                id={"type": "nb-cell-text", "index": cell_id},
                value=source,
                style={"display": "none"},
            ),
            # Monaco mount point — JS finds this by data attributes
            html.Div(
                id=f"nb-cell-editor-{cell_id}",
                **{
                    "data-cell-id": cell_id,
                    "data-cell-type": cell_type,
                    "data-cell-value": source,
                    "data-cell-init": "true",
                },
                style={"minHeight": "102px", "flex": "1"},
            ),
            # Markdown preview (hidden for code cells, shown for markdown)
            html.Div(
                id=f"nb-cell-md-preview-{cell_id}",
                className="nb-markdown-preview",
                style={
                    "display": "none",
                    "padding": "12px 16px 4px 16px",
                    "flex": "1",
                    "fontSize": "15px",
                    "lineHeight": "1.6",
                    "color": "#0f172a",
                    "fontFamily": "'Nunito','Segoe UI',system-ui,sans-serif",
                    "fontWeight": "600",
                    "minHeight": "102px",
                },
            ),
            html.Div(
                [
                    html.Button(
                        "Preview",
                        id={"type": "nb-cell-preview", "index": cell_id},
                        n_clicks=0,
                        style={
                            "display": "inline-flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "padding": "3px 8px",
                            "fontSize": "11px",
                            "fontWeight": "700",
                            "borderRadius": "6px",
                            "border": "1px solid rgba(0,31,65,0.18)",
                            "background": "rgba(255,255,255,0.92)",
                            "color": "#001f41",
                            "cursor": "pointer",
                            "boxShadow": "0 2px 10px rgba(15,23,42,0.06)",
                        },
                    ),
                    html.Button(
                        "Edit",
                        id={"type": "nb-cell-edit", "index": cell_id},
                        n_clicks=0,
                        style={
                            "display": "inline-flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "padding": "3px 8px",
                            "fontSize": "11px",
                            "fontWeight": "700",
                            "borderRadius": "6px",
                            "border": "1px solid rgba(185,28,28,0.18)",
                            "background": "rgba(255,255,255,0.92)",
                            "color": "#991b1b",
                            "cursor": "pointer",
                            "boxShadow": "0 2px 10px rgba(15,23,42,0.06)",
                        },
                    ),
                    html.Button(
                        "✕",
                        id={"type": "nb-cell-delete", "index": cell_id},
                        n_clicks=0,
                        title="Delete cell",
                        style={
                            "display": "inline-flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "padding": "3px 8px",
                            "fontSize": "11px",
                            "fontWeight": "700",
                            "borderRadius": "6px",
                            "border": "1px solid rgba(185,28,28,0.18)",
                            "background": "rgba(255,255,255,0.92)",
                            "color": "#991b1b",
                            "cursor": "pointer",
                            "boxShadow": "0 2px 10px rgba(15,23,42,0.06)",
                        },
                    ),
                ],
                className="nb-markdown-toolbar",
                style={
                    "display": "flex",
                    "gap": "4px",
                    "position": "absolute",
                    "top": "8px",
                    "right": "8px",
                    "zIndex": "2",
                },
            ) if not is_code_cell else None,
        ],
        style={"flex": "1", "minWidth": "0", "display": "flex", "flexDirection": "column", "position": "relative"},
    )

    # ── Right: results (code cells) or nothing (markdown cells) ──────────────
    if cell_type == "code":
        results_area = html.Div(
            [
                html.Div(
                    build_notebook_results(outputs),
                    id={"type": "nb-cell-results", "index": cell_id},
                    style={
                        "border": "1px solid #e2e8f0",
                        "borderRadius": "4px",
                        "overflow": "hidden",
                        "background": "#ffffff",
                    },
                ),
            ],
            style={
                "flex": "0 0 440px",
                "width": "440px",
                "minWidth": "440px",
                "padding": "0 10px 8px 0",
                "borderLeft": "none",
                "background": "transparent",
            },
        )
    else:
        results_area = html.Div(style={"width": "0", "overflow": "hidden"})

    # ── Controls bar (below the cell) ─────────────────────────────────────────
    stale_badge = html.Span(
        "⚠ stale",
        style={
            "display": "inline-flex" if dirty else "none",
            "fontSize": "10px", "fontWeight": "700",
            "color": "#b45309", "background": "#fef3c7",
            "border": "1px solid #fcd34d", "borderRadius": "4px",
            "padding": "1px 6px", "alignItems": "center",
        },
    )

    if cell_type == "code":
        run_btn = _cell_btn("▶ Run", {"type": "nb-cell-run", "index": cell_id}, "primary", title="Shift+Enter")
        controls = html.Div(
            [
                stale_badge,
                html.Div(style={"flex": "1"}),
                run_btn,
                _cell_btn("↑", {"type": "nb-cell-up", "index": cell_id}, "secondary",
                          disabled=(cell_index == 0), title="Move cell up"),
                _cell_btn("↓", {"type": "nb-cell-down", "index": cell_id}, "secondary",
                          disabled=(cell_index == total_cells - 1), title="Move cell down"),
                html.Div(style={"width": "1px", "background": "rgba(148,163,184,0.3)",
                                "alignSelf": "stretch", "margin": "0 2px"}),
                _cell_btn("✕", {"type": "nb-cell-delete", "index": cell_id}, "danger", title="Delete cell"),
            ],
            style={
                "display": "flex", "alignItems": "center", "gap": "4px",
                "padding": "4px 8px",
                "background": "#f8fafc",
                "borderTop": "1px solid rgba(148,163,184,0.2)",
            },
        )
    else:
        controls = html.Div(style={"display": "none"})

    # ── Cell wrapper ──────────────────────────────────────────────────────────
    return html.Div(
        [
            html.Div(
                [editor_area, results_area] if is_code_cell else [editor_area],
                style={"display": "flex", "alignItems": "stretch", "minHeight": "34px"},
            ),
            controls,
        ],
        id=f"nb-cell-wrapper-{cell_id}",
        className="nb-markdown-cell" if not is_code_cell else None,
        style={
            "border": "1px solid rgba(100,116,139,0.18)" if is_code_cell else "none",
            "borderLeft": "none",
            "borderRadius": "8px",
            "marginBottom": "10px" if is_code_cell else "2px",
            "background": "#ffffff" if is_code_cell else "transparent",
            "boxShadow": "0 1px 4px rgba(15,23,42,0.04)" if is_code_cell else "none",
            "overflow": "visible",
        },
    )


def build_markdown_help_overlay() -> html.Div:
    """Floating markdown help panel for notebook cells."""
    sections = []
    for title, sample in NOTEBOOK_MARKDOWN_HELP:
        sections.append(
            html.Div(
                [
                    html.Div(
                        title,
                        style={
                            "fontSize": "12px",
                            "fontWeight": "800",
                            "textTransform": "uppercase",
                            "letterSpacing": "0.05em",
                            "color": "#475467",
                            "marginBottom": "6px",
                        },
                    ),
                    html.Pre(
                        sample,
                        style={
                            "margin": "0",
                            "whiteSpace": "pre-wrap",
                            "fontFamily": "'JetBrains Mono','Fira Code','Consolas',monospace",
                            "fontSize": "12px",
                            "lineHeight": "1.55",
                            "color": "#102a43",
                            "background": "rgba(248,250,252,0.95)",
                            "border": "1px solid rgba(148,163,184,0.22)",
                            "borderRadius": "10px",
                            "padding": "10px 12px",
                        },
                    ),
                ],
                style={"display": "grid", "gap": "6px"},
            )
        )

    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        "Markdown Help",
                        style={"fontWeight": "700", "fontSize": "14px", "color": "#0f172a"},
                    ),
                    html.Button(
                        "",
                        id="notebook-md-close-btn",
                        n_clicks=0,
                        className="opview-image-close-btn",
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
            html.Div(
                "Supported here: GFM-style markdown, lists, tables, fenced code blocks, inline code, and KaTeX math.",
                style={"fontSize": "13px", "lineHeight": "1.6", "color": "#475467", "marginBottom": "12px"},
            ),
            html.Div(sections, style={"display": "grid", "gap": "12px"}),
        ],
        id="notebook-md-panel",
        style={
            "display": "none",
            "position": "fixed",
            "top": "60px",
            "right": "440px",
            "width": "380px",
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


def _build_cell_inserter(after_cell_id: str) -> html.Div:
    """Thin strip between cells with Add Code / Add Markdown buttons."""
    return html.Div(
        [
            _cell_btn("+ Code",     {"type": "nb-add-code",     "index": after_cell_id}, "add",  title="Add code cell below"),
            _cell_btn("+ Markdown", {"type": "nb-add-markdown", "index": after_cell_id}, "md",   title="Add markdown cell below"),
        ],
        className="nb-cell-inserter",
        style={"display": "flex", "alignItems": "center", "justifyContent": "center", "gap": "4px", "padding": "1px 2px"},
    )


def build_cells_container(cells: list) -> list:
    """Build the full list of cell HTML elements, with inserter strips between them."""
    total = len(cells)
    items = [_build_cell_inserter("__start__")]
    for i, cell in enumerate(cells):
        items.append(build_cell(cell, i, total))
        items.append(_build_cell_inserter(cell["id"]))
    return items


def build_notebook_results(
    result_lines: list[dict] | list[str] | None = None,
    min_rows: int = NOTEBOOK_ROWS,
) -> list[html.Div]:
    """Build the result gutter lines."""
    result_lines = result_lines or []
    total_rendered_rows = 0
    for line in result_lines:
        if isinstance(line, dict):
            total_rendered_rows += int(line.get("row_span", 1) or 1)
        else:
            total_rendered_rows += 1
    rows = max(min_rows, total_rendered_rows)
    label_lengths = []
    for line in result_lines:
        if isinstance(line, dict):
            label_lengths.append(len(str(line.get("name", "") or "")))
    name_col_width = max(72, min(220, max(label_lengths or [0]) * 9 + 16))
    children = []
    rendered_rows = 0
    for line in result_lines:
        if isinstance(line, dict):
            kind = str(line.get("kind", "") or "")
            row_span = int(line.get("row_span", 1) or 1)
            name = str(line.get("name", "") or "")
            value = str(line.get("value", "") or "")
            count = str(line.get("count", "") or "")
            is_error = bool(line.get("error"))
            title_text = " | ".join(part for part in [name, value, count] if part)
            matrix_rows = line.get("matrix", [])
        else:
            text = str(line or "")
            kind = ""
            row_span = 1
            is_error = text.startswith("Error:")
            name = ""
            value = text
            count = ""
            title_text = text
            matrix_rows = []
        row_height = f"{row_span * int(NOTEBOOK_LINE_HEIGHT[:-2])}px"
        if kind == "matrix":
            value_component = html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                cell_value,
                                style={
                                    "height": NOTEBOOK_LINE_HEIGHT,
                                    "lineHeight": NOTEBOOK_LINE_HEIGHT,
                                    "padding": "0 8px",
                                    "borderBottom": "1px solid rgba(226,232,240,0.8)" if r_index < len(matrix_rows) - 1 else "none",
                                    "borderRight": "1px solid rgba(226,232,240,0.8)" if c_index < len(row_values) - 1 else "none",
                                    "textAlign": "right",
                                    "fontWeight": "600",
                                    "color": "#001f41",
                                },
                            )
                            for c_index, cell_value in enumerate(row_values)
                        ],
                        style={"display": "grid", "gridTemplateColumns": "repeat(" + str(len(row_values)) + ", minmax(0, 1fr))"},
                    )
                    for r_index, row_values in enumerate(matrix_rows)
                ],
                style={"display": "grid", "gridAutoRows": NOTEBOOK_LINE_HEIGHT, "borderRight": "1px solid #e2e8f0"},
            )
        else:
            value_component = html.Div(
                value,
                title="Value",
                style={
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                    "padding": "0 8px",
                    "height": row_height,
                    "lineHeight": row_height,
                    "borderRight": "1px solid #e2e8f0",
                    "color": "#b42318" if is_error else "#001f41" if value else "#b0bec5",
                    "fontWeight": "600",
                },
            )
        children.append(
            html.Div(
                [
                    html.Div(
                        name,
                        title="Data",
                        style={
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "whiteSpace": "nowrap",
                            "padding": "0 8px",
                            "height": row_height,
                            "lineHeight": row_height,
                            "borderRight": "1px solid #e2e8f0",
                            "color": "#475467" if not is_error else "#b42318",
                            "fontWeight": "600",
                            "alignSelf": "stretch",
                        },
                    ),
                    value_component,
                    html.Div(
                        count,
                        title="Count",
                        style={
                            "overflow": "hidden",
                            "textOverflow": "ellipsis",
                            "whiteSpace": "nowrap",
                            "padding": "0 8px",
                            "height": row_height,
                            "lineHeight": row_height,
                            "textAlign": "right",
                            "color": "#64748b" if count else "#98a2b3",
                            "fontWeight": "600",
                            "alignSelf": "stretch",
                        },
                    ),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": f"{name_col_width}px minmax(0, 1fr) 56px",
                    "columnGap": "0",
                    "height": row_height,
                    "lineHeight": NOTEBOOK_LINE_HEIGHT,
                    "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                    "fontSize": "13px",
                    "borderBottom": "1px solid #e2e8f0",
                    "alignItems": "center",
                },
                title=title_text,
            )
        )
        rendered_rows += row_span
    for _ in range(rows - rendered_rows):
        children.append(
            html.Div(
                [
                    html.Div("", style={"padding": "0 8px", "height": NOTEBOOK_LINE_HEIGHT, "lineHeight": NOTEBOOK_LINE_HEIGHT, "borderRight": "1px solid #e2e8f0"}),
                    html.Div("", style={"padding": "0 8px", "height": NOTEBOOK_LINE_HEIGHT, "lineHeight": NOTEBOOK_LINE_HEIGHT, "borderRight": "1px solid #e2e8f0"}),
                    html.Div("", style={"padding": "0 8px", "height": NOTEBOOK_LINE_HEIGHT, "lineHeight": NOTEBOOK_LINE_HEIGHT, "textAlign": "right"}),
                ],
                style={
                    "display": "grid",
                    "gridTemplateColumns": f"{name_col_width}px minmax(0, 1fr) 56px",
                    "columnGap": "0",
                    "height": NOTEBOOK_LINE_HEIGHT,
                    "lineHeight": NOTEBOOK_LINE_HEIGHT,
                    "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                    "fontSize": "13px",
                    "borderBottom": "1px solid #e2e8f0",
                    "alignItems": "center",
                },
            )
        )
    return children


def build_notebook_execution_view(execution_blocks: list[dict] | None = None) -> list[html.Div]:
    """Render aligned source/result execution blocks for a code cell."""
    execution_blocks = execution_blocks or []
    children: list[html.Div] = []
    for block in execution_blocks:
        source_span = max(1, int(block.get("source_span", 1) or 1))
        result_span = max(1, int(block.get("result_span", 1) or 1))
        block_span = max(source_span, result_span)
        block_height = f"{block_span * int(NOTEBOOK_LINE_HEIGHT[:-2])}px"
        kind = str(block.get("result_kind", "") or "")
        source_component = html.Pre(
            str(block.get("source", "") or ""),
            style={
                "margin": "0",
                "padding": "8px 12px",
                "minHeight": block_height,
                "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                "fontSize": "13px",
                "lineHeight": NOTEBOOK_LINE_HEIGHT,
                "whiteSpace": "pre-wrap",
                "color": "#102a43",
                "background": "transparent",
            },
        )
        if kind == "matrix":
            matrix_rows = block.get("matrix", [])
            result_component = html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                cell_value,
                                style={
                                    "height": NOTEBOOK_LINE_HEIGHT,
                                    "lineHeight": NOTEBOOK_LINE_HEIGHT,
                                    "padding": "0 8px",
                                    "borderBottom": "1px solid rgba(226,232,240,0.8)" if r_index < len(matrix_rows) - 1 else "none",
                                    "borderRight": "1px solid rgba(226,232,240,0.8)" if c_index < len(row_values) - 1 else "none",
                                    "textAlign": "right",
                                    "fontWeight": "600",
                                    "color": "#001f41",
                                },
                            )
                            for c_index, cell_value in enumerate(row_values)
                        ],
                        style={"display": "grid", "gridTemplateColumns": "repeat(" + str(len(row_values)) + ", minmax(0, 1fr))"},
                    )
                    for r_index, row_values in enumerate(matrix_rows)
                ],
                style={
                    "display": "grid",
                    "gridAutoRows": NOTEBOOK_LINE_HEIGHT,
                    "border": "1px solid #e2e8f0",
                    "background": "#ffffff",
                    "minHeight": block_height,
                },
            )
        else:
            color = "#b42318" if block.get("error") else "#001f41" if block.get("value") else "#98a2b3"
            result_component = html.Div(
                str(block.get("value", "") or ""),
                style={
                    "padding": "8px 12px",
                    "minHeight": block_height,
                    "fontFamily": "'JetBrains Mono', 'Fira Code', 'Consolas', monospace",
                    "fontSize": "13px",
                    "lineHeight": NOTEBOOK_LINE_HEIGHT,
                    "color": color,
                    "fontWeight": "600",
                    "whiteSpace": "pre-wrap",
                    "background": "#ffffff",
                    "border": "1px solid #e2e8f0",
                },
            )
        children.append(
            html.Div(
                [source_component, result_component],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "minmax(0, 1fr) 440px",
                    "gap": "12px",
                    "alignItems": "start",
                    "borderBottom": "1px solid rgba(226,232,240,0.8)",
                },
            )
        )
    if not children:
        children.append(html.Div(style={"minHeight": NOTEBOOK_LINE_HEIGHT}))
    return children


def _empty_nb_figure() -> go.Figure:
    """Return a blank placeholder figure for the notebook side plot."""
    fig = go.Figure()
    fig.update_layout(
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(200,210,220,0.5)",
            zeroline=True,
            zerolinecolor="rgba(100,116,139,0.45)",
            zerolinewidth=2,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(200,210,220,0.5)",
            zeroline=True,
            zerolinecolor="rgba(100,116,139,0.45)",
            zerolinewidth=2,
        ),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=50, r=20, t=30, b=50),
        annotations=[dict(
            text="Define arrays in the notebook<br>then select x / y variables above",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font=dict(size=13, color="#94a3b8"),
        )],
    )
    return fig


def build_notebook_sidebar_controls(cells: list) -> html.Div:
    """
    Build the notebook sidebar: examples dropdown, action buttons, and all hidden stores.
    Placed in the left blue sidebar panel when the Calculation Notebook tab is active.
    """
    snippet_options = []
    for group_label, keys in NOTEBOOK_SNIPPET_GROUPS.items():
        snippet_options.append({"label": f"── {group_label} ──", "value": f"__group__{group_label}", "disabled": True})
        for k in keys:
            if k in NOTEBOOK_SNIPPETS:
                snippet_options.append({"label": f"  {k}", "value": k})

    _divider = html.Hr(style={
        "border": "none", "borderTop": "1px solid rgba(255,255,255,0.15)", "margin": "10px 0",
    })

    return html.Div([
        # ── hidden stores (must always be in DOM) ─────────────────────────────
        dcc.Download(id=NOTEBOOK_DOWNLOAD_ID),
        dcc.Store(id="notebook-monaco-sync-dummy"),
        dcc.Store(id="notebook-var-refresh-dummy"),
        dcc.Store(id="notebook-markdown-preview-dummy"),
        dcc.Store(id="notebook-md-panel-dummy"),
        dcc.Store(id="notebook-external-sync", data=None),
        dcc.Store(id="notebook-save-sync", data=None),
        dcc.Store(id="notebook-cells-store", data=cells),
        dcc.Store(id="nb-op-sync", data=None),
        dcc.Store(id="nb-cell-run-trigger", data=None),
        dcc.Store(id="notebook-fn-dummy"),
        dcc.Input(id="notebook-auto-update-state", type="hidden", value="on"),

        # ── Examples ──────────────────────────────────────────────────────────
        html.Span("EXAMPLES", className="sidebar-projects-title"),
        dcc.Dropdown(
            id="notebook-example-select",
            options=snippet_options,
            value=None,
            placeholder="Select an example…",
            clearable=True,
            optionHeight=34,
            maxHeight=600,
            style={"fontSize": "13px", "marginTop": "6px", "marginBottom": "6px"},
        ),
        html.Button("Insert Example", id="notebook-insert-example-btn", n_clicks=0,
                    className="sidebar-notebook-btn sidebar-notebook-btn--primary"),

        _divider,

        # ── Run & Auto-update ─────────────────────────────────────────────────
        html.Span("RUN", className="sidebar-projects-title"),
        html.Button("▶  Run All  (Ctrl+Enter)", id="notebook-run-btn", n_clicks=0,
                    className="sidebar-notebook-btn sidebar-notebook-btn--primary"),
        dcc.Checklist(
            id="notebook-auto-update",
            options=[{"label": " Auto update", "value": "auto"}],
            value=["auto"],
            inline=True,
            inputStyle={"marginRight": "6px", "cursor": "pointer"},
            labelStyle={"display": "inline-flex", "alignItems": "center",
                        "fontSize": "13px", "color": "rgba(255,255,255,0.85)",
                        "cursor": "pointer", "marginTop": "6px"},
        ),

        _divider,

        # ── File actions ──────────────────────────────────────────────────────
        html.Span("FILE", className="sidebar-projects-title"),
        dcc.Upload(
            html.Button("Load (.json / .txt)", className="sidebar-notebook-btn",
                        style={"width": "100%", "textAlign": "left"}),
            id="notebook-load-upload",
            accept=".json,.txt",
            multiple=False,
        ),
        html.Button("Save (.json)", id="notebook-save-btn", n_clicks=0,
                    className="sidebar-notebook-btn"),
        dcc.ConfirmDialogProvider(
            children=html.Button("Clear All", className="sidebar-notebook-btn sidebar-notebook-btn--danger"),
            id="notebook-clear-confirm-provider",
            message="Clear all notebook content? This cannot be undone.",
        ),

        _divider,

        # ── Extras ────────────────────────────────────────────────────────────
        html.Span("TOOLS", className="sidebar-projects-title"),
        html.Button("≡  Functions", id="notebook-fn-btn", n_clicks=0,
                    className="sidebar-notebook-btn"),
        html.Button("Markdown Help", id="notebook-md-help-btn", n_clicks=0,
                    className="sidebar-notebook-btn"),
        html.Button("✦  AI Settings", id="nb-settings-open-btn", n_clicks=0,
                    className="sidebar-notebook-btn sidebar-notebook-btn--ai"),
    ])


def build_calculation_notebook(state: dict | None = None) -> html.Div:
    """Build the calculation notebook tab content."""
    state = state or default_notebook_state()
    text = state.get("text", "")
    array_vars = state.get("array_variables", {})
    arr_options = [{"label": k, "value": k} for k in sorted(array_vars)]
    cells = state.get("cells") or [default_notebook_cell()]

    return html.Div(
        [
            # ── AI settings modal ────────────────────────────────────────────
            html.Div(
                id="nb-settings-modal",
                children=[
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span("AI Settings", style={
                                        "fontWeight": "700", "fontSize": "15px",
                                        "color": "#1e1b4b",
                                    }),
                                    html.Button("", id="nb-settings-close-btn",
                                        n_clicks=0,
                                        className="opview-image-close-btn"),
                                ],
                                style={"display": "flex", "justifyContent": "space-between",
                                       "alignItems": "center", "marginBottom": "16px"},
                            ),
                            html.Label("Provider", style={"fontSize": "12px", "fontWeight": "600",
                                                           "color": "#374151", "display": "block",
                                                           "marginBottom": "6px"}),
                            dcc.RadioItems(
                                id="nb-settings-provider",
                                options=[
                                    {"label": " Anthropic (Claude Haiku)", "value": "anthropic"},
                                    {"label": " OpenAI (GPT-4o-mini)",      "value": "openai"},
                                    {"label": " Google Gemini (gemini-2.0-flash)", "value": "gemini"},
                                    {"label": " GitHub Models (auto gh auth)", "value": "github"},
                                ],
                                value="anthropic",
                                style={"fontSize": "13px", "marginBottom": "14px"},
                                inputStyle={"marginRight": "6px"},
                            ),
                            html.Label(
                                id="nb-settings-key-label",
                                children="API Key",
                                style={"fontSize": "12px", "fontWeight": "600",
                                       "color": "#374151", "display": "block",
                                       "marginBottom": "6px"},
                            ),
                            dcc.Input(
                                id="nb-settings-apikey",
                                type="password",
                                placeholder="Paste your API key here…",
                                value=_setting_get("ANTHROPIC_API_KEY") or _setting_get("OPENAI_API_KEY"),
                                style={
                                    "width": "100%", "fontSize": "13px",
                                    "padding": "7px 10px", "borderRadius": "8px",
                                    "border": "1px solid #d1d5db", "boxSizing": "border-box",
                                    "marginBottom": "14px",
                                },
                            ),
                            html.Div(
                                [
                                    html.Button("Save", id="nb-settings-save-btn", n_clicks=0,
                                        style={"background": "#7c3aed", "color": "#fff",
                                               "border": "none", "borderRadius": "8px",
                                               "padding": "7px 20px", "fontSize": "13px",
                                               "fontWeight": "600", "cursor": "pointer"}),
                                    html.Span(id="nb-settings-status",
                                              style={"fontSize": "12px", "color": "#6b7280",
                                                     "marginLeft": "10px"}),
                                ],
                                style={"display": "flex", "alignItems": "center"},
                            ),
                        ],
                        style={
                            "background": "#fff",
                            "borderRadius": "14px",
                            "padding": "24px",
                            "width": "380px",
                            "boxShadow": "0 20px 60px rgba(0,0,0,0.18)",
                            "position": "relative",
                        },
                    ),
                ],
                style={
                    "display": "none",
                    "position": "fixed", "inset": "0",
                    "background": "rgba(0,0,0,0.45)",
                    "zIndex": "9999",
                    "justifyContent": "center",
                    "alignItems": "center",
                },
            ),
            # ── hidden inputs kept for backward compat (Monaco sync, var decorations) ──
            dcc.Textarea(id="notebook-textarea", value=text, style={"display": "none"}),
            dcc.Textarea(id="notebook-live-text", value=text, style={"display": "none"}),
            dcc.Textarea(id="notebook-run-text",  value=text, style={"display": "none"}),
            html.Div(id="notebook-results",       style={"display": "none"}),
            html.Div(id="notebook-vim-statusbar", style={"display": "none"}),
            # ── main row: cells + side plot ──────────────────────────────────
            html.Div(
                [
            # ── cells column ─────────────────────────────────────────────────
            html.Div(
                [
                    html.Div(
                        build_cells_container(cells),
                        id="notebook-cells-container",
                        style={"width": "100%"},
                    ),
                ],
                style={
                    "flex": "1 1 auto",
                    "minWidth": f"calc({RESULTS_GUTTER_WIDTH} + 300px)",
                    "maxWidth": NOTEBOOK_SHEET_WIDTH,
                    "padding": "14px",
                    "overflowY": "visible",
                    "display": "flex",
                    "flexDirection": "column",
                },
            ),
            # ── plots panel ──────────────────────────────────────────────────
            html.Div(
                [
                    # panel header: title + global controls
                    html.Div(
                        [
                            html.Span("Plots", style={"fontSize": "12px", "fontWeight": "700",
                                                       "textTransform": "uppercase", "letterSpacing": "0.08em",
                                                       "color": "#475467"}),
                            html.Span("Call plot(x, y) in the notebook",
                                      style={"fontSize": "11px", "color": "#94a3b8", "marginLeft": "10px"}),
                            html.Div(style={"flex": "1"}),
                            html.Div("Font", style={"fontSize": "11px", "fontWeight": "700",
                                                     "color": "#475467", "alignSelf": "center",
                                                     "marginRight": "4px"}),
                            dcc.Input(
                                id="nb-global-font-size",
                                type="number", value=14, min=8, max=28, step=1,
                                style={"fontSize": "12px", "width": "50px", "padding": "3px 5px",
                                       "border": "1px solid rgba(100,116,139,0.35)", "borderRadius": "6px",
                                       "marginRight": "10px",
                                       "fontFamily": "'Inter','Segoe UI',system-ui,sans-serif"},
                            ),
                            html.Div("Line W", style={"fontSize": "11px", "fontWeight": "700",
                                                       "color": "#475467", "alignSelf": "center",
                                                       "marginRight": "4px"}),
                            dcc.Input(
                                id="nb-global-line-width",
                                type="number", value=2, min=0.5, max=8, step=0.5,
                                style={"fontSize": "12px", "width": "50px", "padding": "3px 5px",
                                       "border": "1px solid rgba(100,116,139,0.35)", "borderRadius": "6px",
                                       "fontFamily": "'Inter','Segoe UI',system-ui,sans-serif"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center", "flexWrap": "wrap",
                               "gap": "4px", "borderBottom": "1px solid rgba(100,116,139,0.12)",
                               "paddingBottom": "10px", "marginBottom": "10px"},
                    ),
                    # notebook-driven plots (from plot() calls) — updated by notebook-state
                    html.Div(id="notebook-auto-plots", style={"flex": "0 0 auto"}),
                    # quick plots (user-created) — updated by selector-specs only
                    html.Div(id="notebook-plots-panel", style={"overflow": "visible", "flex": "0 0 auto"}),
                    html.Button(
                        "+ New Plot",
                        id="nb-plot-new-btn",
                        n_clicks=0,
                        style={
                            "fontSize": "13px", "padding": "8px 12px",
                            "background": "rgba(124,58,237,0.08)",
                            "border": "1px solid rgba(124,58,237,0.24)",
                            "borderRadius": "8px", "cursor": "pointer",
                            "color": "#6d28d9", "fontWeight": "700",
                            "marginTop": "10px", "whiteSpace": "nowrap",
                        },
                    ),
                ],
                style={
                    "flex": "1 1 420px",
                    "minWidth": "420px",
                    "padding": "14px 16px",
                    "display": "flex",
                    "flexDirection": "column",
                    "background": "#ffffff",
                    "border": "1px solid rgba(100,116,139,0.18)",
                    "boxShadow": "0 4px 6px rgba(15,23,42,0.04), 0 10px 28px rgba(15,23,42,0.06)",
                },
            ),
                ],  # end flex row children
                style={
                    "display": "flex",
                    "alignItems": "flex-start",
                    "flexWrap": "wrap",
                    "gap": "14px",
                    "width": "100%",
                },
            ),  # end flex row
            # ── floating functions reference overlay ─────────────────────────
            build_fn_overlay(),
            build_markdown_help_overlay(),
        ],
        style={"padding": "16px 20px", "width": "100%", "overflowX": "auto", "background": "#ffffff"},
    )

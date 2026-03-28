/**
 * Autocomplete for the OPView calculation notebook textarea.
 * Triggers on any identifier prefix (≥1 char), shows a floating dropdown,
 * and completes on Tab / Enter / click. Escape or typing a non-match hides it.
 */
(function () {
  'use strict';

  // ── Completion catalogue ────────────────────────────────────────────────────
  // Each entry: { match: string to match, insert: text to insert, sig: display label }
  const COMPLETIONS = [
    // Trig
    { match: 'sin',       insert: 'sin(',       sig: 'sin(x)' },
    { match: 'cos',       insert: 'cos(',       sig: 'cos(x)' },
    { match: 'tan',       insert: 'tan(',       sig: 'tan(x)' },
    { match: 'asin',      insert: 'asin(',      sig: 'asin(x)' },
    { match: 'acos',      insert: 'acos(',      sig: 'acos(x)' },
    { match: 'atan',      insert: 'atan(',      sig: 'atan(x)' },
    { match: 'atan2',     insert: 'atan2(',     sig: 'atan2(y, x)' },
    { match: 'sinh',      insert: 'sinh(',      sig: 'sinh(x)' },
    { match: 'cosh',      insert: 'cosh(',      sig: 'cosh(x)' },
    { match: 'tanh',      insert: 'tanh(',      sig: 'tanh(x)' },
    // Math
    { match: 'exp',       insert: 'exp(',       sig: 'exp(x)' },
    { match: 'log',       insert: 'log(',       sig: 'log(x)  — natural log' },
    { match: 'log10',     insert: 'log10(',     sig: 'log10(x)' },
    { match: 'sqrt',      insert: 'sqrt(',      sig: 'sqrt(x)' },
    { match: 'abs',       insert: 'abs(',       sig: 'abs(x)' },
    { match: 'floor',     insert: 'floor(',     sig: 'floor(x)' },
    { match: 'ceil',      insert: 'ceil(',      sig: 'ceil(x)' },
    { match: 'round',     insert: 'round(',     sig: 'round(x)' },
    { match: 'hypot',     insert: 'hypot(',     sig: 'hypot(x, y)' },
    { match: 'min',       insert: 'min(',       sig: 'min(a, b)' },
    { match: 'max',       insert: 'max(',       sig: 'max(a, b)' },
    // Math helpers
    { match: 'sign',      insert: 'sign(',      sig: 'sign(x)  — -1, 0 or 1' },
    { match: 'log2',      insert: 'log2(',      sig: 'log2(x)' },
    { match: 'degrees',   insert: 'degrees(',   sig: 'degrees(x)  — rad→deg' },
    { match: 'radians',   insert: 'radians(',   sig: 'radians(x)  — deg→rad' },
    { match: 'clamp',     insert: 'clamp(',     sig: 'clamp(x, lo, hi)' },
    { match: 'lerp',      insert: 'lerp(',      sig: 'lerp(a, b, t)  — linear interp' },
    { match: 'factorial', insert: 'factorial(', sig: 'factorial(n)' },
    { match: 'gcd',       insert: 'gcd(',       sig: 'gcd(a, b)' },
    { match: 'lcm',       insert: 'lcm(',       sig: 'lcm(a, b)' },
    // Constants
    { match: 'pi',        insert: 'pi',         sig: 'pi  ≈ 3.14159' },
    { match: 'e',         insert: 'e',          sig: 'e   ≈ 2.71828' },
    { match: 'tau',       insert: 'tau',        sig: 'tau = 2*pi ≈ 6.28318' },
    { match: 'deg',       insert: 'deg',        sig: 'deg = pi/180  (multiply to convert)' },
    { match: 'inf',       insert: 'inf',        sig: 'inf = Infinity' },
    // Engineering
    { match: 'cfl_dt',            insert: 'cfl_dt(',            sig: 'cfl_dt(dx, u, cfl=1)' },
    { match: 'diffusion_dt',      insert: 'diffusion_dt(',      sig: 'diffusion_dt(dx, D, f=0.5)' },
    { match: 'fourier_number',    insert: 'fourier_number(',    sig: 'fourier_number(D, dt, dx)' },
    { match: 'peclet',            insert: 'peclet(',            sig: 'peclet(u, L, D)' },
    { match: 'cell_size',         insert: 'cell_size(',         sig: 'cell_size(L, N)' },
    { match: 'domain_points',     insert: 'domain_points(',     sig: 'domain_points(L, dx)' },
    { match: 'von_mises',         insert: 'von_mises(',         sig: 'von_mises(s11, s22, s33, s12=0, s23=0, s13=0)' },
    { match: 'shear_modulus',     insert: 'shear_modulus(',     sig: 'shear_modulus(E, nu)' },
    { match: 'lame_lambda',       insert: 'lame_lambda(',       sig: 'lame_lambda(E, nu)' },
    { match: 'hooke_1d',          insert: 'hooke_1d(',          sig: 'hooke_1d(E, eps)' },
    { match: 'hooke_3d',          insert: 'hooke_3d(',          sig: 'hooke_3d(E, nu, exx, eyy, ezz, exy=0, eyz=0, exz=0)' },
    { match: 'plane_strain',      insert: 'plane_strain(',      sig: 'plane_strain(E, nu, exx, eyy, exy=0)' },
    { match: 'plane_stress',      insert: 'plane_stress(',      sig: 'plane_stress(E, nu, exx, eyy, exy=0)' },
    { match: 'plane_stress_ezz',  insert: 'plane_stress_ezz(',  sig: 'plane_stress_ezz(nu, exx, eyy)' },
    // Vector
    { match: 'dot',       insert: 'dot(',       sig: 'dot(a, b)  — scalar dot product' },
    { match: 'cross',     insert: 'cross(',     sig: 'cross(a, b)  — 3-D cross product' },
    { match: 'norm',      insert: 'norm(',      sig: 'norm(v)  — Euclidean length' },
    { match: 'normalize', insert: 'normalize(', sig: 'normalize(v)  — unit vector' },
    { match: 'length',    insert: 'length(',    sig: 'length(v)  — same as norm' },
    // Matrix
    { match: 'det',       insert: 'det(',       sig: 'det(M)  — determinant' },
    { match: 'inv',       insert: 'inv(',       sig: 'inv(M)  — matrix inverse' },
    { match: 'transpose', insert: 'transpose(', sig: 'transpose(M)' },
    { match: 'trace',     insert: 'trace(',     sig: 'trace(M)  — sum of diagonal' },
    { match: 'rank',      insert: 'rank(',      sig: 'rank(M)' },
    { match: 'eig',       insert: 'eig(',       sig: 'eig(M)  — eigenvalues array' },
    // Builders
    { match: 'eye',       insert: 'eye(',       sig: 'eye(n)  — n×n identity matrix' },
    { match: 'zeros',     insert: 'zeros(',     sig: 'zeros(m, n)  — zero matrix / vector' },
    { match: 'ones',      insert: 'ones(',      sig: 'ones(m, n)  — ones matrix / vector' },
    { match: 'shape',     insert: 'shape(',     sig: 'shape(M)  — dimensions' },
    // Statistics
    { match: 'sum',     insert: 'sum(',     sig: 'sum(v)  — array sum' },
    { match: 'mean',    insert: 'mean(',    sig: 'mean(v)  — arithmetic mean' },
    { match: 'std',     insert: 'std(',     sig: 'std(v)  — standard deviation' },
    { match: 'variance',insert: 'variance(',sig: 'variance(v)' },
    { match: 'median',  insert: 'median(',  sig: 'median(v)' },
    { match: 'prod',    insert: 'prod(',    sig: 'prod(v)  — array product' },
    { match: 'cumsum',  insert: 'cumsum(',  sig: 'cumsum(v)  — cumulative sum' },
    { match: 'diff',    insert: 'diff(',    sig: 'diff(v)  — consecutive differences' },
    { match: 'diff2',   insert: 'diff2(',   sig: 'diff2(v, n=1)  — n-th order differences' },
    { match: 'cov',     insert: 'cov(',     sig: 'cov(x, y)  — covariance' },
    { match: 'histogram',insert:'histogram(', sig:'histogram(v, bins=10)  — bin counts' },
    { match: 'mode',    insert: 'mode(',    sig: 'mode(v)  — most frequent value' },
    // Loop helpers
    { match: 'range',     insert: 'range(',     sig: 'range(stop) / range(start, stop, step)  — integer range' },
    { match: 'enumerate', insert: 'enumerate(', sig: 'enumerate(v, start=0)  — (index, value) pairs' },
    { match: 'zip',       insert: 'zip(',       sig: 'zip(a, b)  — pair elements from two iterables' },
    { match: 'len',       insert: 'len(',       sig: 'len(v)  — length of array or list' },
    // Array builders
    { match: 'linspace', insert: 'linspace(', sig: 'linspace(start, stop, num)' },
    { match: 'arange',   insert: 'arange(',   sig: 'arange(start, stop, step)' },
    { match: 'diag',     insert: 'diag(',     sig: 'diag(v)  — diagonal matrix from vector' },
    { match: 'flatten',  insert: 'flatten(',  sig: 'flatten(M)  — flatten to 1-D' },
    { match: 'outer',    insert: 'outer(',    sig: 'outer(a, b)  — outer product' },
    { match: 'vstack',   insert: 'vstack(',   sig: 'vstack(a, b)  — stack arrays row-wise' },
    { match: 'hstack',   insert: 'hstack(',   sig: 'hstack(a, b)  — stack arrays column-wise' },
    { match: 'meshgrid', insert: 'meshgrid(', sig: 'meshgrid(x, y)  — 2-D coordinate grids' },
    // Linear algebra extras
    { match: 'solve',    insert: 'solve(',    sig: 'solve(A, b)  — linear system Ax=b' },
    { match: 'lstsq',    insert: 'lstsq(',    sig: 'lstsq(A, b)  — least squares' },
    { match: 'svd',      insert: 'svd(',      sig: 'svd(M)  — singular values' },
    { match: 'norm_p',   insert: 'norm_p(',   sig: 'norm_p(v, p=2)  — p-norm' },
    // Dimensionless numbers
    { match: 'reynolds',       insert: 'reynolds(',       sig: 'reynolds(rho, u, L, mu)' },
    { match: 'mach',           insert: 'mach(',           sig: 'mach(u, a)  — Mach number' },
    { match: 'prandtl',        insert: 'prandtl(',        sig: 'prandtl(mu, cp, k)' },
    { match: 'nusselt_dittus', insert: 'nusselt_dittus(', sig: 'nusselt_dittus(Re, Pr, heating=True)' },
    { match: 'biot',           insert: 'biot(',           sig: 'biot(h, L, k)  — Biot number' },
    { match: 'fourier_thermal',insert: 'fourier_thermal(',sig: 'fourier_thermal(alpha, t, L)  — Fourier number' },
    { match: 'lewis',          insert: 'lewis(',          sig: 'lewis(alpha, D)  — Lewis number' },
    { match: 'weber',          insert: 'weber(',          sig: 'weber(rho, u, L, sigma)  — Weber number' },
    { match: 'stokes',         insert: 'stokes(',         sig: 'stokes(rho_p, rho_f, d, mu)  — Stokes settling' },
    { match: 'grashof',        insert: 'grashof(',        sig: 'grashof(g, beta, dT, L, nu)  — Grashof number' },
    // Special math
    { match: 'erf',     insert: 'erf(',     sig: 'erf(x)  — error function' },
    { match: 'erfc',    insert: 'erfc(',    sig: 'erfc(x)  — complementary error function' },
    { match: 'gamma',   insert: 'gamma(',   sig: 'gamma(x)  — gamma function' },
    { match: 'lgamma',  insert: 'lgamma(',  sig: 'lgamma(x)  — log-gamma' },
    { match: 'beta',    insert: 'beta(',    sig: 'beta(a, b)  — beta function' },
    // Sorting / array ops
    { match: 'sort',         insert: 'sort(',         sig: 'sort(v)  — sorted copy' },
    { match: 'argsort',      insert: 'argsort(',      sig: 'argsort(v)  — sort indices' },
    { match: 'unique',       insert: 'unique(',       sig: 'unique(v)  — unique values' },
    { match: 'flip',         insert: 'flip(',         sig: 'flip(v)  — reverse array' },
    { match: 'clip',         insert: 'clip(',         sig: 'clip(v, lo, hi)  — clamp elements' },
    { match: 'roll',         insert: 'roll(',         sig: 'roll(v, n)  — circular shift' },
    { match: 'repeat',       insert: 'repeat(',       sig: 'repeat(v, n)  — repeat elements' },
    { match: 'tile',         insert: 'tile(',         sig: 'tile(v, n)  — tile array' },
    { match: 'full',         insert: 'full(',         sig: 'full(n, val)  — array filled with val' },
    { match: 'where',        insert: 'where(',        sig: 'where(cond, x, y)  — elementwise select' },
    { match: 'concat',       insert: 'concat(',       sig: 'concat(a, b)  — concatenate arrays' },
    { match: 'reshape',      insert: 'reshape(',      sig: 'reshape(v, rows, cols)  — reshape array' },
    { match: 'append',       insert: 'append(',       sig: 'append(v, x)  — append element/array' },
    // Interpolation
    { match: 'interp',   insert: 'interp(',   sig: 'interp(x, xp, fp)  — piecewise linear interp' },
    { match: 'polyfit',  insert: 'polyfit(',  sig: 'polyfit(x, y, deg)  — polynomial fit coeffs' },
    { match: 'polyval',  insert: 'polyval(',  sig: 'polyval(p, x)  — evaluate polynomial' },
    // Calculus
    { match: 'gradient',  insert: 'gradient(',  sig: 'gradient(v, dx=1)  — numerical gradient' },
    { match: 'trapz',     insert: 'trapz(',     sig: 'trapz(y, x=null)  — trapezoidal integral' },
    { match: 'cumtrapz',  insert: 'cumtrapz(',  sig: 'cumtrapz(y, x=null)  — cumulative trapz' },
    // FFT / signal
    { match: 'fft',      insert: 'fft(',      sig: 'fft(v)  — real FFT magnitudes' },
    { match: 'ifft',     insert: 'ifft(',     sig: 'ifft(v)  — inverse FFT' },
    { match: 'fftfreq',  insert: 'fftfreq(',  sig: 'fftfreq(n, dt=1)  — FFT frequency bins' },
    { match: 'fftshift', insert: 'fftshift(', sig: 'fftshift(v)  — center DC component' },
    { match: 'real',     insert: 'real(',     sig: 'real(v)  — real parts' },
    { match: 'imag',     insert: 'imag(',     sig: 'imag(v)  — imaginary parts' },
    { match: 'angle',    insert: 'angle(',    sig: 'angle(v)  — phase angles (rad)' },
    // More statistics
    { match: 'percentile',  insert: 'percentile(',  sig: 'percentile(v, p)  — p-th percentile' },
    { match: 'quantile',    insert: 'quantile(',    sig: 'quantile(v, q)  — q in [0,1]' },
    { match: 'corrcoef',    insert: 'corrcoef(',    sig: 'corrcoef(x, y)  — Pearson correlation' },
    { match: 'zscore',      insert: 'zscore(',      sig: 'zscore(v)  — standardise to z-scores' },
    { match: 'norm01',      insert: 'norm01(',      sig: 'norm01(v)  — normalise to [0, 1]' },
    // More linear algebra
    { match: 'pinv',          insert: 'pinv(',          sig: 'pinv(M)  — pseudo-inverse' },
    { match: 'cond',          insert: 'cond(',          sig: 'cond(M)  — condition number' },
    { match: 'matrix_power',  insert: 'matrix_power(',  sig: 'matrix_power(M, n)  — M^n' },
    { match: 'kron',          insert: 'kron(',          sig: 'kron(A, B)  — Kronecker product' },
    { match: 'cholesky',      insert: 'cholesky(',      sig: 'cholesky(A)  — Cholesky factor L' },
    // Alloy composition
    { match: 'wt_to_mol',  insert: 'wt_to_mol(',  sig: 'wt_to_mol(wt, M)         — wt% array → mole fractions' },
    { match: 'wt_to_mol2', insert: 'wt_to_mol2(', sig: 'wt_to_mol2(wt_B, M_A, M_B) — binary scan, wt_B can be array' },
    { match: 'mol_to_wt', insert: 'mol_to_wt(', sig: 'mol_to_wt(x, M)   — mole fractions → wt% (sums to 100)' },
    { match: 'qr',            insert: 'qr(',            sig: 'qr(A)  — QR decomposition [Q, R]' },
    { match: 'eig_full',      insert: 'eig_full(',      sig: 'eig_full(M)  — [eigenvalues, eigenvectors]' },
    // Physical constants
    { match: 'g_n',      insert: 'g_n',      sig: 'g_n   = 9.80665 m/s²  (standard gravity)' },
    { match: 'c_0',      insert: 'c_0',      sig: 'c_0   = 2.998e8 m/s   (speed of light)' },
    { match: 'R_gas',    insert: 'R_gas',    sig: 'R_gas = 8.314 J/mol·K (gas constant)' },
    { match: 'k_B',      insert: 'k_B',      sig: 'k_B   = 1.381e-23 J/K (Boltzmann)' },
    { match: 'N_A',      insert: 'N_A',      sig: 'N_A   = 6.022e23 /mol  (Avogadro)' },
    { match: 'h_p',      insert: 'h_p',      sig: 'h_p   = 6.626e-34 J·s  (Planck)' },
    { match: 'sigma_SB', insert: 'sigma_SB', sig: 'sigma_SB = 5.67e-8 W/m²K⁴ (Stefan-Boltzmann)' },
    // Units
    { match: 'nm',  insert: 'nm',  sig: 'nm   = 1e-9 m' },
    { match: 'um',  insert: 'um',  sig: 'um   = 1e-6 m' },
    { match: 'mm',  insert: 'mm',  sig: 'mm   = 1e-3 m' },
    { match: 'cm',  insert: 'cm',  sig: 'cm   = 1e-2 m' },
    { match: 'm',   insert: 'm',   sig: 'm    = 1 m  (metre)' },
    { match: 'km',  insert: 'km',  sig: 'km   = 1e3 m' },
    { match: 'GPa', insert: 'GPa', sig: 'GPa  = 1e9 Pa' },
    { match: 'MPa', insert: 'MPa', sig: 'MPa  = 1e6 Pa' },
    { match: 'kPa', insert: 'kPa', sig: 'kPa  = 1e3 Pa' },
    { match: 'Pa',  insert: 'Pa',  sig: 'Pa   = 1 Pa' },
    { match: 'sec',   insert: 'sec',   sig: 'sec   = 1 s' },
    { match: 'hour',  insert: 'hour',  sig: 'hour  = 3600 s' },
    { match: 'day',   insert: 'day',   sig: 'day   = 86400 s' },
    { match: 'week',  insert: 'week',  sig: 'week  = 604800 s' },
    { match: 'month', insert: 'month', sig: 'month = 2592000 s  (30 days)' },
    { match: 'ms',  insert: 'ms',  sig: 'ms   = 1e-3 s' },
    { match: 'us',  insert: 'us',  sig: 'us   = 1e-6 s' },
    { match: 'min', insert: 'min', sig: 'min  = 60 s  (also: min(a,b))' },
    { match: 'h',   insert: 'h',   sig: 'h    = 3600 s' },
    { match: 'kg',  insert: 'kg',  sig: 'kg   = 1 kg (kilogram)' },
    { match: 'N',   insert: 'N',   sig: 'N    = 1 N  (newton)' },
    { match: 'kN',  insert: 'kN',  sig: 'kN   = 1e3 N' },
    { match: 'MN',  insert: 'MN',  sig: 'MN   = 1e6 N' },
    { match: 'J',   insert: 'J',   sig: 'J    = 1 J  (joule)' },
    { match: 'kJ',  insert: 'kJ',  sig: 'kJ   = 1e3 J' },
    { match: 'MJ',  insert: 'MJ',  sig: 'MJ   = 1e6 J' },
    { match: 'W',   insert: 'W',   sig: 'W    = 1 W  (watt)' },
    { match: 'kW',  insert: 'kW',  sig: 'kW   = 1e3 W' },
    { match: 'MW',  insert: 'MW',  sig: 'MW   = 1e6 W' },
    { match: 'Hz',  insert: 'Hz',  sig: 'Hz   = 1 Hz (hertz)' },
    { match: 'kHz', insert: 'kHz', sig: 'kHz  = 1e3 Hz' },
    { match: 'MHz', insert: 'MHz', sig: 'MHz  = 1e6 Hz' },
    { match: 'bar',  insert: 'bar',  sig: 'bar  = 1e5 Pa' },
    { match: 'mbar', insert: 'mbar', sig: 'mbar = 100 Pa' },
    { match: 'kWh',  insert: 'kWh',  sig: 'kWh  = 3.6e6 J' },
    { match: 'atm',  insert: 'atm',  sig: 'atm  = 101325 Pa  (std atmosphere)' },
    { match: 'L',    insert: 'L',    sig: 'L    = 1e-3 m³  (litre)' },
    { match: 'mu_0',  insert: 'mu_0',  sig: 'mu_0  = 1.257e-6 H/m  (vacuum permeability)' },
    { match: 'eps_0', insert: 'eps_0', sig: 'eps_0 = 8.854e-12 F/m  (vacuum permittivity)' },
  ];

  const STATIC_MATCH_WORDS = new Set(COMPLETIONS.map(c => c.match));

  // ── State ───────────────────────────────────────────────────────────────────
  let popup    = null;
  let textarea = null;
  let matches  = [];
  let active   = -1;

  // ── Popup DOM ───────────────────────────────────────────────────────────────
  function ensurePopup() {
    if (popup) return popup;
    popup = Object.assign(document.createElement('div'), { id: 'nb-ac-popup' });
    Object.assign(popup.style, {
      position:   'fixed',
      zIndex:     '99999',
      background: '#fff',
      border:     '1px solid #94a3b8',
      borderRadius: '10px',
      boxShadow:  '0 10px 32px rgba(15,23,42,.18)',
      maxHeight:  '240px',
      overflowY:  'auto',
      minWidth:   '280px',
      maxWidth:   '520px',
      fontFamily: '"JetBrains Mono","Fira Code",Consolas,monospace',
      fontSize:   '13px',
      display:    'none',
      padding:    '4px 0',
    });
    document.body.appendChild(popup);
    return popup;
  }

  function hide() {
    if (popup) popup.style.display = 'none';
    matches = [];
    active  = -1;
  }

  // ── Cursor word ─────────────────────────────────────────────────────────────
  function wordBefore(ta) {
    const before = ta.value.slice(0, ta.selectionStart);
    const m = before.match(/([a-zA-Z_][a-zA-Z0-9_]*)$/);
    return m ? m[1] : '';
  }

  // ── User variables ──────────────────────────────────────────────────────────
  function userVars(text) {
    const vars = [];
    for (const line of (text || '').split('\n')) {
      const stripped = line.replace(/\/\/.*|#.*/g, '').trim();
      const m = stripped.match(/^([a-zA-Z_][a-zA-Z0-9_]*)\s*=/);
      if (m && !STATIC_MATCH_WORDS.has(m[1])) {
        vars.push({ match: m[1], insert: m[1], sig: m[1] + '  (variable)' });
      }
    }
    // Deduplicate
    const seen = new Set();
    return vars.filter(v => seen.has(v.match) ? false : (seen.add(v.match), true));
  }

  // ── Dropdown position ───────────────────────────────────────────────────────
  function dropdownPos(ta) {
    const rect     = ta.getBoundingClientRect();
    const cs       = window.getComputedStyle(ta);
    const lh       = parseFloat(cs.lineHeight)  || 34;
    const padTop   = parseFloat(cs.paddingTop)  || 18;
    const padLeft  = parseFloat(cs.paddingLeft) || 18;
    const charW    = parseFloat(cs.fontSize) * 0.605; // monospace estimate

    const text   = ta.value.slice(0, ta.selectionStart);
    const lines  = text.split('\n');
    const lineNo = lines.length - 1;
    const curLine = lines[lineNo];

    // x: start of the word being typed
    const wordStart = curLine.replace(/([a-zA-Z_][a-zA-Z0-9_]*)$/, '').length;

    const x = rect.left + padLeft + wordStart * charW;
    const y = rect.top  + padTop  + (lineNo + 1) * lh - ta.scrollTop;
    return { x, y };
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  function render(word) {
    const p = ensurePopup();
    p.innerHTML = '';

    matches.forEach((m, i) => {
      const el = document.createElement('div');
      Object.assign(el.style, {
        padding:    '6px 14px',
        cursor:     'pointer',
        whiteSpace: 'nowrap',
        overflow:   'hidden',
        textOverflow: 'ellipsis',
      });

      // Bold-highlight the typed prefix
      const hi = word.length;
      el.innerHTML =
        '<span style="color:#2563eb;font-weight:700">' + esc(m.sig.slice(0, hi)) + '</span>' +
        '<span style="color:#334155">'                 + esc(m.sig.slice(hi))    + '</span>';

      el.addEventListener('mouseover', () => setActive(i));
      el.addEventListener('mousedown', e => { e.preventDefault(); apply(matches[i]); });
      p.appendChild(el);
    });

    setActive(0);
  }

  function setActive(i) {
    if (!popup) return;
    const items = popup.querySelectorAll('div');
    items.forEach((el, idx) => {
      el.style.background = idx === i ? '#eff6ff' : '';
    });
    active = i;
    if (items[i]) items[i].scrollIntoView({ block: 'nearest' });
  }

  // ── Apply completion ────────────────────────────────────────────────────────
  function apply(m) {
    if (!textarea) return;
    const pos    = textarea.selectionStart;
    const val    = textarea.value;
    const before = val.slice(0, pos);
    const wMatch = before.match(/([a-zA-Z_][a-zA-Z0-9_]*)$/);
    if (!wMatch) return;

    const wordStart = pos - wMatch[1].length;
    const newVal    = val.slice(0, wordStart) + m.insert + val.slice(pos);
    const newPos    = wordStart + m.insert.length;

    // Use the native setter so React/Dash picks up the change
    const setter = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
    setter.call(textarea, newVal);
    textarea.setSelectionRange(newPos, newPos);
    textarea.dispatchEvent(new Event('input', { bubbles: true }));

    hide();
    textarea.focus();
  }

  // ── Escape HTML ─────────────────────────────────────────────────────────────
  function esc(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  // ── Show suggestions ────────────────────────────────────────────────────────
  function suggest(ta) {
    const word  = wordBefore(ta);
    if (word.length < 1) { hide(); return; }

    const lower = word.toLowerCase();
    const all   = [...COMPLETIONS, ...userVars(ta.value)];
    matches     = all.filter(c =>
      c.match.toLowerCase().startsWith(lower) && c.match !== word
    );

    if (!matches.length) { hide(); return; }

    render(word);

    const p        = ensurePopup();
    const { x, y } = dropdownPos(ta);
    p.style.left    = x + 'px';
    p.style.top     = y + 'px';
    p.style.display = 'block';

    // Keep within viewport
    requestAnimationFrame(() => {
      const r = p.getBoundingClientRect();
      if (r.right > window.innerWidth - 8)
        p.style.left = Math.max(4, window.innerWidth - r.width - 8) + 'px';
      if (r.bottom > window.innerHeight - 8)
        p.style.top  = (y - r.height - parseInt(window.getComputedStyle(ta).lineHeight || 34)) + 'px';
    });
  }

  // ── Event handlers ──────────────────────────────────────────────────────────
  function onInput() {
    textarea = this;
    suggest(this);
  }

  function onKeydown(e) {
    if (!popup || popup.style.display === 'none' || !matches.length) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActive((active + 1) % matches.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActive((active - 1 + matches.length) % matches.length);
    } else if (e.key === 'Tab') {
      e.preventDefault();
      if (active >= 0 && active < matches.length) apply(matches[active]);
    } else if (e.key === 'Enter') {
      // Only intercept Enter if the user navigated with arrows
      if (active > 0 || (active === 0 && matches.length === 1)) {
        e.preventDefault();
        apply(matches[active]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      hide();
    }
  }

  function onBlur() {
    // Delay so mousedown on the popup fires first
    setTimeout(hide, 160);
  }

  // ── Attach ──────────────────────────────────────────────────────────────────
  function attach(ta) {
    if (ta._acAttached) return;
    ta._acAttached = true;
    ta.addEventListener('input',   onInput);
    ta.addEventListener('keydown', onKeydown);
    ta.addEventListener('blur',    onBlur);
  }

  function tryAttach() {
    const ta = document.getElementById('notebook-textarea');
    if (ta) { attach(ta); return true; }
    return false;
  }

  if (!tryAttach()) {
    const obs = new MutationObserver(() => { if (tryAttach()) obs.disconnect(); });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  // Expose catalogue so Monaco completion provider can use it
  window._nbCompletions = COMPLETIONS;
})();

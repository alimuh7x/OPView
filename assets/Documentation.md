# OpenPhase Post-Processing Suite

## Overview
The OpenPhase Post-Processing Suite is an interactive application for inspecting simulation outputs through six work modes:

- **Single View** for detailed inspection of one active dataset.
- **Multi View** for side-by-side comparison across multiple selected files.
- **Custom Graph** for plotting trends from `TextData` files.
- **Formula Plot** for plotting and analysing mathematical formulas with interactive parameter sliders.
- **Calculation Notebook** for scientific and engineering calculations with 100+ built-in functions.
- **Initializations Explorer** for previewing OpenPhase microstructure initialization methods.

Use the **Documentation** link in the header to return to this guide at any time.

Supported visualization file types are: `.vtk`, `.vti`, `.vtp`, `.vtr`, `.vts`.

## Getting Started
1. In the **PROJECTS** sidebar, select one or more project entries to load data into the app context.
2. If your project is not listed, click **📂 Add Project Folder** and select the folder.
3. Choose the top tab based on your task:
   - **Single View** for one dataset.
   - **Multi View** for comparison.
   - **Custom Graph** for `TextData` analysis.
   - **Formula Plot** for plotting and analysing mathematical expressions.
   - **Calculation Notebook** for scientific and engineering computations.
   - **Initializations Explorer** for previewing microstructure initialization methods.
4. Use the relevant **ADD PANEL** selector to add the data type/panel you want to work with.
5. In **Custom Graph**, **+ Add Graph Panel** is active only after you select a folder that contains text data files (`.txt`, `.dat`, `.csv`).

## Common Viewer Controls
The main heatmap viewers (used in `Single View` and `Multi View`) share these controls:

<table style="width:100%; border-collapse:collapse;">
  <thead>
    <tr>
      <th style="border:1px solid #cfd6e4; padding:8px; text-align:left;">Control</th>
      <th style="border:1px solid #cfd6e4; padding:8px; text-align:left;">Outcome</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Select Folder</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Chooses the active project folder for that panel. The available file list updates to that folder.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Select File</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Chooses the VTK file used for rendering. The heatmap updates to the selected file.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Select Field</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Chooses the scalar/component to display. The rendered field and colorbar update.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Range:</strong> (<code>Min</code>, <code>Max</code>, and <strong>Reset</strong>)</td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Sets explicit value bounds. The heatmap contrast and clipping update immediately.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Range Selection on Map</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Enables range picking from map clicks. Selected range limits are applied to the current view.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>palette</strong> dropdown</td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Changes the color palette. The heatmap recolors with the selected palette.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Range slider</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Interactively narrows or widens the visible value interval. Values outside the interval are clipped.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Full Scale</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Restores full-range scaling for the active field. The slider and rendering return to full data span.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Interfaces Overlay</strong> / <strong>Show Interfaces</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Toggles interface overlay visibility. Interface boundaries appear/disappear on the map.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Line Scan</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Enables line-scan interaction mode. Click behavior switches to profile sampling.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Show Line</strong></td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Toggles the line marker visibility. The scan line appears/disappears in the view.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>Reset</strong> button</td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Restores default range state for the active panel.</td>
    </tr>
    <tr>
      <td style="border:1px solid #cfd6e4; padding:8px;"><strong>PNG</strong> button</td>
      <td style="border:1px solid #cfd6e4; padding:8px;">Exports the currently shown heatmap as a PNG image.</td>
    </tr>
  </tbody>
</table>

## Single View
### Purpose
Use **Single View** for focused analysis of one dataset panel at a time.

### Workflow
1. Open **Single View**.
2. In **ADD PANEL**, select a data type.
3. In the panel controls, choose **Select Folder**, **Select File**, and **Select Field**.
4. Adjust **Range:** values, **Range slider**, and **palette**.
5. Toggle **Full Scale**, **Interfaces Overlay**, **Line Scan**, and **Show Line** as needed.
6. Click **Reset** to return range settings to default.
7. Click **PNG** to export the current view.

### Typical Use Cases
- Inspecting one dataset at one time/file state.
- Fine-tuning range and palette for feature visibility.
- Producing a single publication or report figure.

## Multi View
### Purpose
Use **Multi View** when you need direct visual comparison across multiple selected files.

### Workflow
1. Open **Multi View**.
2. In **ADD PANEL**, select a data type to compare.
3. In the comparison card, choose **Select Folder** and one or more files in **Select File**.
4. Set **Select Field** for the comparison.
5. Adjust **Range:**, **Range slider**, **palette**, **Full Scale**, and **Show Interfaces**.
6. Use **Reset** when needed.
7. Use the comparison **PNG** export control to capture the current comparison state.

### Layout Behavior
- Multiple heatmaps are displayed in the comparison area for selected files.
- Controls apply at the active comparison group level and update the corresponding comparison views.
- Comparison selection persists while navigating between top tabs during the same session.

### Typical Comparison Workflows
- Compare the same field across different files.
- Compare different projects under consistent palette/range settings.
- Export side-by-side comparison images for reports.

## Calculation Notebook
### Purpose
Use **Calculation Notebook** to perform scientific and engineering calculations directly within OPView. Evaluate expressions, define variables, create arrays and matrices, compute statistics, and visualize results.

### Workflow
1. Open **Calculation Notebook**.
2. Write formulas, variable assignments, and function calls in the left **textarea**:
   - Simple expressions: `x = 5`, `y = x^2 - 3`, `z = sin(x)`
   - Arrays and matrices: `v = [1, 2, 3]`, `A = [[1, 2], [3, 4]]`
   - Function calls: `mean(v)`, `det(A)`, `solve(A, b)`
   - Unit arithmetic: `10*mm`, `210*GPa`, `5*min`
3. Results appear **line by line** in the right **results gutter**.
4. Variables carry forward: define once, use anywhere below.
5. Comment any line with `#` or `//`; inline comments are ignored.
6. Use `^` as a shorthand power operator (`x^2` is equivalent to `x**2`).
7. Slice arrays with standard indexing: `v[0]`, `v[1:4]`, `A[0][1]`.
8. Use `A @ B` for matrix multiplication.
9. Ternary expressions are supported: `x if condition else y`.

### Side Plot Panel (Right)
- **X**: Select an array variable for the x-axis.
- **Y**: Select one or more array variables for y-axis traces.
- **Type**: Choose visualization style:
  - **Lines**: Connected line plot
  - **Lines+Markers**: Lines with data points
  - **Markers**: Points only
  - **Bar**: Bar chart
  - **Histogram**: Distribution plot
- The plot updates automatically as you define/modify array variables.

### Save and Load
- **Save (.txt)**: Export notebook content (formulas and comments) to a `.txt` file. Variables and state are not saved; only the source text.
- **Load (.txt)**: Import a previously saved notebook `.txt` file.
- **Clear Notebook**: Reset all content and variables.

### Available Functions (By Category)

**Trigonometric**: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`

**Math**: `abs`, `sqrt`, `exp`, `log`, `log10`, `log2`, `hypot`, `floor`, `ceil`, `round`, `sign`, `degrees`, `radians`

**Number Helpers**: `clamp(x,lo,hi)`, `lerp(a,b,t)`, `factorial`, `gcd`, `lcm`

**Statistics**: `sum`, `mean`, `std`, `variance`, `median`, `prod`, `cumsum`, `diff`, `diff2`, `percentile`, `quantile`, `corrcoef`, `cov`, `zscore`, `norm01`, `histogram`, `mode`

**Array Builders**: `linspace(a,b,n)`, `arange(a,b,step)`, `zeros(m,n)`, `ones(m,n)`, `eye(n)`, `diag(v)`, `flatten`, `outer`, `vstack`, `hstack`, `meshgrid`, `full`, `reshape`

**Array Operations**: `sort`, `argsort`, `unique`, `flip`, `clip`, `roll`, `repeat`, `tile`, `where`, `concat`, `append`

**Matrix Multiplication**: `A @ B` (operator), `dot(a,b)` (vectors)

**Linear Algebra**:
- `eig(M)` → eigenvalue array; `eig_full(M)` → eigenvalue array (same, explicit name)
- `qr(A)` → `[Q, R]` list; `svd(M)` → singular values only; `cholesky(A)` → lower-triangular L
- `solve(A,b)`, `lstsq(A,b)`, `pinv(M)`, `inv(M)`, `det(M)`, `rank(M)`, `cond(M)`
- `transpose(M)`, `trace(M)`, `matrix_power(M,n)`, `kron(A,B)`, `norm_p(v,p)`

**Vector Operations**: `dot(a,b)`, `cross(a,b)`, `norm(v)`, `normalize(v)`, `length(v)`

**Interpolation & Fitting**: `interp(x,xp,fp)`, `polyfit(x,y,deg)` → coefficients, `polyval(p,x)`, `gradient(v,dx)`, `trapz(y,x)`, `cumtrapz(y,x)`

**FFT / Signal**: `fft(v)` → **magnitudes** `|FFT|` (not complex), `ifft(v)`, `fftfreq(n,dt)`, `fftshift(v)`, `real(v)`, `imag(v)`, `angle(v)`

**Engineering & Mechanics**:
  - Computational: `cfl_dt(dx,u,cfl)`, `diffusion_dt(dx,D,f)`, `fourier_number(D,dt,dx)`, `peclet(u,L,D)`, `cell_size(L,N)`, `domain_points(L,dx)`
  - Stress & Strain: `von_mises(s11,s22,s33,s12,s23,s13)` → scalar; `hooke_3d(E,nu,...)` → `[sxx,syy,szz,sxy,syz,sxz]`; `plane_stress(E,nu,exx,eyy,exy)` → `[sxx,syy,txy]`; `plane_strain(E,nu,exx,eyy,exy)` → `[sxx,syy,txy]`; `shear_modulus(E,nu)`, `lame_lambda(E,nu)`, `hooke_1d(E,eps)`, `plane_stress_ezz(nu,exx,eyy)`

**Dimensionless Numbers**: `reynolds(rho,u,L,mu)`, `mach(u,a)`, `prandtl(mu,cp,k)`, `nusselt_dittus(Re,Pr)`, `biot(h,L,k)`, `fourier_thermal(alpha,t,L)`, `lewis(alpha,D)`, `weber(rho,u,L,sig)`, `stokes(...)`, `grashof(...)`

**Special Functions**: `erf(x)`, `erfc(x)`, `gamma(x)`, `lgamma(x)`, `beta(a,b)`

**Physical Constants**: `g_n` (9.80665), `c_0` (2.998e8), `R_gas` (8.314), `k_B` (1.381e-23), `N_A` (6.022e23), `h_p` (6.626e-34), `sigma_SB` (5.67e-8), `mu_0`, `eps_0`, `atm`

**Units**:
  - Length: `nm`, `um`, `mm`, `cm`, `m`, `km`
  - Time: `s`, `ms`, `us`, `min`, `h`
  - Force/Pressure: `Pa`, `kPa`, `MPa`, `GPa`, `bar`, `mbar`, `atm`, `N`, `kN`, `MN`
  - Energy/Power: `J`, `kJ`, `MJ`, `kWh`, `W`, `kW`, `MW`
  - Other: `kg`, `Hz`, `kHz`, `MHz`, `L` (litre)

**Constants**: `pi`, `e`, `tau`, `deg` (π/180), `inf`

### Autocomplete
- The dropdown appears **automatically** as you type (≥1 character prefix).
- Press **Tab** or **Enter** to accept the highlighted suggestion.
- Click any suggestion to insert it.
- Press **Escape** to dismiss.
- Completions cover all built-in functions, constants, units, and user-defined variable names.

### Example Workflows

**Example 1: Stress Calculation**
```
E = 210*GPa          # Young's modulus
nu = 0.3             # Poisson's ratio
exx = 1e-3           # Strain
ps = plane_stress(E, nu, exx, 0, 0)  # returns [sxx, syy, txy]
sxx = ps[0]          # first element
sxx_MPa = sxx / MPa  # convert to MPa
```

**Example 2: Array and Statistics**
```
data = linspace(0, 10, 50)
values = sin(data)
m = mean(values)
s = std(values)
result = m / s
```

**Example 3: Matrix Operations**
```
A = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
b = [1, 2, 3]
det_A = det(A)
rank_A = rank(A)
eig_vals = eig(A)
```

### For Loops and If Statements
The notebook supports `for` loops and `if` / `elif` / `else` blocks. Write the header on one notebook row and indent the body lines with spaces or tabs on the following rows.

**Syntax rules**
- The header line must end with `:` (e.g. `for i in range(10):` or `if x > 0:`).
- Body lines must be indented (at least one space or tab).
- A blank row or an unindented row ends the block.
- The header row shows `[done — N iter]` in the results gutter; body rows show no result.
- Loop safety: `range()` is capped at **100 000 iterations** — larger ranges raise an error.

**Example 1 — accumulate a sum**
```
total = 0
for i in range(5):
    total = total + i
total
```

**Example 2 — build an array (diffusion equation)**
```
N = 100
dx = 1.0 / N
u = linspace(0, 1, N)
D = 0.01
dt = diffusion_dt(dx, D)
steps = 200
for t in range(steps):
    u_new = zeros(N, 1)
    for i in range(1, N - 1):
        u_new[i] = u[i] + D * dt / dx^2 * (u[i+1] - 2*u[i] + u[i-1])
    u = u_new
u
```

**Example 3 — conditional logic**
```
x = -3.5
sign_x = 1 if x > 0 else -1
```

**Available loop helpers** (auto-completed): `range(stop)`, `range(start, stop, step)`, `enumerate(v)`, `zip(a, b)`, `len(v)`.

### Typical Use Cases
- Quick scientific calculations during data analysis.
- Converting units and evaluating engineering formulas.
- Computing statistical measures (mean, std, percentiles) on simulation data.
- Plotting derived quantities (stress, strain, gradients) as arrays.
- Solving linear systems and eigenvalue problems.
- Interpolating or fitting curves for post-processing.
- Running iterative simulations (diffusion, time-stepping, finite differences).

### Known Limitations
- **No `while` loops** — use `for i in range(n):` instead.
- **No nested function definitions** — only built-in functions are available.
- **No `print()` function** — assign to a variable to see its value in the results gutter.
- **Side plot: 1D arrays only** — 2D arrays (matrices) cannot be selected for plotting.
- **For loops: server-side only** — the live JS preview shows blank for block lines; the correct result appears after the server evaluates.
- **FFT/advanced linalg: server-side only** — `fft`, `pinv`, `cholesky`, `qr` etc. do not show a live preview while typing; the correct result appears after the server evaluates.
- **Variable names cannot shadow built-ins** — `sin`, `pi`, `mm`, etc. are reserved.

## Formula Plot
### Purpose
Use **Formula Plot** to plot and analyse mathematical expressions interactively. Parameters are auto-detected and exposed as sliders. Panels can be linked to Calculation Notebook variables.

### Workflow
1. Open **Formula Plot**.
2. Click **+ Add Formula Panel 1D** or **+ Add Formula Panel 2D** in the sidebar.
3. In the panel, type a formula expression (e.g. `a*exp(-b*x)*sin(c*x)`).
4. Any free symbols other than `x` (and `x`, `y` in 2D) become **parameter sliders** automatically.
5. Adjust sliders to update the plot in real time.
6. Add more formula rows with **+ Add Formula** to overlay multiple curves.

### 1D Panel Controls
- **Expression**: the formula as a function of `x`. Use standard operators and any function from the math library.
- **Label**: legend entry for this curve.
- **Color / Line style / Width**: visual appearance of the trace.
- **Visible** checkbox: toggle a trace without removing it.
- **x min / x max / Points**: define the evaluation range and resolution.
- **Remove** (×): delete a formula row.

### Parameter Sliders
- Auto-detected from free symbols in the expression (e.g. `a`, `b`, `tau`).
- Each slider shows the current numeric value and can be adjusted by dragging or clicking ±.
- **Bind to Notebook** toggle: when enabled, the parameter value is read from the matching variable in the Calculation Notebook instead of the slider. If the variable does not exist in the notebook the binding is inactive.

### Curve Overlays (1D)
Toggle any of these alongside the main formula traces:
- **Derivative** — first derivative (computed via cubic spline).
- **2nd Derivative** — second derivative.
- **Integral Curve** — antiderivative (cumulative integral from x min).

### Analysis Panel (1D)
- **Value at point** (`x₀`): displays f(x₀), f′(x₀), f″(x₀) for the selected formula.
- **Definite integral** over a configurable interval `[a, b]`: shows the numeric integral value.
- **Select integral interval**: click the graph to set interval endpoints interactively.

### Export (1D)
- **Export CSV**: downloads the x and y data for all visible traces.
- **Export PNG**: downloads the current plot as a PNG image.

### 2D Panel
- **Expression**: formula as a function of `x` and `y` (e.g. `sin(x)*cos(y)`).
- **Presets**: Periodic Surface (`sin(x)*cos(y)`), Gaussian Hill, Saddle.
- **Display mode**: Surface (3D) or Contour (2D heatmap).
- **Contour levels**: number of isolines when in contour mode.
- **x/y range and resolution**: independently configurable.
- Parameters (free symbols other than `x`, `y`) become sliders just like in 1D.

### Built-in Formula Examples
`sin(x)`, `a*exp(-b*x)*sin(c*x)`, `a*exp(-((x-b)²)/(2c²))`, `1/(1+exp(-a*(x-b)))`, `a*exp(-x/tau)+c`, `a*(1-exp(-x/tau))+c`, `a/(1+exp(-(x-b)/c))+d`, `a*exp(-q/(r*x))`, `a/(x-b)+c`, `x²`, `x³-3x`

### Typical Use Cases
- Fitting analytical models visually before numerical fitting.
- Exploring how a formula changes with its parameters.
- Comparing multiple model curves (e.g. different decay constants).
- Deriving and integrating expressions without writing code.
- Linking fitted parameters back to the Calculation Notebook for further analysis.

## Initializations Explorer
### Purpose
Use **Initializations Explorer** to preview and understand OpenPhase microstructure initialization methods before running a simulation. Each method is rendered as a 2D phase map with configurable parameters.

### Workflow
1. Open **Initializations Explorer**.
2. Select an initialization **method** from the dropdown.
3. Adjust the **parameters** for the selected method using the controls that appear.
4. The preview heatmap updates automatically.
5. Read the **summary panel** for quantitative information (phase fractions, layer thicknesses, grain counts, etc.).

### Available Methods (25+)

| Category | Methods |
|----------|---------|
| Random nuclei | QuasiRandomNuclei, QuasiRandomSpheres, RandomNuclei |
| Layered structures | Single, SectionalPlane, Layer, Fractional, ThreeFractionals, TwoWalls, TwoDifferentWalls |
| Geometric shapes | Sphere, SphereInGrain, Ellipsoid, Rectangular, Cylinder, Paraboloid |
| Interface physics | ThermalGrooving, TripleJunction, Young3, Young4, Young4Periodic |
| Polycrystals | VoronoiTessellation, BlobbyAuto |

### Method Parameters (examples)

**QuasiRandomNuclei / QuasiRandomSpheres**: grid size (nx, ny), minimum distance between nuclei, radius range, phase probabilities, random seed.

**Layer / Fractional / ThreeFractionals**: grid size, layer thicknesses for each phase.

**Sphere / Ellipsoid / Cylinder**: grid size, center coordinates, radius (and axis for cylinder).

**VoronoiTessellation**: grid size, number of grains, random seed.

**ThermalGrooving**: groove width and depth.

**Young3 / Young4**: contact angle configurations.

### Summary Panel
For methods that support it, a summary panel shows:
- Phase fractions and counts.
- Layer thickness measurements.
- Nucleus positions and inter-nucleus distances (quasi-random methods).
- Grain size statistics (Voronoi).

### Typical Use Cases
- Checking that an initialization geometry matches the intended microstructure before a long simulation run.
- Comparing different initialization strategies (random vs. structured) visually.
- Verifying phase fractions and layer proportions from the summary panel.
- Exploring parameter sensitivity (e.g. how grain size changes with radius or distance settings).

## Custom Graph
### Purpose
Use **Custom Graph** to analyze `TextData` numerically and build multi-series trend plots.

### Workflow
1. Open **Custom Graph**.
2. Select a folder that contains text data files (`.txt`, `.dat`, `.csv`).
3. Click **+ Add Graph Panel** to create a graph workspace.
4. In **Data Sources:**, select 1–3 files.
5. In each file section, select columns to plot.
6. Configure graph settings in the right **Settings** area:
   - **X-Axis**: choose **Column** and edit **Title**.
   - **Display**: set **Legend Pos:** and toggle **Legend** / **Grid**.
   - **Y-Axis**: set axis titles and units (**Y-Axis 1 Units**, **Y-Axis 2 Units**).
   - **Column Settings**: assign each selected column to `Y1` or `Y2` and set legend labels.
7. Interact directly with the graph (zoom/pan/hover) and repeat adjustments until the plot is final.

### Controls and Outcomes
- **+ Add Graph Panel**: creates a new graph panel. A new configurable plotting area appears.
  This button is enabled only after a folder with `.txt`, `.dat`, or `.csv` files is selected.
- **Data Sources:** selector: loads file data into the panel. Column selectors populate for selected files.
- Column checklists: selects plotted series. Traces are added/removed from the graph.
- **X-Axis Column**: changes x-data source. All traces replot against the selected x-axis column.
- **Legend Pos:**: moves legend location. Legend redraws at the selected corner.
- **Legend** / **Grid** toggles: show/hide legend and grid lines.
- **Y-Axis 1 Units** / **Y-Axis 2 Units**: applies unit conversion for traces mapped to each y-axis.
- **Column Settings** (`Y1`/`Y2` and legend text): routes each trace to an axis and updates label text.

### Typical Use Cases
- Plotting stress/strain or other tabular trends from `TextData`.
- Overlaying multiple files in one chart for trend comparison.
- Preparing graph outputs for analysis notes and publications.

## Exporting Results
- Heatmaps: click the **PNG** button in `Single View` or `Multi View` controls.
- Graphs: use the graph toolbar export action in each `Custom Graph` panel.
- Formula Plot: use **Export CSV** or **Export PNG** in the panel toolbar.
- Notebook: use **Save (.txt)** to export formulas; use the side plot toolbar to export the chart.
- Exported files are saved through your browser/system download flow.

Recommended usage:
- Capture final figure states after setting range/palette/overlays.
- Export comparison snapshots from `Multi View` with consistent settings.
- Export graph images after final axis/unit/legend configuration.

## Troubleshooting
### Empty view
- Confirm a project is selected in **PROJECTS**.
- Confirm a panel is added through **ADD PANEL**.
- Confirm **Select File** and **Select Field** are set.

### Controls disabled
- Ensure the correct top tab is active.
- In `Multi View`, select files first; field/range controls remain limited until files are selected.

### Notebook: "Unknown symbol" error
- The variable or function name is not recognised. Check spelling and ensure the variable is defined on a line above the failing line.

### Notebook: result shows no live preview while typing
- FFT and advanced linear algebra functions (`fft`, `pinv`, `cholesky`, `qr`, etc.) are evaluated server-side only. The result appears after a short pause once you stop typing.

### Formula Plot: parameter slider not appearing
- Only free symbols that are not `x` (or `y` in 2D) become sliders. Ensure the symbol is present in the expression.

### Graph not updating
- Ensure `Custom Graph` panel has selected files and columns.
- Check that the selected x-axis column exists in the loaded data.

### Slow interaction
- Reduce the number of simultaneously selected comparison files.
- Reduce active graph traces in `Custom Graph` panels.
- Apply updates in smaller steps (range, then field, then overlays).

## FAQ
**Q: When should I use `Single View` vs `Multi View`?**
A: Use `Single View` for deep inspection of one panel; use `Multi View` for side-by-side comparison.

**Q: Why do I not see any files in selectors?**
A: Select a valid project in **PROJECTS** or add one with **📂 Add Project Folder**.

**Q: What is the fastest way to recover display settings?**
A: Click **Reset** in the active heatmap control area.

**Q: How do I compare several files in one place?**
A: Open `Multi View`, add a comparison panel, and select multiple entries in **Select File**.

**Q: How do I build a graph from text output?**
A: Open `Custom Graph`, click **+ Add Graph Panel**, then choose files/columns under **Data Sources:**.

**Q: How do I export what I see?**
A: Use **PNG** for heatmaps and graph toolbar export for plots.

**Q: What can I do in the Calculation Notebook?**
A: Define variables, compute formulas, work with arrays/matrices, call 100+ scientific functions, use units (e.g., `10*mm`, `210*GPa`), and plot results. Variables persist across lines.

**Q: How do I save my notebook calculations?**
A: Click **Save (.txt)** to export your formulas. Click **Load (.txt)** to import a previously saved notebook.

**Q: Can I use matrix multiplication in the notebook?**
A: Yes. Use `A @ B` for matrix multiplication or `dot(a, b)` for vector dot product.

**Q: How do I plot arrays from my calculations?**
A: Define array variables in the notebook, then use the **Side Plot Panel** to select X and Y variables and choose a visualization type (lines, markers, bars, etc.).

**Q: Is it safe to execute arbitrary Python code in the notebook?**
A: Yes. The notebook uses a safe AST-based evaluator—no `exec()` or `eval()`. Only allowed functions and operations are available.

**Q: What is Formula Plot for?**
A: For plotting `y = f(x)` or `z = f(x,y)` expressions with interactive sliders for each free parameter. Use it to explore model behaviour, overlay multiple curves, and compute derivatives or integrals visually.

**Q: How do I link a Formula Plot parameter to a Calculation Notebook variable?**
A: In the Formula Plot parameter controls, enable the **Bind to Notebook** toggle next to the parameter. The slider will then read its value from the matching variable name in the Calculation Notebook.

**Q: What is Initializations Explorer for?**
A: For previewing OpenPhase microstructure initialization methods (random nuclei, layers, spheres, Voronoi tessellation, etc.) before running a simulation. Adjust parameters and see the 2D phase map update in real time.

**Q: Does Initializations Explorer require a project to be loaded?**
A: No. It works independently of the project selection and does not read any simulation files.

# OpenPhase Post-Processing Suite

## Overview
The OpenPhase Post-Processing Suite is an interactive Dash web application for inspecting multi-physics simulation results. It combines reusable VTK heat-map viewers, statistical summaries, and text-data analytics to help you explore Phase Field, Mechanics, and Plasticity data without leaving the browser. A **Documentation** badge in the header links back to this guide for quick reference.

## Getting Started
- Launch the Dash app (`/home/alimuh7x/myenv/bin/python3 app.py`) and open the reported URL in a browser.
- Use the left sidebar to switch between the **Phase Field**, **Mechanics**, and **Plasticity** modules. Each module displays up to two heat-map “cards” per row.
- Every viewer remembers the latest available VTK file automatically; you only need to provide the data in the `VTK/` folder.

## Color Palettes
The heat maps share a curated set of perceptually balanced palettes. Each palette blends brand reds/blues with high-contrast midpoints so you can switch contexts without losing readability. The gradients below are rendered exactly as they appear in the app:

<table style="width:40%;margin:0 auto;border-collapse:collapse;table-layout:fixed;">
  <thead>
    <tr>
      <th style="text-align:left;padding:8px;border-bottom:1px solid #dbe3f4;width:35%;">Palette</th>
      <th style="text-align:left;padding:8px;border-bottom:1px solid #dbe3f4;width:65%;">Gradient</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding:8px;width:35%;"><strong>Yellow Blue</strong></td>
      <td style="padding:8px;width:65%;">
        <span style="display:block;height:18px;border-radius:6px;background:linear-gradient(90deg,#a5521a,#fbbc3c,#fffbe0,#00afb8,#00328f);"></span>
      </td>
    </tr>
    <tr>
      <td style="padding:8px;width:35%;"><strong>Blue to Red</strong></td>
      <td style="padding:8px;width:65%;">
        <span style="display:block;height:18px;border-radius:6px;background:linear-gradient(90deg,#a51717,#fbbc3c,#fffbe0,#00afb8,#00328f);"></span>
      </td>
    </tr>
    <tr>
      <td style="padding:8px;width:35%;"><strong>Spectral Low Blue</strong></td>
      <td style="padding:8px;width:65%;">
        <span style="display:block;height:18px;border-radius:6px;background:linear-gradient(90deg,#5e4fa2,#3f96b7,#b3e0a3,#fdd280,#9e0142);"></span>
      </td>
    </tr>
    <tr>
      <td style="padding:8px;width:35%;"><strong>Cool Warm Extended</strong></td>
      <td style="padding:8px;width:65%;">
        <span style="display:block;height:18px;border-radius:6px;background:linear-gradient(90deg,#000059,#295698,#fcf5e6,#f7d5b2,#590c36);"></span>
      </td>
    </tr>
    <tr>
      <td style="padding:8px;width:35%;"><strong>Aqua Fire</strong></td>
      <td style="padding:8px;width:65%;">
        <span style="display:block;height:18px;border-radius:6px;background:linear-gradient(90deg,#00328f,#00afb8,#fffbdf,#ffbc3c,#a51717);"></span>
      </td>
    </tr>
    <tr>
      <td style="padding:8px;width:35%;"><strong>Steel</strong></td>
      <td style="padding:8px;width:65%;">
        <span style="display:block;height:18px;border-radius:6px;background:linear-gradient(90deg,#0b2545,#3e5c76,#f6f9ff,#f4c06a,#b3541e);"></span>
      </td>
    </tr>
    <tr>
      <td style="padding:8px;width:35%;"><strong>Ice Sunset</strong></td>
      <td style="padding:8px;width:65%;">
        <span style="display:block;height:18px;border-radius:6px;background:linear-gradient(90deg,#1c3d5a,#3aa0c8,#ffffff,#f9d976,#f47068);"></span>
      </td>
    </tr>
  </tbody>
</table>

## Common Viewer Controls
Each heat-map card (Phase Field, Stress Tensor, Elastic Strains, Plastic Strain, CRSS) shares the same control stack:
- **Scalar Field dropdown** – choose which array/component to render. Tensor datasets expose `xx`, `yy`, `zz`, `xy`, `yz`, `zx` entries (e.g., `εᵖ_xx`).
- **Color Map dropdown** – switch among curated palettes while preserving the brand theme.
- **Range inputs & slider** – manually enter min/max values or drag the dual slider to focus on a subrange. Use the **Reset** button (with icon) to restore dataset statistics.
- **Slice controls** – enabled only for 3D volumes. Drag the slice slider or type an index to move through the stack.

## Phase Field Module
### Phase Field Viewer
- Visualizes `PhaseFields`, `Interfaces`, or `PhaseFraction` arrays.
- Titles display dynamically using the selected scalar.

### Size Details Card
- Reads `TextData/SizeDetails.dat` and `SizeAveInfo.dat`.
- Controls:
  - **Time Step** dropdown to choose the row from the text file.
  - **Chart Style** radio (Bar / Line) for the main plot.
  - **Line Series** dropdown to select which size is tracked through time.
- Outputs:
  - Main bar/line chart of size distribution at the selected time.
  - Time-series line chart of the chosen size label.

### Grain Distribution Card
- Histogram of grain sizes per time step with adjustable bin count.
- **Analysis checkbox** enables best-fit evaluation (Normal, Lognormal, Weibull, Gamma). When checked, the PDF overlay appears in navy and a LaTeX summary describes the winning model, parameters, and AIC/BIC scores.

## Mechanics Module
### Stress Tensor Viewer
- Heat map of `Pressure`, `von Mises`, or tensor components from `Stresses`. Units are scaled to MPa (1e6 factor) and displayed in the map title.

### Elastic Strains Viewer
- Visualizes tensor components from `ElasticStrains` with the same controls as other viewers.

### Stress–Strain Curves
- Interactive line plot of stress components (σ_xx, σ_yy, σ_zz, von Mises) versus ε_xx.
- Component checklist toggles traces; legend sits above the chart.

### Stress Histograms
- Histogram of any stress component or the computed average.
- **Bins slider** (5–100) controls resolution.
- **Show Best-fit PDF** toggle runs the distribution fitting routine. When enabled:
  - The chart overlays the selected PDF and the summary box renders LaTeX equations describing μ/σ (Normal), shape/scale (Weibull), etc.
  - Fitting leverages SciPy’s maximum-likelihood estimators and selects the best candidate via BIC (ties use the lowest AIC).

### Strain Histograms
- Same UX as stress histograms but operates on strain components (raw values, no MPa scaling).

## Plasticity Module
### CRSS Viewer
- Heat map of `CRSS_0_i` arrays with units converted to MPa where applicable.
- Shares all common viewer controls.

### Plastic Strain Viewer
- VTK heat map for the `PlasticStrain` tensor (εᵖ components). Helpful for visualizing permanent deformation across the domain.

### CRSS Histograms
- Histogram of average CRSS or any slip-system component.
- Includes bin slider and **Show Best-fit PDF** toggle identical to the stress/strain cards.

### Plastic Strain Analytics
- “Plastic Strain Insights” card plots every εᵖ component and its rate over time using line charts.
- Each chart includes a horizontal legend below the plot, highlighting the active traces.

## Distribution Fitting Details
When a histogram’s **Show Best-fit PDF** toggle is enabled, the app:
1. Extracts the current data series.
2. Fits four candidate distributions via SciPy: Normal (`stats.norm`), Lognormal (`stats.lognorm`), Weibull (`stats.weibull_min`), and Gamma (`stats.gamma`).
3. Computes log-likelihood, AIC, and BIC for each model.
4. Chooses the distribution with the smallest BIC.
5. Scales the PDF to histogram counts (sample size × bin width) and overlays it in navy.
6. Displays a LaTeX summary block containing parameter symbols (μ, σ, k, λ…), AIC, and BIC values.

### Probability Density Functions
For reference, the PDFs used during fitting are:

$$
\begin{aligned}
\text{Normal:}\quad f(x;\mu,\sigma) &= \frac{1}{\sigma\sqrt{2\pi}}\exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right) \\
\text{Lognormal:}\quad f(x;s,\mu,\sigma) &= \frac{1}{x s\sqrt{2\pi}}\exp\left(-\frac{(\ln x - \mu)^2}{2 s^2}\right),\quad x>0 \\
\text{Weibull (minimum):}\quad f(x;k,\lambda) &= \frac{k}{\lambda}\left(\frac{x}{\lambda}\right)^{k-1} \exp\left[-\left(\frac{x}{\lambda}\right)^k\right],\quad x\ge 0 \\
\text{Gamma:}\quad f(x;k,\theta) &= \frac{1}{\Gamma(k)\theta^k} x^{k-1} e^{-x/\theta},\quad x\ge 0
\end{aligned}
$$

SciPy returns shape/location/scale parameters; the app converts them to the notations above before rendering the summary.

## Tips & Shortcuts
- Hover tooltips on heat maps display the underlying scalar plus coordinates.
- Use the **Reset Range** button whenever switching scalars to avoid stale limits.
- For text-data cards, the last-used selections persist while you stay in the current session.
- Click the **Documentation** badge in the header at any time to open this guide in a new tab.

Enjoy exploring your Phase Field, Mechanics, and Plasticity simulations!

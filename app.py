"""Multi-field VTK viewer with reusable tab panels."""
import os
import warnings
from glob import glob
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
from dash import ALL, Dash, Input, Output, State, ctx, dcc, html
from flask import render_template_string
import markdown
from scipy import stats
import dash_mantine_components as dmc

from utils.vtk_reader import VTKReader
from viewer import ViewerPanel


APP_TITLE = "OPView"
TENSOR_COMPONENTS = ['xx', 'yy', 'zz', 'xy', 'yz', 'zx']


def tensor_scalars(array_name: str, prefix: str):
    return [
        {'label': f"{prefix}_{comp}", 'array': array_name, 'component': idx}
        for idx, comp in enumerate(TENSOR_COMPONENTS)
    ]

TAB_CONFIGS = [
    {
        "id": "phase-field",
        "label": "Phase Field",
        "datasets": [
            {
                "id": "phase",
                "label": "Phase Field",
                "file_glob": "VTK/PhaseField_*.vts",
                "scalars": [
                    {'label': 'Phase Field', 'array': 'PhaseFields'},
                    {'label': 'Interfaces', 'array': 'Interfaces'},
                    {'label': 'Phase Fraction', 'array': 'PhaseFraction_0'},
                ]
            }
        ],
    },
    {
        "id": "composition",
        "label": "Composition",
        "datasets": [
            {
                "id": "composition",
                "label": "Composition",
                "file_glob": "VTK/Composition_*.vts",
                "scalars": [
                    {'label': 'Weight Fraction FE (Total)', 'array': 'WeightFractionsTotal_FE'},
                    {'label': 'Mole Fraction FE (Total)', 'array': 'MoleFractionsTotal_FE'},
                    {'label': 'Mole Fraction FE (Phase 0)', 'array': 'MoleFractionsPhase_FE(0)'},
                    {'label': 'Mole Fraction FE (Phase 1)', 'array': 'MoleFractionsPhase_FE(1)'},
                    {'label': 'Weight Fraction SOLVENT (Total)', 'array': 'WeightFractionsTotal_SOLVENT'},
                    {'label': 'Mole Fraction SOLVENT (Total)', 'array': 'MoleFractionsTotal_SOLVENT'},
                    {'label': 'Mole Fraction SOLVENT (Phase 0)', 'array': 'MoleFractionsPhase_SOLVENT(0)'},
                    {'label': 'Mole Fraction SOLVENT (Phase 1)', 'array': 'MoleFractionsPhase_SOLVENT(1)'},
                    {'label': 'Weight Fraction CL (Total)', 'array': 'WeightFractionsTotal_CL'},
                    {'label': 'Mole Fraction CL (Total)', 'array': 'MoleFractionsTotal_CL'},
                    {'label': 'Mole Fraction CL (Phase 0)', 'array': 'MoleFractionsPhase_CL(0)'},
                    {'label': 'Mole Fraction CL (Phase 1)', 'array': 'MoleFractionsPhase_CL(1)'},
                ]
            }
        ],
    },
    {
        "id": "mechanics",
        "label": "Mechanics",
        "datasets": [
            {
                "id": "stresses",
                "label": "Stress Tensor",
                "units": "MPa",
                "scale": 1e-6,
                "file_glob": "VTK/Stresses_*.vts",
                "scalars": [
                    {'label': 'Pressure', 'array': 'Pressure'},
                    {'label': 'von Mises', 'array': 'von Mises'},
                    *tensor_scalars('Stresses', 'σ')
                ],
            },
            {
                "id": "elastic",
                "label": "Elastic Strains",
                "file_glob": "VTK/ElasticStrains_*.vts",
                # Store elastic strains in percent for all components
                "units": "%",
                "scale": 100.0,
                "scalars": tensor_scalars('ElasticStrains', 'ε'),
            },
        ],
    },
    {
        "id": "plasticity",
        "label": "Plasticity",
        "datasets": [
            {
                "id": "crss",
                "label": "CRSS",
                "units": "MPa",
                "scale": 1e-6,
                "file_glob": "VTK/CRSS_00001000.vts",
                "scalars": [
                    {'label': f"CRSS {i}", 'array': f"CRSS_0_{i}"}
                    for i in range(12)
                ],
            },
            {
                "id": "plastic-strain",
                "label": "Plastic Strain",
                "file_glob": "VTK/PlasticStrain_*.vts",
                # Store plastic strains in percent for all components
                "units": "%",
                "scale": 100.0,
                "scalars": tensor_scalars('PlasticStrain', 'εᵖ'),
            },
        ],
    },
]

reader_cache = {}


def get_reader(file_path):
    """Return cached VTKReader for a given file path."""
    if not file_path or not os.path.exists(file_path):
        raise FileNotFoundError(f"VTK file not found: {file_path}")
    if file_path not in reader_cache:
        reader_cache[file_path] = VTKReader(file_path)
    return reader_cache[file_path]


def latest_file(pattern: str):
    """Return the most recent file matching the glob pattern."""
    matches = sorted(glob(pattern))
    return matches[-1] if matches else None


app = Dash(__name__, suppress_callback_exceptions=True)
app.title = APP_TITLE

TEXTDATA_DIR = Path("TextData")
SIZE_DETAILS_FILE = TEXTDATA_DIR / "SizeDetails.dat"
SIZE_AVERAGE_FILE = TEXTDATA_DIR / "SizeAveInfo.dat"
STRESS_STRAIN_FILE = TEXTDATA_DIR / "StressStrainFile.txt"
CRSS_FILE = TEXTDATA_DIR / "CRSSFile.txt"
PLASTIC_STRAIN_FILE = TEXTDATA_DIR / "PlasticStrainFile.txt"
SIZE_AVERAGE_FILE = TEXTDATA_DIR / "SizeAveInfo.dat"


def load_size_details():
    if not SIZE_DETAILS_FILE.exists():
        return None
    rows = []
    try:
        with SIZE_DETAILS_FILE.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                try:
                    rows.append([float(p) for p in parts])
                except ValueError:
                    continue
    except OSError:
        return None
    if not rows:
        return None
    # Determine columns: first is time, second often count, rest are values
    has_count = len(rows[0]) > 2
    values_offset = 2 if has_count else 1
    labels = [str(idx + 1) for idx in range(len(rows[0]) - values_offset)]
    data_matrix = [row[values_offset:] for row in rows]
    times = [row[0] for row in rows]
    counts = [row[1] for row in rows] if has_count else None
    return {
        "times": times,
        "counts": counts,
        "labels": labels,
        "values": data_matrix,
    }


def load_size_averages():
    if not SIZE_AVERAGE_FILE.exists():
        return None
    times = []
    averages = []
    try:
        with SIZE_AVERAGE_FILE.open() as fh:
            for line in fh:
                parts = line.strip().split()
                if len(parts) < 3:
                    continue
                try:
                    times.append(float(parts[0]))
                    averages.append(float(parts[2]))
                except ValueError:
                    continue
    except OSError:
        return None
    if not times:
        return None
    return {"times": times, "averages": averages}


SIZE_DETAILS_DATA = load_size_details()
SIZE_AVERAGE_DATA = load_size_averages()


def load_stress_strain():
    if not STRESS_STRAIN_FILE.exists():
        return None
    try:
        with STRESS_STRAIN_FILE.open() as fh:
            lines = [line.strip() for line in fh if line.strip()]
    except OSError:
        return None
    if not lines:
        return None
    header = [token.strip() for token in lines[0].replace(',', ' ').split()]
    rows = []
    for line in lines[1:]:
        parts = [token.strip() for token in line.replace(',', ' ').split()]
        if len(parts) != len(header):
            continue
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue
    if not rows:
        return None

    columns = {name: [row[idx] for row in rows] for idx, name in enumerate(header)}

    def col(*names):
        for name in names:
            if name in columns:
                return columns[name]
        return None

    strain_components = {
        name: columns[name]
        for name in columns
        if name.lower().startswith('epsilon')
    }
    strain = strain_components.get('Epsilon_xx') or strain_components.get('EpsilonXX')
    if strain is None and strain_components:
        strain = next(iter(strain_components.values()))
    time = col('Time', 'TimeStep')
    sigma_xx = col('Sigma_xx', 'SigmaXX')
    sigma_yy = col('Sigma_yy', 'SigmaYY')
    sigma_zz = col('Sigma_zz', 'SigmaZZ')
    mises = col('Mises', 'VonMises')

    stress_components = {
        key: value for key, value in {
            "Sigma_xx": sigma_xx,
            "Sigma_yy": sigma_yy,
            "Sigma_zz": sigma_zz,
            "Mises": mises,
        }.items() if value is not None
    }

    if not strain or not stress_components:
        return None

    return {
        "strain": strain,
        "time": time,
        "components": stress_components,
        "strain_components": strain_components
    }


def load_crss():
    if not CRSS_FILE.exists():
        return None
    try:
        with CRSS_FILE.open() as fh:
            lines = [line.strip() for line in fh if line.strip()]
    except OSError:
        return None
    if not lines:
        return None
    header = [h.strip() for h in lines[0].split(',')]
    if 'Time' not in header:
        return None
    times = []
    averages = []
    time_idx = header.index('Time')
    avg_idx = header.index('Average') if 'Average' in header else None
    slip_columns = [
        (idx, name)
        for idx, name in enumerate(header)
        if name.lower().startswith('ss_')
    ]
    series = {name: [] for _, name in slip_columns}
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(',')]
        if len(parts) <= time_idx:
            continue
        try:
            time_val = float(parts[time_idx])
        except ValueError:
            continue
        if avg_idx is not None and len(parts) > avg_idx:
            try:
                avg_val = float(parts[avg_idx])
            except ValueError:
                avg_val = None
        else:
            avg_val = None
        row_series = {}
        for idx, name in slip_columns:
            if idx >= len(parts):
                row_series = {}
                break
            try:
                row_series[name] = float(parts[idx])
            except ValueError:
                row_series = {}
                break
        if not row_series:
            continue
        if avg_val is None:
            avg_val = float(np.mean(list(row_series.values())))
        times.append(time_val)
        averages.append(avg_val)
        for name in series:
            series[name].append(row_series[name])
    if not times:
        return None
    return {"times": times, "averages": averages, "series": series}


STRESS_STRAIN_DATA = load_stress_strain()
CRSS_DATA = load_crss()
PLASTIC_STRAIN_DATA = None


def load_plastic_strain():
    if not PLASTIC_STRAIN_FILE.exists():
        return None
    try:
        with PLASTIC_STRAIN_FILE.open() as fh:
            lines = [line.strip() for line in fh if line.strip()]
    except OSError:
        return None
    if not lines:
        return None
    header = [token.strip() for token in lines[0].replace(',', ' ').split()]
    rows = []
    for line in lines[1:]:
        parts = [token.strip() for token in line.replace(',', ' ').split()]
        if len(parts) != len(header):
            continue
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            continue
    if not rows:
        return None
    columns = {name: [row[idx] for row in rows] for idx, name in enumerate(header)}

    def collect(prefix):
        return {
            name: columns[name]
            for name in columns
            if name.lower().startswith(prefix)
        }

    times = columns.get('time') or columns.get('Time')
    if not times:
        return None
    epsilons = collect('epsilon')
    if 'PEEQ' in columns:
        epsilons['PEEQ'] = columns['PEEQ']
    rates = collect('rate')
    return {
        "times": times,
        "epsilons": epsilons,
        "rates": rates
    }


PLASTIC_STRAIN_DATA = load_plastic_strain()


DOCUMENTATION_FILE = Path("assets/Documentation.md")


@app.server.route('/docs')
def render_docs():
    if not DOCUMENTATION_FILE.exists():
        return render_template_string(
            "<h1>Documentation</h1><p>Documentation file not found.</p>"
        )
    content = DOCUMENTATION_FILE.read_text(encoding='utf-8')
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc'])
    html_body = md.convert(content)
    toc_html = md.toc
    template = """
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>OpenPhase Documentation</title>
        <link rel="stylesheet" href="/assets/style.css">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { background: var(--bg-gradient); }
            .doc-article {
                background: var(--surface);
                border-radius: 18px;
                padding: 32px 40px;
                box-shadow: var(--shadow-lg);
                line-height: 1.7;
                color: var(--text-main);
                word-wrap: break-word;
            }
            .doc-article h1, .doc-article h2, .doc-article h3 {
                color: #183568;
            }
            .doc-article pre {
                background: #0d2244;
                color: #fff;
                padding: 12px;
                border-radius: 8px;
                overflow-x: auto;
            }
            .doc-article code {
                color: #c50623;
            }
            .doc-sidebar .sidebar-tabs {
                overflow: visible;
            }
            .doc-sidebar .toc {
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            .doc-sidebar .toc ul {
                list-style: none;
                padding-left: 16px;
                margin-top: 6px;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .doc-sidebar .toc a {
                color: rgba(255,255,255,0.75);
                text-decoration: none;
                font-weight: 600;
                font-size: 14px;
                display: block;
                padding: 8px 12px;
                border-radius: 12px;
                transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
            }
            .doc-sidebar .toc a:hover {
                color: #fff;
                background: rgba(255,255,255,0.1);
            }
            .doc-sidebar .toc a.active {
                color: #fff;
                background: rgba(255,255,255,0.15);
                box-shadow: inset 3px 0 0 #c50623;
            }
            .doc-main {
                max-width: 1080px;
                width: 100%;
                margin: 0 auto;
            }
            /* Ensure doc header logo matches main app sizing */
            .app-logo {
                width: 42px;
                height: 42px;
                object-fit: contain;
            }
        </style>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async
          src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    </head>
    <body>
        <div id="app-container">
            <div class="app-header">
                <div class="top-bar">
                    <div class="top-left">
                        <img src="/assets/OP_Logo_main.png" class="app-logo" alt="OP logo">
                        <h1 class="app-title">OPV<span class="app-title-sub">iew</span></h1>
                    </div>
                    <div class="top-right">
                        <a class="doc-link" href="/">Back to App</a>
                    </div>
                </div>
            </div>
            <div class="layout-shell">
                <div class="sidebar doc-sidebar" style="position: sticky; top: 0; max-height: 100vh; overflow-y: auto; width: 280px;">
                    <span class="sidebar-title">Contents</span>
                    <div class="sidebar-tabs">
                        {{ toc|safe }}
                    </div>
                </div>
                <div class="main-panel">
                    <div class="doc-main">
                        <article class="doc-article">
                            {{ body|safe }}
                        </article>
                    </div>
                </div>
            </div>
        </div>
        <script>
            document.addEventListener('DOMContentLoaded', function () {
                const tocLinks = Array.from(document.querySelectorAll('.doc-sidebar .toc a'));
                if (!tocLinks.length) {
                    return;
                }
                const headingMap = tocLinks.map(link => {
                    const hash = decodeURIComponent(link.hash || '').replace('#', '');
                    const target = document.getElementById(hash);
                    return { link, target };
                }).filter(item => item.target);

                function setActive(link) {
                    tocLinks.forEach(l => l.classList.remove('active'));
                    if (link) {
                        link.classList.add('active');
                    }
                }

                tocLinks.forEach(link => {
                    link.addEventListener('click', () => setActive(link));
                });

                const observer = new IntersectionObserver((entries) => {
                    const visible = entries
                        .filter(entry => entry.isIntersecting)
                        .sort((a, b) => b.intersectionRatio - a.intersectionRatio);
                    if (visible.length > 0) {
                        const match = headingMap.find(item => item.target === visible[0].target);
                        if (match) {
                            setActive(match.link);
                        }
                    }
                }, {
                    rootMargin: '-150px 0px -60% 0px',
                    threshold: [0.2, 0.4, 0.6]
                });

                headingMap.forEach(item => observer.observe(item.target));

                // highlight first item initially
                setActive(tocLinks[0]);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(template, body=html_body, toc=toc_html)


def compute_average_series(series_dict):
    """Return element-wise average across provided series."""
    arrays = []
    lengths = []
    for values in series_dict.values():
        if values is None:
            continue
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            continue
        arrays.append(arr)
        lengths.append(arr.size)
    if not arrays:
        return None
    min_len = min(lengths)
    stacked = np.vstack([arr[:min_len] for arr in arrays])
    return np.mean(stacked, axis=0)


def build_histogram_figure(values, x_label, bins=None, fit=False):
    if values is None:
        return go.Figure(), "No data available"
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        return go.Figure(), "No data available"
    if bins is None:
        nbins = max(10, min(60, int(np.sqrt(arr.size) * 3)))
    else:
        nbins = max(5, min(100, int(bins)))
    hist = go.Histogram(
        x=arr,
        nbinsx=nbins,
        marker_color='#183568',
        name='Histogram'
    )

    x_min, x_max = arr.min(), arr.max()
    if np.isclose(x_min, x_max):
        x_min -= 1
        x_max += 1
    x_vals = np.linspace(x_min, x_max, 400)
    summary = "_Enable **Best-fit PDF** to evaluate distributions._"
    traces = [hist]

    if fit:
        best_fit = fit_best_distribution(arr)
        if best_fit:
            pdf_vals = best_fit['dist'].pdf(x_vals, *best_fit['params'])
            counts, edges = np.histogram(arr, bins=nbins)
            bin_width = edges[1] - edges[0]
            pdf_scaled = pdf_vals * arr.size * bin_width
            pdf_line = go.Scatter(
                x=x_vals,
                y=pdf_scaled,
                mode='lines',
                line=dict(color='#0d2244', width=2),
                name=f"{best_fit['name']} PDF"
            )
            traces.append(pdf_line)
            summary = format_fit_summary(best_fit)
        else:
            summary = "_No valid fit available._"

    fig = go.Figure(data=traces)
    fig.update_layout(
        margin=dict(l=50, r=20, t=30, b=50),
        height=320,
        template='plotly_white',
        bargap=0.05
    )
    fig.update_xaxes(
        title=x_label,
        title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
        tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
    )
    fig.update_yaxes(
        title="Frequency",
        title_font=dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f'),
        tickfont=dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
    )
    fig.update_traces(showlegend=False, selector=lambda t: isinstance(t, go.Histogram))
    return fig, summary


def crss_series_values(component):
    data = CRSS_DATA
    if not data:
        return None
    if component == 'Average':
        return np.asarray(data['averages']) / 1e6
    values = (data.get('series') or {}).get(component)
    return np.asarray(values) / 1e6 if values is not None else None


def stress_series_values(component):
    data = STRESS_STRAIN_DATA
    if not data:
        return None
    comps = data.get('components') or {}
    if component == 'Average':
        avg = compute_average_series(comps)
        return avg / 1e6 if avg is not None else None
    values = comps.get(component)
    return np.asarray(values) / 1e6 if values is not None else None


def strain_series_values(component):
    data = STRESS_STRAIN_DATA
    if not data:
        return None
    comps = data.get('strain_components') or {}
    if component == 'Average':
        avg = compute_average_series(comps)
        return avg * 100.0 if avg is not None else None
    values = comps.get(component)
    return np.asarray(values) * 100.0 if values is not None else None


def build_grain_histogram(time_value, bins, fit=False):
    data = SIZE_DETAILS_DATA
    if not data:
        return go.Figure(), "_No data available._"
    times = data['times']
    values = data['values']
    if not times or not values:
        return go.Figure(), "_No data available._"
    try:
        time_value = float(time_value)
    except (TypeError, ValueError):
        time_value = times[0]
    row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
    row_values = values[row_index]
    if not row_values:
        return go.Figure(), "_No data available._"
    fig, summary = build_histogram_figure(row_values, "Grain Size", bins, fit=fit)
    summary = f"**Time:** {times[row_index]:.3f}\n\n" + summary
    return fig, summary


def fit_best_distribution(data):
    """Fit candidate distributions and select best via BIC."""
    if data is None:
        return None
    arr = np.asarray(data, dtype=float)
    if arr.size < 3 or np.allclose(arr.std(), 0):
        return None
    candidates = {
        "Normal": stats.norm,
        "Lognormal": stats.lognorm,
        "Weibull": stats.weibull_min,
        "Gamma": stats.gamma
    }
    best = None
    n = arr.size
    for name, dist in candidates.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                params = dist.fit(arr)
        except Exception:
            continue
        try:
            loglik = np.sum(dist.logpdf(arr, *params))
        except Exception:
            continue
        k = len(params)
        aic = 2 * k - 2 * loglik
        bic = np.log(n) * k - 2 * loglik
        if not best or bic < best['bic']:
            best = {
                "name": name,
                "dist": dist,
                "params": params,
                "aic": aic,
                "bic": bic
            }
    return best


def format_fit_summary(best_fit):
    if not best_fit:
        return "_No valid fit available._"
    label_map = {
        "Normal": ["\\mu", "\\sigma"],
        "Lognormal": ["s", "\\mu", "\\sigma"],
        "Weibull": ["k", "\\lambda", "\\theta"],
        "Gamma": ["k", "\\theta", "\\lambda"]
    }
    labels = label_map.get(best_fit["name"]) or [f"\\theta_{i+1}" for i in range(len(best_fit["params"]))]
    param_lines = []
    for label, value in zip(labels, best_fit["params"]):
        param_lines.append(f"{label} &= {value:.3g}")
    params_block = " \\\\ ".join(param_lines)
    return (
        f"**Best Fit:** $\\text{{{best_fit['name']}}}$\n\n"
        f"$$\\begin{{aligned}}{params_block}\\end{{aligned}}$$\n\n"
        f"$$\\mathrm{{AIC}} = {best_fit['aic']:.2f}\\quad "
        f"\\mathrm{{BIC}} = {best_fit['bic']:.2f}$$"
    )


tab_datasets = {}
for tab in TAB_CONFIGS:
    datasets = []
    for dataset in tab.get("datasets", []):
        # Collect all available files for this dataset (time steps)
        files = []
        if dataset.get("file_glob"):
            files = sorted(glob(dataset["file_glob"]))
        elif dataset.get("file"):
            files = [dataset["file"]]
        if not files:
            continue
        # Default to latest file for initial view
        file_path = files[-1]
        dataset_config = {
            "id": f"{tab['id']}-{dataset['id']}",
            "label": dataset["label"],
            "scalars": dataset.get("scalars"),
            "colorA": dataset.get("colorA"),
            "colorB": dataset.get("colorB"),
            "file": file_path,
            "files": files,
            "scale": dataset.get("scale"),
            "units": dataset.get("units"),
            "overrides": dataset.get("overrides"),
            "enable_line_scan": tab['id'] != 'phase-field',  # Enable for all tabs except phase-field
        }
        try:
            panel = ViewerPanel(app, get_reader, dataset_config)
        except (FileNotFoundError, ValueError):
            continue
        datasets.append((dataset["label"], panel))
    tab_datasets[tab["id"]] = {
        "label": tab["label"],
        "panels": datasets
    }


def build_tab_children(tab_id):
    panels = tab_datasets[tab_id]["panels"]
    if not panels:
        return [html.Div("No datasets available for this tab.", className='dataset-empty')]
    cards = []

    # Add main viewer cards
    for label, panel in panels:
        # Main viewer card
        cards.append(html.Div([
            html.Div([
                html.Span(className='dataset-accent'),
                html.H3(label, className='dataset-title')
            ], className='dataset-header'),
            html.Div(panel.build_layout(), className='dataset-body')
        ], className='dataset-block'))

        # Line scan and histogram cards - for all tabs EXCEPT Phase Field
        if tab_id != 'phase-field':
            cards.append(panel.build_line_scan_card())
            # build_histogram_card() returns None (deprecated - now combined with line scan)
            histogram_card = panel.build_histogram_card()
            if histogram_card:
                cards.append(histogram_card)

    if tab_id == 'phase-field':
        # Phase-field tab: show size-details and grain distribution cards.
        for builder in (build_size_details_card, build_grain_distribution_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'mechanics':
        for builder in (build_stress_strain_card, build_stress_hist_card, build_strain_hist_card):
            card = builder()
            if card:
                cards.append(card)
    elif tab_id == 'plasticity':
        for builder in (build_crss_card, build_plastic_strain_card):
            card = builder()
            if card:
                cards.append(card)
    return [html.Div(cards, className='dataset-grid')]


TAB_ORDER = [tab['id'] for tab in TAB_CONFIGS]


def get_default_active_tab():
    for tab_id in TAB_ORDER:
        if tab_datasets.get(tab_id, {}).get("panels"):
            return tab_id
    return TAB_ORDER[0] if TAB_ORDER else None


def build_tab_bar():
    icons = {
        "phase-field": "⛶",
        "composition": "⚛",
        "mechanics": "⚙",
        "plasticity": "🧪",
    }
    return [
        html.Button(
            [
                html.Span(icons.get(tab_id, "•"), className="tab-icon"),
                html.Span(
                    tab_datasets.get(tab_id, {}).get("label", tab_id.title()),
                    className="tab-label"
                ),
            ],
            id={'type': 'tab-button', 'tab': tab_id},
            n_clicks=0,
            className='custom-tab'
        )
        for tab_id in TAB_ORDER
    ]


INITIAL_ACTIVE_TAB = get_default_active_tab()


def build_size_details_card():
    data = SIZE_DETAILS_DATA
    if not data:
        return None
    time_options = []
    for t in data['times']:
        if t.is_integer():
            label = str(int(t))
        else:
            label = f"{t:.3f}".rstrip('0').rstrip('.')
        time_options.append({'label': label, 'value': str(t)})
    value_labels = data['labels']
    if not value_labels:
        return None
    default_time = time_options[0]['value'] if time_options else None

    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Grain Details', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            html.Div([
                html.Div([
                    html.Label('Time Step', className='textdata-label'),
                    dcc.Dropdown(
                        id='size-card-time',
                        options=time_options,
                        value=default_time,
                        clearable=False,
                        className='textdata-input'
                    )
                ], className='textdata-control'),
                html.Div([
                    html.Label('Chart Style', className='textdata-label'),
                    dcc.RadioItems(
                        id='size-card-mode',
                        options=[
                            {'label': 'Bar', 'value': 'bar'},
                            {'label': 'Line', 'value': 'line'}
                        ],
                        value='bar',
                        inline=True,
                        className='textdata-radio',
                        labelStyle={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '12px'},
                        inputStyle={'marginRight': '4px'}
                    )
                ], className='textdata-control'),
            ], className='textdata-controls'),
            dcc.Graph(id='size-card-main', className='textdata-plot'),
            dcc.Graph(id='size-card-line', className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_grain_distribution_card():
    data = SIZE_DETAILS_DATA
    if not data:
        return None
    times = data['times']
    if not times:
        return None
    time_options = []
    for t in times:
        if t.is_integer():
            label = str(int(t))
        else:
            label = f"{t:.3f}".rstrip('0').rstrip('.')
        time_options.append({'label': label, 'value': str(t)})
    default_time = time_options[0]['value']
    default_time_val = float(default_time)
    default_bins = 15
    default_fig, default_summary = build_grain_histogram(default_time_val, default_bins)
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Grain Distribution', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            html.Div([
                html.Div([
                    html.Label('Time Step', className='textdata-label'),
                    dcc.Dropdown(
                        id='grain-dist-time',
                        options=time_options,
                        value=default_time,
                        clearable=False,
                        className='textdata-input'
                    )
                ], className='textdata-control'),
                html.Div([
                    html.Label('Number of Bins', className='textdata-label'),
                    dcc.Slider(
                        id='grain-dist-bins',
                        min=5,
                        max=50,
                        step=5,
                        value=default_bins,
                        marks={10: '10', 25: '25', 40: '40'},
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], className='textdata-control'),
                html.Div([
                    html.Label('Analysis', className='textdata-label'),
                    dcc.Checklist(
                        id='grain-dist-fit',
                        options=[{'label': 'Show Best-fit PDF', 'value': 'fit'}],
                        value=[],
                        className='hist-toggle'
                    )
                ], className='textdata-control')
            ], className='textdata-controls'),
            dcc.Graph(id='grain-dist-fig', figure=default_fig, className='textdata-plot')
        ], className='textdata-graphs'),
        dcc.Markdown(default_summary, id='grain-dist-summary', className='hist-summary', mathjax=True)
    ], className='dataset-block textdata-card')


def build_stress_strain_card():
    data = STRESS_STRAIN_DATA
    if not data:
        return None
    options = [
        {'label': 'σ_xx', 'value': 'Sigma_xx'},
        {'label': 'σ_yy', 'value': 'Sigma_yy'},
        {'label': 'σ_zz', 'value': 'Sigma_zz'},
        {'label': 'von Mises', 'value': 'Mises'},
    ]
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Stress–Strain Curves', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
        html.Div([
            html.Div([
                html.Label('Components', className='textdata-label'),
                dcc.Checklist(
                    id='stress-components',
                    options=options,
                    value=['Sigma_xx', 'Mises'],
                    className='textdata-radio',
                    labelStyle={'display': 'inline-flex', 'alignItems': 'center', 'marginRight': '12px'},
                    inputStyle={'marginRight': '4px'}
                )
            ], className='textdata-control')
        ], className='textdata-controls'),
            dcc.Graph(id='stress-strain-fig', className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_stress_hist_card():
    """Legacy PDF-based stress histogram card – hidden from UI."""
    return None


def build_strain_hist_card():
    """Legacy PDF-based strain histogram card – hidden from UI."""
    return None


def build_crss_card():
    data = CRSS_DATA
    if not data:
        return None
    series = data.get('series') or {}

    def sort_key(name):
        digits = ''.join(ch for ch in name if ch.isdigit())
        return int(digits) if digits else name

    options = [{'label': 'Average', 'value': 'Average'}]
    for name in sorted(series.keys(), key=sort_key):
        options.append({'label': name.replace('ss_', 'SS ').upper(), 'value': name})
    fig = build_crss_figure()
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('CRSS Evolution', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
        html.Div([
            html.Div([
                html.Label('Components', className='textdata-label'),
                dcc.Checklist(
                    id='crss-component-select',
                    options=options,
                    value=['Average'],
                    className='crss-checklist'
                )
            ], className='textdata-control crss-control')
        ], className='textdata-controls'),
            dcc.Graph(id='crss-avg-fig', figure=fig, className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_crss_hist_card():
    data = CRSS_DATA
    if not data:
        return None
    series = data.get('series') or {}


def build_crss_figure(selected=None):
    data = CRSS_DATA
    if not data:
        return go.Figure()
    times = data['times']
    series = data.get('series') or {}
    available = {'Average'}
    available.update({name for name, values in series.items() if values})
    if not selected:
        selected = ['Average']
    filtered = [key for key in selected if key in available]
    if not filtered:
        filtered = ['Average'] if 'Average' in available else list(available)
    selected = filtered
    traces = []
    for key in selected:
        if key == 'Average':
            values = data['averages']
            label = 'Average'
        else:
            values = series.get(key)
            label = key.replace('ss_', 'SS ').upper()
        if not values:
            continue
        traces.append(go.Scatter(
            x=times,
            y=np.array(values) / 1e6,
            mode='lines',
            line=dict(width=2),
            name=label
        ))
    fig = go.Figure(data=traces)
    fig.update_layout(
        margin=dict(l=50, r=30, t=70, b=60),
        height=320,
        template='plotly_white',
        legend=dict(
            orientation='h',
            x=0,
            xanchor='left',
            y=1.18,
            yanchor='bottom',
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(24,53,104,0.15)',
            borderwidth=1
        )
    )
    fig.update_xaxes(
        title="Time",
        title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
        tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
    )
    fig.update_yaxes(
        title="CRSS (MPa)",
        title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
        tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
    )
    return fig


def build_plastic_strain_card():
    data = PLASTIC_STRAIN_DATA
    if not data:
        return None
    strain_fig, rate_fig = build_plastic_strain_figures()
    return html.Div([
        html.Div([
            html.Span(className='dataset-accent'),
            html.H3('Plastic Strain Insights', className='dataset-title')
        ], className='dataset-header'),
        html.Div([
            dcc.Graph(id='plastic-strain-eps', figure=strain_fig, className='textdata-plot'),
            dcc.Graph(id='plastic-strain-rate', figure=rate_fig, className='textdata-plot')
        ], className='textdata-graphs')
    ], className='dataset-block textdata-card')


def build_plastic_strain_figures():
    data = PLASTIC_STRAIN_DATA
    times = data['times']
    eps = data['epsilons']
    rates = data['rates']
    strain_traces = []
    for name, values in sorted(eps.items()):
        display = name.replace('_', ' ').title()
        strain_traces.append(go.Scatter(
            x=times,
            y=values,
            mode='lines',
            line=dict(width=2),
            name=display
        ))
    rate_traces = []
    for name, values in sorted(rates.items()):
        display = name.replace('_', ' ').title()
        rate_traces.append(go.Scatter(
            x=times,
            y=values,
            mode='lines',
            line=dict(width=2),
            name=display
        ))
    strain_fig = go.Figure(data=strain_traces)
    strain_fig.update_layout(
        margin=dict(l=50, r=30, t=40, b=60),
        height=320,
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.3)
    )
    rate_fig = go.Figure(data=rate_traces)
    rate_fig.update_layout(
        margin=dict(l=50, r=30, t=40, b=60),
        height=320,
        template='plotly_white',
        legend=dict(orientation='h', yanchor='bottom', y=-0.3)
    )
    for fig, y_title in ((strain_fig, "Strain"), (rate_fig, "Strain Rate")):
        fig.update_xaxes(
            title="Time",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        fig.update_yaxes(
            title=y_title,
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
    return strain_fig, rate_fig


app.layout = dmc.MantineProvider(
    html.Div(
        id='app-container',
        children=[
            dcc.Store(id='active-tab', data=INITIAL_ACTIVE_TAB),
            html.Div([
                html.Div([
                    html.Div([
                        html.Img(src='/assets/OP_Logo_main.png', className='app-logo', alt='OP logo'),
                        html.H1([
                            "OPV",
                            html.Span("iew", className='app-title-sub'),
                        ], className='app-title')
                    ], className='top-left'),
                    html.Div([
                        html.A("Documentation", href='/docs', target='_blank', className='doc-link')
                    ], className='top-right')
                ], className='top-bar')
            ], className='app-header'),
            html.Div([
                html.Div([
                    html.Span("Modules", className='sidebar-title'),
                    html.Div(build_tab_bar(), className='sidebar-tabs')
                ], className='sidebar'),
                html.Div([
                    html.Div(
                        id='tab-content',
                        children=build_tab_children(INITIAL_ACTIVE_TAB) if INITIAL_ACTIVE_TAB else []
                    )
                ], className='main-panel')
            ], className='layout-shell')
        ]
    )
)


@app.callback(
    Output('active-tab', 'data'),
    Input({'type': 'tab-button', 'tab': ALL}, 'n_clicks'),
    State('active-tab', 'data'),
    prevent_initial_call=True
)
def set_active_tab(n_clicks, current_tab):
    trigger = ctx.triggered_id
    if isinstance(trigger, dict) and trigger.get('tab'):
        return trigger['tab']
    return current_tab


@app.callback(
    Output('tab-content', 'children'),
    Output({'type': 'tab-button', 'tab': ALL}, 'className'),
    Input('active-tab', 'data')
)
def render_active_tab(active_tab):
    if active_tab is None:
        return html.Div("No tabs available", className='dataset-empty'), ['custom-tab'] * len(TAB_ORDER)
    children = build_tab_children(active_tab)
    classes = [
        'custom-tab active-tab' if tab_id == active_tab else 'custom-tab'
        for tab_id in TAB_ORDER
    ]
    return children, classes


if SIZE_DETAILS_DATA:

    @app.callback(
        Output('size-card-main', 'figure'),
        Output('size-card-line', 'figure'),
        Input('size-card-time', 'value'),
        Input('size-card-mode', 'value')
    )
    def update_size_details(selected_time, chart_mode):
        data = SIZE_DETAILS_DATA
        times = data['times']
        labels = data['labels']
        values = data['values']
        if not times or not labels:
            return go.Figure(), go.Figure()
        try:
            time_value = float(selected_time)
        except (TypeError, ValueError):
            time_value = times[0]
        row_index = min(range(len(times)), key=lambda idx: abs(times[idx] - time_value))
        row_values = values[row_index]

        if chart_mode not in {'line', 'bar'}:
            chart_mode = 'bar'

        main_fig = go.Figure()
        if chart_mode == 'bar':
            main_fig.add_bar(x=labels, y=row_values, marker_color='#183568')
        else:
            main_fig.add_scatter(x=labels, y=row_values, mode='lines+markers', line=dict(color='#183568'))
        main_fig.update_layout(
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
            template='plotly_white'
        )
        axis_title_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#12294f')
        tick_font = dict(size=16, family='Montserrat, Arial, sans-serif', color='#0f1b2b')
        main_fig.update_xaxes(title="Grain Number", title_font=axis_title_font, tickfont=tick_font)
        main_fig.update_yaxes(title="Grain Size", title_font=axis_title_font, tickfont=tick_font)

        if SIZE_AVERAGE_DATA:
            avg_times = SIZE_AVERAGE_DATA['times']
            avg_values = SIZE_AVERAGE_DATA['averages']
        else:
            avg_times = times
            avg_values = [
                sum(row) / len(row) if row else 0
                for row in values
            ]
        line_fig = go.Figure(
            data=[go.Scatter(x=avg_times, y=avg_values, mode='lines+markers', line=dict(color='#c50623'))]
        )
        line_fig.update_layout(
            margin=dict(l=50, r=30, t=40, b=60),
            height=320,
            template='plotly_white'
        )
        line_fig.update_xaxes(title="Time Step", title_font=axis_title_font, tickfont=tick_font)
        line_fig.update_yaxes(title="Average Grain Size", title_font=axis_title_font, tickfont=tick_font)

        return main_fig, line_fig

    @app.callback(
        Output('grain-dist-fig', 'figure'),
        Output('grain-dist-summary', 'children'),
        Input('grain-dist-time', 'value'),
        Input('grain-dist-bins', 'value'),
        Input('grain-dist-fit', 'value')
    )
    def update_grain_distribution(selected_time, bins, fit_value):
        fit_enabled = bool(fit_value and 'fit' in fit_value)
        fig, summary = build_grain_histogram(selected_time, bins, fit=fit_enabled)
        return fig, summary


if STRESS_STRAIN_DATA:

    @app.callback(
        Output('stress-strain-fig', 'figure'),
        Input('stress-components', 'value')
    )
    def update_stress_strain(components):
        data = STRESS_STRAIN_DATA
        # Convert engineering strain to percent for display
        strain = np.array(data['strain']) * 100.0
        comp_map = data['components']
        labels = {
            "Sigma_xx": "σ_xx",
            "Sigma_yy": "σ_yy",
            "Sigma_zz": "σ_zz",
            "Mises": "von Mises",
        }
        default_components = ['Sigma_xx', 'Mises']
        selected = components or default_components
        traces = []
        for comp in selected:
            values = comp_map.get(comp)
            if values is None:
                continue
            traces.append(go.Scatter(
                x=strain,
                y=np.array(values) / 1e6,
                mode='lines',
                line=dict(width=2),
                name=labels.get(comp, comp)
            ))
        fig = go.Figure(data=traces)
        fig.update_layout(
            margin=dict(l=50, r=30, t=90, b=60),
            height=320,
            template='plotly_white',
            legend=dict(
                orientation='h',
                x=0,
                xanchor='left',
                y=1.18,
                yanchor='bottom',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='rgba(24,53,104,0.15)',
                borderwidth=1
            )
        )
        fig.update_xaxes(
            title="ε_xx (%)",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        fig.update_yaxes(
            title="Stress (MPa)",
            title_font=dict(size=16, family='Inter, sans-serif', color='#12294f'),
            tickfont=dict(size=13, family='Inter, sans-serif', color='#0f1b2b')
        )
        return fig

    @app.callback(
        Output('stress-hist-fig', 'figure'),
        Output('stress-hist-summary', 'children'),
        Input('stress-hist-component', 'value'),
        Input('stress-hist-bins', 'value'),
        Input('stress-hist-fit', 'value')
    )
    def update_stress_hist(selected_component, bins, fit_value):
        values = stress_series_values(selected_component)
        fit_enabled = bool(fit_value and 'fit' in fit_value)
        fig, summary = build_histogram_figure(values, "Stress (MPa)", bins, fit=fit_enabled)
        return fig, summary

    @app.callback(
        Output('strain-hist-fig', 'figure'),
        Output('strain-hist-summary', 'children'),
        Input('strain-hist-component', 'value'),
        Input('strain-hist-bins', 'value'),
        Input('strain-hist-fit', 'value')
    )
    def update_strain_hist(selected_component, bins, fit_value):
        values = strain_series_values(selected_component)
        fit_enabled = bool(fit_value and 'fit' in fit_value)
        fig, summary = build_histogram_figure(values, "Strain (%)", bins, fit=fit_enabled)
        return fig, summary


if CRSS_DATA:

    @app.callback(
        Output('crss-avg-fig', 'figure'),
        Input('crss-component-select', 'value')
    )
    def update_crss_plot(selected_components):
        return build_crss_figure(selected_components)




if __name__ == '__main__':
    print("\n" + "=" * 60)
    print(APP_TITLE.upper())
    print("=" * 60)
    for tab_id, info in tab_datasets.items():
        print(f"[{info['label']}]")
        if not info['panels']:
            print("  - No datasets found.")
            continue
        for dataset_label, panel in info['panels']:
            print(f"  - {dataset_label}: {panel.file_path}")
    print("\nStarting Dash server on http://127.0.0.1:8050\n")

    app.run(debug=True, host='127.0.0.1', port=8050)

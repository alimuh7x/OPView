"""
Helpers for the Mechanical Loads Explorer tab.

Data models and visualization builders for OpenPhase MechanicalLoads structures.
Each load has trigger conditions (ON/OFF) and 6-component boundary conditions
(stress, strain, or strain-rate per Voigt component: XX, YY, ZZ, YZ, XZ, XY).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

import plotly.graph_objects as go


TRIGGER_OPTIONS = [
    {"label": "User (manual)", "value": "USER"},
    {"label": "Time", "value": "TIME"},
    {"label": "Time Step", "value": "TIMESTEP"},
    {"label": "Stress", "value": "STRESS"},
    {"label": "Strain", "value": "STRAIN"},
]

BC_TYPE_OPTIONS = [
    {"label": "None", "value": "NONE"},
    {"label": "Stress", "value": "STRESS"},
    {"label": "Strain", "value": "STRAIN"},
    {"label": "Strain Rate", "value": "STRAINRATE"},
]

COMPONENT_LABELS = ["XX", "YY", "ZZ", "YZ", "XZ", "XY"]
BC_PARAMETER_NAMES = ["BCX", "BCY", "BCZ", "BCYZ", "BCXZ", "BCXY"]
BC_VALUE_PARAMETER_NAMES = ["BCValueX", "BCValueY", "BCValueZ", "BCValueYZ", "BCValueXZ", "BCValueXY"]

COMPONENT_INDEX_OPTIONS = [
    {"label": lbl, "value": i} for i, lbl in enumerate(COMPONENT_LABELS)
]

BC_TYPE_COLORS = {
    "STRESS": "#2563eb",
    "STRAIN": "#f59e0b",
    "STRAINRATE": "#10b981",
    "NONE": "#e2e8f0",
}

# Triggers that require a numeric threshold value
VALUE_TRIGGERS = {"TIME", "TIMESTEP", "STRESS", "STRAIN"}

# Triggers that require a component index (XX/YY/...)
INDEX_TRIGGERS = {"STRESS", "STRAIN"}
TIME_TRIGGERS = {"TIME", "TIMESTEP"}


def step_from_value(value: float | int | None, fallback: float = 0.001) -> float:
    """Return a numeric input step that matches the current value precision."""
    print(f"[mechanical-loads] step_from_value value={value!r} fallback={fallback!r}", flush=True)
    if value is None:
        return float(fallback)
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return float(fallback)
    if not decimal_value.is_finite():
        return float(fallback)
    if decimal_value == decimal_value.to_integral_value():
        return 1.0
    exponent = decimal_value.normalize().as_tuple().exponent
    if exponent >= 0:
        return 1.0
    return float(Decimal("1").scaleb(exponent))


def default_load_structure() -> dict:
    """Return a default MechanicalLoadStructure as a Python dict."""
    print("[mechanical-loads] default_load_structure", flush=True)
    return {
        "dt": 1.0,
        "trigger_on": "USER",
        "trigger_on_val": 0.0,
        "trigger_on_idx": 0,
        "trigger_off": "USER",
        "trigger_off_val": 0.0,
        "trigger_off_idx": 0,
        "repeat": 1,
        "bc_types": ["NONE"] * 6,
        "bc_values": [0.0] * 6,
    }


def reconstruct_loads(
    num_loads: int,
    trigger_on_all: list,
    trigger_on_val_all: list,
    trigger_on_idx_all: list,
    trigger_off_all: list,
    trigger_off_val_all: list,
    trigger_off_idx_all: list,
    repeat_all: list,
    bc_type_all: list,
    bc_val_all: list,
) -> list[dict]:
    """
    Reconstruct a list of load dicts from Dash ALL-pattern callback values.

    ALL arrays are ordered by DOM position (load 0 first, then load 1, etc.).
    bc_type_all and bc_val_all have 6 entries per load (one per Voigt component).
    """
    loads = []
    print(
        "[mechanical-loads] reconstruct_loads:start "
        f"num_loads={num_loads!r} trigger_on_all={trigger_on_all!r} "
        f"trigger_on_val_all={trigger_on_val_all!r} trigger_on_idx_all={trigger_on_idx_all!r} "
        f"trigger_off_all={trigger_off_all!r} trigger_off_val_all={trigger_off_val_all!r} "
        f"trigger_off_idx_all={trigger_off_idx_all!r} repeat_all={repeat_all!r} "
        f"bc_type_all={bc_type_all!r} bc_val_all={bc_val_all!r}",
        flush=True,
    )
    defaults = default_load_structure()
    for n in range(num_loads):
        bc_types = []
        bc_values = []
        for c in range(6):
            flat = n * 6 + c
            t = bc_type_all[flat] if flat < len(bc_type_all) else "NONE"
            v = bc_val_all[flat] if flat < len(bc_val_all) else 0.0
            bc_types.append(t if t is not None else "NONE")
            bc_values.append(float(v) if v is not None else 0.0)

        loads.append({
            "trigger_on":     trigger_on_all[n] if n < len(trigger_on_all) and trigger_on_all[n] else defaults["trigger_on"],
            "trigger_on_val": float(trigger_on_val_all[n]) if n < len(trigger_on_val_all) and trigger_on_val_all[n] is not None else 0.0,
            "trigger_on_idx": int(trigger_on_idx_all[n]) if n < len(trigger_on_idx_all) and trigger_on_idx_all[n] is not None else 0,
            "trigger_off":    trigger_off_all[n] if n < len(trigger_off_all) and trigger_off_all[n] else defaults["trigger_off"],
            "trigger_off_val": float(trigger_off_val_all[n]) if n < len(trigger_off_val_all) and trigger_off_val_all[n] is not None else 0.0,
            "trigger_off_idx": int(trigger_off_idx_all[n]) if n < len(trigger_off_idx_all) and trigger_off_idx_all[n] is not None else 0,
            "repeat":         int(repeat_all[n]) if n < len(repeat_all) and repeat_all[n] is not None else 1,
            "bc_types":  bc_types,
            "bc_values": bc_values,
        })
    print(f"[mechanical-loads] reconstruct_loads:done loads={loads!r}", flush=True)
    return loads


def build_load_figure(loads: list[dict], dt: float = 1.0) -> go.Figure:
    """
    Grouped bar chart: X = Voigt component, bars = loads, color = BC type.
    Only components with a non-NONE BC type are shown.
    """
    print(f"[mechanical-loads] build_load_figure loads={loads!r}", flush=True)
    history_traces = build_load_history_traces(loads, dt=dt)
    if history_traces:
        fig = go.Figure()
        for trace in history_traces:
            fig.add_trace(go.Scatter(
                x=trace["x"],
                y=trace["y"],
                mode="lines",
                line={"color": BC_TYPE_COLORS.get(trace["bc_type"], "#64748b"), "width": 3},
                name=trace["name"],
                hovertemplate=(
                    f"{trace['name']}<br>Time: %{{x}}<br>"
                    f"{trace['y_label']}: %{{y}}<extra></extra>"
                ),
            ))
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Applied Stress / Strain",
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            height=320,
            margin={"t": 20, "b": 40, "l": 50, "r": 20},
            legend={"orientation": "h", "y": -0.28, "x": 0},
        )
        return fig

    fig = go.Figure()

    if not loads:
        fig.update_layout(
            title="No loads defined",
            xaxis_title="Component",
            yaxis_title="Value",
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            height=320,
            margin={"t": 40, "b": 40, "l": 50, "r": 20},
        )
        return fig

    for i, load in enumerate(loads):
        for bc_type in ("STRESS", "STRAIN", "STRAINRATE"):
            x_vals, y_vals = [], []
            for c, (t, v) in enumerate(zip(load["bc_types"], load["bc_values"])):
                if t == bc_type:
                    x_vals.append(COMPONENT_LABELS[c])
                    y_vals.append(v)
            if not x_vals:
                continue
            fig.add_trace(go.Bar(
                name=f"Load {i} — {bc_type.capitalize()}",
                x=x_vals,
                y=y_vals,
                marker_color=BC_TYPE_COLORS[bc_type],
                legendgroup=bc_type,
                showlegend=True,
            ))

    has_any = any(
        t != "NONE"
        for load in loads
        for t in load["bc_types"]
    )
    if not has_any:
        fig.add_annotation(
            text="No active BCs — set a component type to Stress, Strain, or Strain Rate",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font={"size": 13, "color": "#94a3b8"},
        )

    fig.update_layout(
        barmode="group",
        xaxis_title="Voigt Component",
        yaxis_title="Applied Value",
        xaxis={"categoryorder": "array", "categoryarray": COMPONENT_LABELS},
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        height=320,
        margin={"t": 20, "b": 40, "l": 50, "r": 20},
        legend={"orientation": "h", "y": -0.28, "x": 0},
    )
    return fig


def build_load_step_figure(loads: list[dict], dt: float = 1.0) -> go.Figure:
    """Render the same load history preview against timestep count instead of time."""
    print(f"[mechanical-loads] build_load_step_figure loads={loads!r} dt={dt!r}", flush=True)
    history_traces = build_load_history_traces(loads, dt=dt)
    fig = go.Figure()

    if history_traces and dt > 0.0:
        for trace in history_traces:
            step_x = [(x / dt) if x is not None else None for x in trace["x"]]
            fig.add_trace(go.Scatter(
                x=step_x,
                y=trace["y"],
                mode="lines",
                line={"color": BC_TYPE_COLORS.get(trace["bc_type"], "#64748b"), "width": 3},
                name=trace["name"],
                hovertemplate=(
                    f"{trace['name']}<br>Timestep: %{{x}}<br>"
                    f"{trace['y_label']}: %{{y}}<extra></extra>"
                ),
            ))
        fig.update_layout(
            xaxis_title="Timestep",
            yaxis_title="Applied Stress / Strain",
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            height=320,
            margin={"t": 20, "b": 40, "l": 50, "r": 20},
            legend={"orientation": "h", "y": -0.28, "x": 0},
        )
        return fig

    fig.add_annotation(
        text="No timestep preview available — define a load history and set dt > 0",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font={"size": 13, "color": "#94a3b8"},
    )
    fig.update_layout(
        xaxis_title="Timestep",
        yaxis_title="Applied Stress / Strain",
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        height=320,
        margin={"t": 20, "b": 40, "l": 50, "r": 20},
    )
    return fig


def _time_window(load: dict, bc_type: str, bc_value: float, dt: float = 1.0) -> tuple[float, float] | None:
    """Return the preview time window for a load when time-based triggers exist."""
    on_is_time = load["trigger_on"] in TIME_TRIGGERS
    off_is_time = load["trigger_off"] in TIME_TRIGGERS
    if not on_is_time and not off_is_time:
        if (
            bc_type == "STRAINRATE"
            and load["trigger_on"] == "STRAIN"
            and load["trigger_off"] == "STRAIN"
            and float(bc_value) != 0.0
        ):
            start = abs(float(load["trigger_on_val"])) / abs(float(bc_value))
            delta_strain = float(load["trigger_off_val"]) - float(load["trigger_on_val"])
            duration = abs(delta_strain) / abs(float(bc_value))
            if duration <= 0.0:
                duration = 1.0
            return start, start + duration
        return None

    start = float(load["trigger_on_val"]) if on_is_time else 0.0
    end = float(load["trigger_off_val"]) if off_is_time else start + 1.0
    if load["trigger_on"] == "TIMESTEP":
        start *= dt
    if load["trigger_off"] == "TIMESTEP":
        end *= dt
    if end <= start:
        end = start + dt
    return start, end


def _uses_derived_strainrate_window(load: dict, bc_type: str, bc_value: float) -> bool:
    """Return whether this history preview derives time from strain delta and strain rate."""
    return (
        bc_type == "STRAINRATE"
        and load["trigger_on"] == "STRAIN"
        and load["trigger_off"] == "STRAIN"
        and float(bc_value) != 0.0
    )


def build_load_history_traces(loads: list[dict], dt: float = 1.0) -> list[dict]:
    """Build time-history preview traces for stress, strain, and strain-rate BCs."""
    print(f"[mechanical-loads] build_load_history_traces loads={loads!r} dt={dt!r}", flush=True)
    traces = []
    derived_time_cursor = 0.0
    for load_index, load in enumerate(loads):
        repeats = max(1, int(load.get("repeat", 1) or 1))
        load_derived_end = derived_time_cursor

        for component_index, (bc_type, bc_value) in enumerate(zip(load["bc_types"], load["bc_values"])):
            if bc_type == "NONE":
                continue
            window = _time_window(load, bc_type, float(bc_value), dt=dt)
            if window is None:
                continue
            start, end = window
            if _uses_derived_strainrate_window(load, bc_type, float(bc_value)):
                duration = end - start
                start = derived_time_cursor
                end = start + duration
                load_derived_end = max(load_derived_end, start + repeats * duration)
                print(
                    "[mechanical-loads] build_load_history_traces:derived_window "
                    f"load_index={load_index} component_index={component_index} "
                    f"duration={duration!r} start={start!r} end={end!r} "
                    f"cursor_end={load_derived_end!r}",
                    flush=True,
                )
            duration = end - start

            x_vals: list[float | None] = []
            y_vals: list[float | None] = []
            name = f"Load {load_index} {COMPONENT_LABELS[component_index]} {bc_type.title()}"

            if bc_type in {"STRESS", "STRAIN"}:
                for cycle in range(repeats):
                    cycle_start = start + cycle * duration
                    cycle_end = cycle_start + duration
                    x_vals.extend([cycle_start, cycle_start, cycle_end, cycle_end, None])
                    y_vals.extend([0.0, float(bc_value), float(bc_value), 0.0, None])
            elif bc_type == "STRAINRATE":
                if load["trigger_on"] == "STRAIN" and load["trigger_off"] == "STRAIN":
                    start_strain = float(load["trigger_on_val"])
                    target_strain = float(load["trigger_off_val"])
                    for cycle in range(repeats):
                        cycle_start = start + cycle * duration
                        cycle_end = cycle_start + duration
                        x_vals.extend([cycle_start, cycle_end])
                        y_vals.extend([start_strain, target_strain])
                        if repeats > 1:
                            x_vals.extend([cycle_end, None])
                            y_vals.extend([start_strain, None])
                        else:
                            x_vals.append(None)
                            y_vals.append(None)
                else:
                    start_strain = 0.0
                    target_delta = float(bc_value) * duration
                    for cycle in range(repeats):
                        cycle_start = start + cycle * duration
                        cycle_end = cycle_start + duration
                        x_vals.extend([cycle_start, cycle_end])
                        y_vals.extend([start_strain, start_strain + target_delta])
                        if repeats > 1:
                            x_vals.extend([cycle_end, None])
                            y_vals.extend([start_strain, None])
                        else:
                            x_vals.append(None)
                            y_vals.append(None)
            else:
                continue

            traces.append({
                "name": name,
                "component": COMPONENT_LABELS[component_index],
                "bc_type": bc_type,
                "x": x_vals,
                "y": y_vals,
                "y_label": "Strain" if bc_type in {"STRAIN", "STRAINRATE"} else "Stress",
            })
        if load_derived_end > derived_time_cursor:
            derived_time_cursor = load_derived_end
            print(
                "[mechanical-loads] build_load_history_traces:advance_cursor "
                f"load_index={load_index} derived_time_cursor={derived_time_cursor!r}",
                flush=True,
            )

    print(f"[mechanical-loads] build_load_history_traces traces={traces!r}", flush=True)
    return traces


def build_trigger_timeline(loads: list[dict], dt: float = 1.0) -> go.Figure:
    """
    Scatter timeline for loads with TIME or TIMESTEP triggers.
    Each load gets a lane showing ON (green ▶) and OFF (red ■) trigger points.
    """
    print(f"[mechanical-loads] build_trigger_timeline loads={loads!r} dt={dt!r}", flush=True)
    time_loads = [
        (i, load) for i, load in enumerate(loads)
        if load["trigger_on"] in VALUE_TRIGGERS or load["trigger_off"] in VALUE_TRIGGERS
    ]

    fig = go.Figure()
    x_points: list[float] = []

    if not time_loads:
        fig.add_annotation(
            text="No time / timestep / stress / strain triggers defined",
            xref="paper", yref="paper", x=0.5, y=0.5,
            showarrow=False, font={"size": 13, "color": "#94a3b8"},
        )
        fig.update_layout(
            height=160,
            plot_bgcolor="#f8fafc",
            paper_bgcolor="#ffffff",
            margin={"t": 10, "b": 30, "l": 80, "r": 20},
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return fig

    y_labels = [f"Load {i}" for i, _ in time_loads]

    for i, load in time_loads:
        label = f"Load {i}"
        on_is_valued = load["trigger_on"] in VALUE_TRIGGERS
        off_is_valued = load["trigger_off"] in VALUE_TRIGGERS
        on_x = load["trigger_on_val"] if on_is_valued else None
        off_x = load["trigger_off_val"] if off_is_valued else None
        if on_x is not None and load["trigger_on"] == "TIMESTEP":
            on_x = on_x * dt
        if off_x is not None and load["trigger_off"] == "TIMESTEP":
            off_x = off_x * dt
        if on_x is not None:
            x_points.append(float(on_x))
        if off_x is not None:
            x_points.append(float(off_x))

        if on_x is not None and off_x is not None:
            fig.add_trace(go.Scatter(
                x=[on_x, off_x], y=[label, label],
                mode="lines",
                line={"color": "#94a3b8", "width": 2, "dash": "dot"},
                showlegend=False,
                hoverinfo="skip",
            ))
        if on_x is not None:
            on_label = load["trigger_on"]
            if load["trigger_on"] in INDEX_TRIGGERS:
                on_label += f"[{COMPONENT_LABELS[load['trigger_on_idx']]}]"
            fig.add_trace(go.Scatter(
                x=[on_x], y=[label],
                mode="markers+text",
                marker={"symbol": "diamond", "size": 13, "color": "#10b981"},
                text=[f"ON ({on_label})"],
                textposition="middle right" if off_x is not None and on_x >= off_x else "middle left",
                showlegend=False,
                hovertemplate=f"Load {i} ON<br>Trigger: {on_label}<br>Value: {on_x}<extra></extra>",
            ))
        if off_x is not None:
            off_label = load["trigger_off"]
            if load["trigger_off"] in INDEX_TRIGGERS:
                off_label += f"[{COMPONENT_LABELS[load['trigger_off_idx']]}]"
            fig.add_trace(go.Scatter(
                x=[off_x], y=[label],
                mode="markers+text",
                marker={"symbol": "square", "size": 12, "color": "#ef4444"},
                text=[f"OFF ({off_label})"],
                textposition="middle left" if on_x is not None and off_x <= on_x else "middle right",
                showlegend=False,
                hovertemplate=f"Load {i} OFF<br>Trigger: {off_label}<br>Value: {off_x}<extra></extra>",
            ))

    if x_points:
        x_min = min(x_points)
        x_max = max(x_points)
        x_span = x_max - x_min
        padding = max(0.001, x_span * 0.1) if x_span > 0 else max(0.001, abs(x_min) * 0.1, 0.001)
        xaxis_config = {
            "range": [x_min - padding, x_max + padding],
        }
    else:
        xaxis_config = {}

    fig.update_layout(
        xaxis_title="Trigger Time / Value",
        plot_bgcolor="#f8fafc",
        paper_bgcolor="#ffffff",
        height=max(240, 80 + 90 * len(time_loads)),
        margin={"t": 50, "b": 40, "l": 100, "r": 100},
        xaxis=xaxis_config,
        yaxis={
            "categoryorder": "array",
            "categoryarray": y_labels,
            "autorange": "reversed",
        },
    )
    print(
        "[mechanical-loads] build_trigger_timeline:layout "
        f"y_labels={y_labels!r} autorange='reversed'",
        flush=True,
    )
    return fig


def _format_scalar(value: float) -> str:
    """Format numeric values compactly for OPStudio export."""
    return f"{float(value):g}"


def build_opstudio_export_text(loads: list[dict]) -> str:
    """Build OPStudio-compatible Mechanical Loads input text for the current loads."""
    print(f"[mechanical-loads] build_opstudio_export_text loads={loads!r}", flush=True)
    entries: list[tuple[str, str] | None] = []

    for idx, load in enumerate(loads):
        entries.append((f"$Load_{idx}", "Yes"))
        entries.append((f"$TriggerON_{idx}", load["trigger_on"]))
        if load["trigger_on"] != "USER":
            entries.append((f"$TriggerONvalue_{idx}", _format_scalar(load["trigger_on_val"])))
        if load["trigger_on"] in INDEX_TRIGGERS:
            entries.append((f"$ONindex_{idx}", COMPONENT_LABELS[load["trigger_on_idx"]]))

        entries.append((f"$TriggerOFF_{idx}", load["trigger_off"]))
        if load["trigger_off"] != "USER":
            entries.append((f"$TriggerOFFvalue_{idx}", _format_scalar(load["trigger_off_val"])))
        if load["trigger_off"] in INDEX_TRIGGERS:
            entries.append((f"$OFFindex_{idx}", COMPONENT_LABELS[load["trigger_off_idx"]]))

        entries.append((f"$Repeat_{idx}", str(int(load["repeat"]))))

        for component_index, (bc_type, bc_value) in enumerate(zip(load["bc_types"], load["bc_values"])):
            if bc_type == "NONE":
                continue
            bc_name = BC_PARAMETER_NAMES[component_index]
            bc_value_name = BC_VALUE_PARAMETER_NAMES[component_index]
            entries.append((f"${bc_name}_{idx}", bc_type))
            entries.append((f"${bc_value_name}_{idx}", _format_scalar(bc_value)))

        if idx < len(loads) - 1:
            entries.append(None)

    key_width = max((len(entry[0]) for entry in entries if entry is not None), default=0)
    lines: list[str] = []
    for entry in entries:
        if entry is None:
            lines.append("")
            continue
        key, value = entry
        lines.append(f"{key.ljust(key_width)} : {value}")
    return "\n".join(lines)


def build_loads_summary(loads: list[dict]) -> list[tuple[str, str]]:
    """Return (label, value) pairs for summary stat cards."""
    print(f"[mechanical-loads] build_loads_summary loads={loads!r}", flush=True)
    total = len(loads)
    n_stress = sum(1 for load in loads for t in load["bc_types"] if t == "STRESS")
    n_strain = sum(1 for load in loads for t in load["bc_types"] if t == "STRAIN")
    n_rate = sum(1 for load in loads for t in load["bc_types"] if t == "STRAINRATE")
    n_time = sum(1 for load in loads if load["trigger_on"] in VALUE_TRIGGERS)
    return [
        ("Loads", str(total)),
        ("Stress BCs", str(n_stress)),
        ("Strain BCs", str(n_strain)),
        ("Strain Rate BCs", str(n_rate)),
        ("Value-Triggered", str(n_time)),
    ]


def summarize_load(load: dict, idx: int) -> str:
    """Return a plain-text description of a single load."""
    print(f"[mechanical-loads] summarize_load idx={idx!r} load={load!r}", flush=True)
    lines = [f"Load {idx}:"]

    on_desc = load["trigger_on"]
    if load["trigger_on"] in VALUE_TRIGGERS:
        on_desc += f" = {load['trigger_on_val']}"
    if load["trigger_on"] in INDEX_TRIGGERS:
        on_desc += f" [{COMPONENT_LABELS[load['trigger_on_idx']]}]"
    lines.append(f"  TriggerON : {on_desc}")

    off_desc = load["trigger_off"]
    if load["trigger_off"] in VALUE_TRIGGERS:
        off_desc += f" = {load['trigger_off_val']}"
    if load["trigger_off"] in INDEX_TRIGGERS:
        off_desc += f" [{COMPONENT_LABELS[load['trigger_off_idx']]}]"
    lines.append(f"  TriggerOFF: {off_desc}")

    lines.append(f"  Repeat    : {load['repeat']}")

    active = [
        f"{COMPONENT_LABELS[c]}: {t} = {v:g}"
        for c, (t, v) in enumerate(zip(load["bc_types"], load["bc_values"]))
        if t != "NONE"
    ]
    lines.append("  BCs: " + (", ".join(active) if active else "(none)"))
    return "\n".join(lines)

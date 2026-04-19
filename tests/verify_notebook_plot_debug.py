from callbacks.notebook_manager import NotebookCallbackManager
from ui.calculation_notebook import NOTEBOOK_SNIPPETS
from utils.notebook_eval import evaluate_notebook_rows


def main() -> None:
    print("[verify][notebook-plot] start", flush=True)
    snippet = NOTEBOOK_SNIPPETS["Wt% ↔ Mole Fraction"]
    rows = [{"id": f"line_{index}", "expression": line} for index, line in enumerate(snippet.splitlines())]
    print(f"[verify][notebook-plot] rows={len(rows)}", flush=True)
    evaluated_rows, variables, array_variables = evaluate_notebook_rows(rows)
    print(f"[verify][notebook-plot] evaluated_rows={len(evaluated_rows)}", flush=True)
    print(f"[verify][notebook-plot] scalar_names={sorted(variables.keys())}", flush=True)
    print(f"[verify][notebook-plot] array_names={sorted(array_variables.keys())}", flush=True)
    spec = {
        "x_var": "wt_Ni_arr",
        "y_vars": ["x_Ni_arr"],
        "plot_type": "lines",
        "title": "Wt% to mole fraction debug",
        "x_title": "wt_Ni_arr",
        "y_title": "x_Ni_arr",
    }
    print(f"[verify][notebook-plot] spec={spec}", flush=True)
    fig = NotebookCallbackManager._build_plot_figure(spec, array_variables, 14, 2.0)
    print(f"[verify][notebook-plot] traces={len(fig.data)}", flush=True)
    if fig.data:
        trace = fig.data[0]
        x_len = len(trace["x"]) if "x" in trace and trace["x"] is not None else None
        y_len = len(trace["y"]) if "y" in trace and trace["y"] is not None else None
        print(f"[verify][notebook-plot] trace0_type={trace['type']} x_len={x_len} y_len={y_len}", flush=True)
    print("[verify][notebook-plot] done", flush=True)


if __name__ == "__main__":
    main()

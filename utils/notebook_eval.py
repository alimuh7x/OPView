"""
Safe scalar evaluation helpers for the calculation notebook tab.
"""

from __future__ import annotations

import ast
import math
from typing import Iterable

import numpy as np

from .formula_parser import ALLOWED_CONSTANTS, ALLOWED_FUNCTIONS


ALLOWED_SCALAR_FUNCTIONS = {
    name: func for name, func in ALLOWED_FUNCTIONS.items()
}
ALLOWED_SCALAR_FUNCTIONS.update(
    {
        "floor": math.floor,
        "ceil": math.ceil,
        "round": round,
    }
)


ALLOWED_NOTEBOOK_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.USub,
    ast.UAdd,
)


class NotebookEvaluationError(ValueError):
    """Raised when a notebook line cannot be evaluated safely."""


class _NotebookValidator(ast.NodeVisitor):
    """Validate that a notebook expression only uses allowed syntax."""

    def __init__(self, allowed_names: Iterable[str]):
        self.allowed_names = set(allowed_names)

    def generic_visit(self, node):
        if not isinstance(node, ALLOWED_NOTEBOOK_NODES):
            raise NotebookEvaluationError(f"Unsupported syntax: {type(node).__name__}")
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id not in self.allowed_names:
            raise NotebookEvaluationError(f"Unknown symbol: {node.id}")

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_SCALAR_FUNCTIONS:
            raise NotebookEvaluationError("Only approved math functions are allowed")
        for arg in node.args:
            self.visit(arg)
        if node.keywords:
            raise NotebookEvaluationError("Keyword arguments are not supported")


def _normalize_expression(expression: str) -> str:
    return expression.replace("^", "**").strip()


def _coerce_scalar(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        if value.size != 1:
            raise NotebookEvaluationError("Only scalar results are supported")
        return np.asarray(value).reshape(-1)[0].item()
    if isinstance(value, (int, float)):
        return value
    raise NotebookEvaluationError("Only scalar numeric results are supported")


def _format_scalar(value) -> str:
    scalar = _coerce_scalar(value)
    if isinstance(scalar, (int, float)):
        abs_scalar = abs(float(scalar))
        if abs_scalar >= 1e3 or (abs_scalar > 0 and abs_scalar <= 1e-3):
            return f"{float(scalar):.6e}".replace(".000000e", "e").replace("e+0", "e").replace("e-0", "e-").replace("e+", "e")
    if isinstance(scalar, float) and scalar.is_integer():
        return str(int(scalar))
    return f"{scalar:.12g}"


def evaluate_notebook_expression(expression: str, variables: dict[str, float]):
    """Evaluate a notebook expression against current variables."""
    expr = _normalize_expression(expression)
    if not expr:
        raise NotebookEvaluationError("Please enter a value or formula")

    context = {}
    context.update(ALLOWED_SCALAR_FUNCTIONS)
    context.update(ALLOWED_CONSTANTS)
    context.update(variables)

    try:
        parsed = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise NotebookEvaluationError("Invalid expression") from exc

    _NotebookValidator(context.keys()).visit(parsed)
    compiled = compile(parsed, "<notebook>", "eval")
    value = eval(compiled, {"__builtins__": {}}, context)
    return _coerce_scalar(value)


def evaluate_notebook_rows(rows: list[dict]) -> tuple[list[dict], dict[str, float]]:
    """Evaluate notebook rows from top to bottom."""
    variables: dict[str, float] = {}
    evaluated_rows: list[dict] = []

    for row in rows:
        expression = str(row.get("expression", "") or "").strip()
        updated = dict(row)
        updated["result"] = ""
        updated["error"] = ""

        if not expression:
            evaluated_rows.append(updated)
            continue

        try:
            if "=" in expression:
                variable_name, rhs = expression.split("=", 1)
                variable_name = variable_name.strip()
                rhs = rhs.strip()
                if not variable_name.isidentifier():
                    raise NotebookEvaluationError("Variable name is invalid")
                if variable_name in ALLOWED_SCALAR_FUNCTIONS or variable_name in ALLOWED_CONSTANTS:
                    raise NotebookEvaluationError("Variable name is reserved")
                value = evaluate_notebook_expression(rhs, variables)
                variables[variable_name] = value
                updated["result"] = _format_scalar(value)
            else:
                value = evaluate_notebook_expression(expression, variables)
                updated["result"] = _format_scalar(value)
        except NotebookEvaluationError as exc:
            updated["error"] = str(exc)
        except Exception as exc:  # pragma: no cover - defensive guard
            updated["error"] = f"Evaluation failed: {exc}"

        evaluated_rows.append(updated)

    return evaluated_rows, variables

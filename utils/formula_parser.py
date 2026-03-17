"""
Safe formula parsing utilities for interactive plotting.
"""

from __future__ import annotations

import ast
from typing import Dict, Iterable

import numpy as np


ALLOWED_FUNCTIONS = {
    "abs": np.abs,
    "arccos": np.arccos,
    "arcsin": np.arcsin,
    "arctan": np.arctan,
    "cos": np.cos,
    "cosh": np.cosh,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
    "sin": np.sin,
    "sinh": np.sinh,
    "sqrt": np.sqrt,
    "tan": np.tan,
    "tanh": np.tanh,
}

ALLOWED_CONSTANTS = {
    "e": np.e,
    "pi": np.pi,
}

ALLOWED_NODES = (
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


class FormulaValidationError(ValueError):
    """Raised when a formula contains unsupported syntax."""


class _FormulaValidator(ast.NodeVisitor):
    """Validate that the expression only contains allowed syntax."""

    def __init__(self, allowed_names: Iterable[str]):
        self.allowed_names = set(allowed_names)

    def generic_visit(self, node):
        if not isinstance(node, ALLOWED_NODES):
            raise FormulaValidationError(
                f"Unsupported syntax: {type(node).__name__}"
            )
        super().generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if node.id not in self.allowed_names:
            raise FormulaValidationError(f"Unknown symbol: {node.id}")

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in ALLOWED_FUNCTIONS:
            raise FormulaValidationError("Only approved math functions are allowed")
        for arg in node.args:
            self.visit(arg)
        if node.keywords:
            raise FormulaValidationError("Keyword arguments are not supported")


def extract_formula_variables(expression: str) -> list[str]:
    """
    Extract user-defined variable names from a formula.

    Returns variable names excluding ``x``, built-in constants, and allowed functions.
    """
    if not expression or not str(expression).strip():
        return []

    try:
        parsed = ast.parse(expression, mode="eval")
    except SyntaxError:
        return []
    names = set()

    for node in ast.walk(parsed):
        if isinstance(node, ast.Name):
            if node.id in {"x", *ALLOWED_FUNCTIONS.keys(), *ALLOWED_CONSTANTS.keys()}:
                continue
            names.add(node.id)

    return sorted(names)


def evaluate_formula(expression: str, x_values, extra_context: Dict[str, float] | None = None):
    """
    Evaluate a formula safely against a NumPy x array.

    Args:
        expression: Formula such as ``sin(x)`` or ``x**2 + 1``
        x_values: NumPy array of x values
        extra_context: Optional extra scalar values available in the expression

    Returns:
        NumPy array of y values
    """
    if not expression or not str(expression).strip():
        raise FormulaValidationError("Please enter a formula")

    context = {"x": np.asarray(x_values)}
    context.update(ALLOWED_FUNCTIONS)
    context.update(ALLOWED_CONSTANTS)
    if extra_context:
        context.update(extra_context)

    parsed = ast.parse(expression, mode="eval")
    _FormulaValidator(context.keys()).visit(parsed)

    compiled = compile(parsed, "<formula>", "eval")
    result = eval(compiled, {"__builtins__": {}}, context)
    result = np.asarray(result)

    if result.ndim == 0:
        result = np.full_like(context["x"], float(result), dtype=float)

    if result.shape != context["x"].shape:
        raise FormulaValidationError("Formula must return one y value for each x")

    return result

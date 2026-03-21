"""
SymPy helper library for common symbolic math operations in notebooks.
"""

from __future__ import annotations

from typing import Any

import sympy as sp


def verify_equation(lhs_str: str, rhs_str: str, variables: str = "x y z") -> dict[str, Any]:
    """Symbolically verify that lhs equals rhs.

    Returns a dict with 'equal' (bool), 'simplified_diff', and 'latex'.
    """
    syms = sp.symbols(variables)
    local_dict = {str(s): s for s in syms}
    local_dict.update({"pi": sp.pi, "e": sp.E, "I": sp.I, "oo": sp.oo})

    lhs = sp.sympify(lhs_str, locals=local_dict)
    rhs = sp.sympify(rhs_str, locals=local_dict)
    diff = sp.simplify(lhs - rhs)

    return {
        "equal": diff == 0,
        "simplified_diff": str(diff),
        "lhs_latex": sp.latex(lhs),
        "rhs_latex": sp.latex(rhs),
        "diff_latex": sp.latex(diff),
    }


def compute_derivative(expr_str: str, var: str = "x") -> dict[str, str]:
    """Compute the symbolic derivative.

    Returns dict with 'result' and 'latex'.
    """
    v = sp.Symbol(var)
    expr = sp.sympify(expr_str, locals={var: v})
    deriv = sp.diff(expr, v)
    return {
        "result": str(deriv),
        "latex": sp.latex(deriv),
        "original_latex": sp.latex(expr),
    }


def compute_integral(expr_str: str, var: str = "x", definite: tuple | None = None) -> dict[str, str]:
    """Compute the symbolic integral.

    If `definite` is (a, b), compute the definite integral from a to b.
    """
    v = sp.Symbol(var)
    expr = sp.sympify(expr_str, locals={var: v})

    if definite:
        a, b = definite
        result = sp.integrate(expr, (v, a, b))
    else:
        result = sp.integrate(expr, v)

    return {
        "result": str(result),
        "latex": sp.latex(result),
        "original_latex": sp.latex(expr),
    }


def solve_equation(equation_str: str, var: str = "x") -> dict[str, Any]:
    """Solve an equation (given as 'lhs = rhs' or just an expression = 0)."""
    v = sp.Symbol(var)

    if "=" in equation_str:
        parts = equation_str.split("=", 1)
        lhs = sp.sympify(parts[0].strip(), locals={var: v})
        rhs = sp.sympify(parts[1].strip(), locals={var: v})
        eq = sp.Eq(lhs, rhs)
    else:
        eq = sp.sympify(equation_str, locals={var: v})

    solutions = sp.solve(eq, v)
    return {
        "solutions": [str(s) for s in solutions],
        "solutions_latex": [sp.latex(s) for s in solutions],
        "num_solutions": len(solutions),
    }


def solve_ode(
    ode_str: str, func: str = "y", var: str = "x"
) -> dict[str, str]:
    """Solve an ODE.

    ode_str: The ODE expression (e.g., "y'' + y" for y'' + y = 0).
    """
    v = sp.Symbol(var)
    f = sp.Function(func)

    # Parse the ODE string  
    local_dict = {var: v, func: f(v)}
    ode_expr = sp.sympify(ode_str, locals=local_dict)
    eq = sp.Eq(ode_expr, 0)

    try:
        solution = sp.dsolve(eq, f(v))
        return {
            "solution": str(solution),
            "latex": sp.latex(solution),
        }
    except Exception as e:
        return {
            "solution": f"Could not solve: {e}",
            "latex": "",
        }


def series_expansion(
    expr_str: str, var: str = "x", point: str = "0", order: int = 6
) -> dict[str, str]:
    """Compute Taylor/Laurent series expansion."""
    v = sp.Symbol(var)
    expr = sp.sympify(expr_str, locals={var: v})
    pt = sp.sympify(point)
    series = expr.series(v, pt, order)

    return {
        "series": str(series),
        "latex": sp.latex(series),
        "original_latex": sp.latex(expr),
    }


def generate_sympy_code(description: str) -> str:
    """Generate a self-contained SymPy code snippet for a given task.

    Returns executable Python code as a string.
    """
    # This is a template-based generator; for complex cases, use the LLM
    return f"""\
import sympy as sp
from sympy import *
from IPython.display import Latex

# {description}
x, y, z = sp.symbols('x y z')

# TODO: Add specific computation here
result = sp.simplify(x + y)
display(Latex(f'${{sp.latex(result)}}$'))
"""

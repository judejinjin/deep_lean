"""
Visualization code generator — creates Matplotlib/Plotly code from specifications.
"""

from __future__ import annotations

from typing import Any


# ── Template Library ────────────────────────────────────────────────

TEMPLATES: dict[str, str] = {
    "line_plot": """\
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace({x_min}, {x_max}, {n_points})
{y_expressions}

fig, ax = plt.subplots(figsize=(8, 5))
{plot_lines}
ax.set_xlabel('{x_label}')
ax.set_ylabel('{y_label}')
ax.set_title('{title}')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
""",
    "vector_field": """\
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace({x_min}, {x_max}, {n_points})
y = np.linspace({y_min}, {y_max}, {n_points})
X, Y = np.meshgrid(x, y)

U = {u_expr}
V = {v_expr}

fig, ax = plt.subplots(figsize=(8, 8))
magnitude = np.sqrt(U**2 + V**2)
ax.quiver(X, Y, U/magnitude, V/magnitude, magnitude, cmap='viridis', alpha=0.8)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('{title}')
ax.set_aspect('equal')
plt.colorbar(ax.collections[0], label='Magnitude')
plt.tight_layout()
plt.show()
""",
    "surface_3d": """\
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

x = np.linspace({x_min}, {x_max}, {n_points})
y = np.linspace({y_min}, {y_max}, {n_points})
X, Y = np.meshgrid(x, y)
Z = {z_expr}

fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8, edgecolor='none')
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_zlabel('z')
ax.set_title('{title}')
plt.tight_layout()
plt.show()
""",
    "contour": """\
import numpy as np
import matplotlib.pyplot as plt

x = np.linspace({x_min}, {x_max}, {n_points})
y = np.linspace({y_min}, {y_max}, {n_points})
X, Y = np.meshgrid(x, y)
Z = {z_expr}

fig, ax = plt.subplots(figsize=(8, 6))
cs = ax.contourf(X, Y, Z, levels=20, cmap='RdBu_r')
ax.contour(X, Y, Z, levels=20, colors='k', linewidths=0.3)
plt.colorbar(cs)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('{title}')
ax.set_aspect('equal')
plt.tight_layout()
plt.show()
""",
    "phase_portrait": """\
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

def system(state, t):
    x, y = state
    dxdt = {dx_expr}
    dydt = {dy_expr}
    return [dxdt, dydt]

fig, ax = plt.subplots(figsize=(8, 8))

# Plot trajectories from various initial conditions
t = np.linspace(0, {t_max}, 500)
for x0 in np.linspace({x_min}, {x_max}, 8):
    for y0 in np.linspace({y_min}, {y_max}, 8):
        sol = odeint(system, [x0, y0], t)
        ax.plot(sol[:, 0], sol[:, 1], 'b-', alpha=0.3, linewidth=0.5)

# Add vector field
xg = np.linspace({x_min}, {x_max}, 15)
yg = np.linspace({y_min}, {y_max}, 15)
Xg, Yg = np.meshgrid(xg, yg)
U = {dx_expr_grid}
V = {dy_expr_grid}
ax.streamplot(Xg, Yg, U, V, color='darkblue', density=1.5, linewidth=0.5)

ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('{title}')
ax.set_xlim({x_min}, {x_max})
ax.set_ylim({y_min}, {y_max})
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
""",
}


def generate_plot_code(spec: dict[str, Any]) -> str:
    """Generate Python plotting code from a specification dict.

    spec keys:
        type: "line_plot", "vector_field", "surface_3d", "contour", "phase_portrait"
        title: str
        ... (type-specific parameters)
    """
    plot_type = spec.get("type", "line_plot")
    template = TEMPLATES.get(plot_type)

    if not template:
        return f"# Unknown plot type: {plot_type}\n# Available: {list(TEMPLATES.keys())}"

    # Apply defaults
    defaults = {
        "x_min": -5,
        "x_max": 5,
        "y_min": -5,
        "y_max": 5,
        "n_points": 50,
        "title": spec.get("title", "Plot"),
        "x_label": "x",
        "y_label": "y",
        "t_max": 10,
    }
    params = {**defaults, **spec}

    # Handle line_plot specifics
    if plot_type == "line_plot":
        expressions = spec.get("expressions", [("np.sin(x)", "sin(x)")])
        y_lines = []
        plot_lines = []
        for i, expr_info in enumerate(expressions):
            if isinstance(expr_info, tuple):
                expr, label = expr_info
            else:
                expr, label = expr_info, f"y{i}"
            y_lines.append(f"y{i} = {expr}")
            plot_lines.append(f"ax.plot(x, y{i}, label='{label}')")
        params["y_expressions"] = "\n".join(y_lines)
        params["plot_lines"] = "\n".join(plot_lines)

    try:
        return template.format(**params)
    except KeyError as e:
        return f"# Missing parameter: {e}\n# Spec: {spec}"


def generate_plotly_code(spec: dict[str, Any]) -> str:
    """Generate Plotly (interactive) code from a specification."""
    plot_type = spec.get("type", "line_plot")
    title = spec.get("title", "Interactive Plot")

    if plot_type == "line_plot":
        return f"""\
import numpy as np
import plotly.graph_objects as go

x = np.linspace({spec.get('x_min', -5)}, {spec.get('x_max', 5)}, 200)

fig = go.Figure()
fig.add_trace(go.Scatter(x=x, y=np.sin(x), mode='lines', name='sin(x)'))
fig.update_layout(title='{title}', xaxis_title='x', yaxis_title='y')
fig.show()
"""
    elif plot_type == "surface_3d":
        return f"""\
import numpy as np
import plotly.graph_objects as go

x = np.linspace({spec.get('x_min', -5)}, {spec.get('x_max', 5)}, 50)
y = np.linspace({spec.get('y_min', -5)}, {spec.get('y_max', 5)}, 50)
X, Y = np.meshgrid(x, y)
Z = {spec.get('z_expr', 'np.sin(np.sqrt(X**2 + Y**2))')}

fig = go.Figure(data=[go.Surface(x=X, y=Y, z=Z, colorscale='Viridis')])
fig.update_layout(title='{title}')
fig.show()
"""

    return f"# Plotly template not available for type: {plot_type}"

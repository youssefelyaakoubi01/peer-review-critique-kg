"""Shared look of the figures: colours, fonts, bars with a rounded data end.

One hue per side of a baseline (below / above), text in ink colours, hairline grid.
The palette was checked for colour-vision deficiencies.
"""

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath

NEGATIVE, POSITIVE, SECOND, NEUTRAL = "#e34948", "#2a78d6", "#eb6834", "#898781"
INK, MUTED, GRID, AXIS, MIDPOINT = "#0b0b0b", "#52514e", "#e1e0d9", "#c3c2b7", "#f0efec"
DIVERGING = LinearSegmentedColormap.from_list("red_gray_blue", [NEGATIVE, MIDPOINT, POSITIVE])


def style() -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "pdf.fonttype": 42})


def save(fig, path, **options) -> None:
    """Write a figure. A PDF carries no creation date: the same data give the same file."""
    if str(path).endswith(".pdf"):
        options["metadata"] = {"CreationDate": None}
    fig.savefig(path, **options)


def clean(ax, grid_axis: str | None = "x") -> None:
    """No frame, no tick marks, hairline grid behind the marks."""
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=0, colors=MUTED)


def bar(ax, y: float, value: float, height: float, colour: str) -> None:
    """Horizontal bar from zero to `value`: square at the baseline, rounded at the data
    end. The axes must have their final size and limits (shapes are computed in pixels)."""
    to_pixels = ax.transData.transform
    (x0, bottom), (x1, top) = to_pixels((0, y - height / 2)), to_pixels((value, y + height / 2))
    y0, y1 = sorted((bottom, top))  # the axis may be inverted
    radius = min(4 * ax.figure.dpi / 72, abs(x1 - x0), (y1 - y0) / 2)  # 4 points, less on a very short bar
    direction = 1 if x1 >= x0 else -1
    inner = x1 - direction * radius
    vertices = [(x0, y0), (inner, y0), (x1, y0), (x1, y0 + radius), (x1, y1 - radius), (x1, y1), (inner, y1), (x0, y1), (x0, y0)]
    codes = [MplPath.MOVETO, MplPath.LINETO, MplPath.CURVE3, MplPath.CURVE3, MplPath.LINETO, MplPath.CURVE3, MplPath.CURVE3,
             MplPath.LINETO, MplPath.CLOSEPOLY]
    path = MplPath(ax.transData.inverted().transform(vertices), codes)
    ax.add_patch(PathPatch(path, facecolor=colour, edgecolor="none", zorder=2))

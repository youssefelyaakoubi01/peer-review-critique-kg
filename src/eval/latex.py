"""booktabs tables of the paper, written from values read in the result files.

The caller gives cells that are already LaTeX: text goes through `escape`, numbers
through `number`, `signed`, `interval` or `count`.
"""

import math

SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
MISSING = "--"


def escape(text: object) -> str:
    return "".join(SPECIAL.get(character, character) for character in str(text))


def is_missing(value: object) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def number(value: float, decimals: int = 3) -> str:
    return MISSING if is_missing(value) else f"${value:.{decimals}f}$"


def signed(value: float, decimals: int = 3) -> str:
    """Number with its sign; a value that rounds to zero carries none."""
    if is_missing(value):
        return MISSING
    return f"${value:+.{decimals}f}$" if round(value, decimals) else f"${0:.{decimals}f}$"


def count(value: float) -> str:
    """Integer with a thin space between thousands."""
    return MISSING if is_missing(value) else "$" + f"{int(round(value)):,}".replace(",", r"\,") + "$"


def percent(share: float, decimals: int = 1) -> str:
    return MISSING if is_missing(share) else rf"${100 * share:.{decimals}f}\,\%$"


def interval(low: float, high: float, decimals: int = 3, sign: bool = False) -> str:
    if is_missing(low) or is_missing(high):
        return MISSING
    form = f"+.{decimals}f" if sign else f".{decimals}f"
    return f"$[{low:{form}},\\,{high:{form}}]$"


def bold(cell: str) -> str:
    """Bold cell; a cell in math mode stays in math mode."""
    if cell.startswith("$") and cell.endswith("$"):
        return rf"$\mathbf{{{cell[1:-1]}}}$"
    return rf"\textbf{{{cell}}}"


def table(columns: list[str], rows: list, caption: str, label: str, align: str | None = None, wide: bool = False,
          header: list[str] | None = None, size: str = "small", gap: int = 4) -> str:
    """One booktabs table. `rows` holds lists of cells, strings (title of a block of
    rows, over the whole width) and None (a rule). `header` lines are placed above the
    column names (grouped headings, already in LaTeX). `wide`: over the two columns of
    a two-column paper. `size`: font size command; `gap`: half the space between two
    columns, in points."""
    width = len(columns)
    align = align or "l" + "r" * (width - 1)
    environment = "table*" if wide else "table"
    lines = [rf"\begin{{{environment}}}[t]", r"\centering", rf"\{size}", rf"\setlength{{\tabcolsep}}{{{gap}pt}}", rf"\caption{{{caption}}}",
             rf"\label{{{label}}}", rf"\begin{{tabular}}{{@{{}}{align}@{{}}}}", r"\toprule", *(header or []), " & ".join(columns) + r" \\", r"\midrule"]
    for position, row in enumerate(rows):
        if row is None:
            lines.append(r"\midrule")
        elif isinstance(row, str):
            if position:
                lines.append(r"\addlinespace")
            lines.append(rf"\multicolumn{{{width}}}{{l}}{{\emph{{{row}}}}} \\")
        else:
            if len(row) != width:
                raise ValueError(f"table {label}: a row has {len(row)} cells for {width} columns")
            lines.append(" & ".join(row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", rf"\end{{{environment}}}", ""]
    return "\n".join(lines)

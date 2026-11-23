"""Values read in the result tables, with the file each one comes from.

Every number of the paper tables, of the consolidated figures and of the results
summary goes through `Sources`: a value is the cell of exactly one row of a CSV file of
results/tables/, and the files read are remembered so that they can be written next to
what was built from them.
"""

from pathlib import Path

import pandas as pd


class Sources:
    def __init__(self, tables_dir: Path, root: Path):
        self.tables_dir, self.root = Path(tables_dir), Path(root)
        self._tables: dict[str, pd.DataFrame] = {}
        self.used: dict[str, None] = {}  # names of the files read, in order

    def path(self, name: str) -> str:
        """Path of a table, relative to the repository root."""
        return (self.tables_dir / name).relative_to(self.root).as_posix()

    def table(self, name: str) -> pd.DataFrame:
        if name not in self._tables:
            path = self.tables_dir / name
            if not path.is_file():
                raise FileNotFoundError(f"result table missing: {self.path(name)}")
            self._tables[name] = pd.read_csv(path)
        self.used[name] = None
        return self._tables[name]

    def rows(self, name: str, **where) -> pd.DataFrame:
        """Rows whose columns equal the given values (None: missing value)."""
        table = self.table(name)
        keep = pd.Series(True, index=table.index)
        for column, wanted in where.items():
            if column not in table.columns:
                raise KeyError(f"{self.path(name)} has no column '{column}'")
            keep &= table[column].isna() if wanted is None else (table[column] == wanted)
        return table[keep]

    def row(self, name: str, **where) -> pd.Series:
        """The only row that matches; an error if there is none or several."""
        found = self.rows(name, **where)
        if len(found) != 1:
            raise LookupError(f"{self.path(name)}: {len(found)} rows match {where}, expected exactly one")
        return found.iloc[0]

    def value(self, name: str, column: str, **where):
        row = self.row(name, **where)
        if column not in row.index:
            raise KeyError(f"{self.path(name)} has no column '{column}'")
        return row[column]

    def take_used(self) -> list[str]:
        """Paths of the files read since the last call."""
        used, self.used = [self.path(name) for name in self.used], {}
        return used


def excludes_zero(low: float, high: float) -> bool:
    return bool(low > 0 or high < 0)


def verdict(low: float, high: float, p_value: float | None = None, alpha: float = 0.05) -> str:
    """The reading rule of the project: a difference is significant when its
    confidence interval excludes zero. When a test is given and does not reject at
    `alpha` although the interval excludes zero, the verdict says so."""
    if not excludes_zero(low, high):
        return "not significant"
    if p_value is not None and p_value >= alpha:
        return "interval excludes zero, test does not reject"
    return "significant"

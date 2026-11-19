"""ログ CSV（列は `LOG_COLUMNS`）の読み書き。"""

import csv

import numpy as np

from physlearn.api import LOG_COLUMNS, Command, Obs


def row(obs: Obs, cmd: Command) -> list[float]:
    return [obs.t, obs.ax, obs.ay, obs.az, obs.gx, obs.gy, obs.gz, cmd.left, cmd.right]


def write_csv(path, rows) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(LOG_COLUMNS)
        w.writerows(rows)


def read_csv(path) -> dict[str, np.ndarray]:
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        missing = set(LOG_COLUMNS) - set(r.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: 列が足りない {sorted(missing)}")
        data = [[float(x[c]) for c in LOG_COLUMNS] for x in r]
    return as_log(data)


def as_log(rows) -> dict[str, np.ndarray]:
    """行のリストを列ごとの配列にする（`read_csv` と同じ形）。"""
    a = np.array(rows, dtype=float).reshape(-1, len(LOG_COLUMNS))
    return {c: a[:, i] for i, c in enumerate(LOG_COLUMNS)}

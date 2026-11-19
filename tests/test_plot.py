import pytest

pytest.importorskip("matplotlib")

from physlearn import sim_log  # noqa: E402
from physlearn.log import write_csv  # noqa: E402
from physlearn.plot import main  # noqa: E402
from physlearn.sim import Params, SimPlant  # noqa: E402


@pytest.fixture
def csv(tmp_path):
    p = tmp_path / "log.csv"
    write_csv(p, sim_log(SimPlant(Params()))[:300])
    return p


@pytest.mark.parametrize(
    "args",
    [["log", "{csv}"], ["log", "{csv}", "--params", "{par}"], ["compare", "{csv}", "{csv}"], ["still", "{csv}"]],
)
def test_subcommands_write_png(tmp_path, csv, args):
    par = tmp_path / "p.json"
    Params().save(par)
    out = tmp_path / "x.png"
    main([a.format(csv=csv, par=par) for a in args] + ["--out", str(out)])
    assert out.stat().st_size > 0

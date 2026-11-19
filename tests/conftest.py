"""偽の XIAO を使う試験の共通の仕掛け。

壁時計も擬似端末 (pty) も使わない: PC が 1 行 readline するごとに偽物の時刻が 1 サンプル進む（fakexiao.VirtualPort）。
PC の負荷に依らず結果が毎回同じ。実時間の形（python -m physlearn.fakexiao）は tests/test_fakexiao.py の煙試験だけが通す。
"""

import pytest

from physlearn import HIDDEN
from physlearn.fakexiao import FakeXiao
from physlearn.sim import SimPlant


@pytest.fixture
def fake_factory():
    """make(axes) -> FakeXiao。f.ser を SerialPlant(ser=...) に渡す。"""
    return lambda axes="x,y,z": FakeXiao(SimPlant(HIDDEN, seed=1), axes, pty=False)

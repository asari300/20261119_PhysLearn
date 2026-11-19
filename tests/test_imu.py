import numpy as np

from physlearn.api import Command
from physlearn.imu import STAND_IN, allan, fit, main, simulate, stand_in, stats, yaw_deg
from physlearn.log import read_csv

N, DT = 3001, 0.01  # 30 s at 100 Hz


def test_stats_recover_bias_and_noise():
    s = stats(simulate(STAND_IN, N, DT)[0])
    assert abs(s["mean"]["gz"] - STAND_IN.gyro_bias) < 0.002
    assert abs(s["std"]["gz"] - STAND_IN.gyro_noise) < 0.002
    assert abs(s["std"]["az"] - STAND_IN.accel_noise) < 0.003
    assert abs(s["norm_err"]) < 0.01 and abs(s["roll"]) < 0.5 and abs(s["dt_mean"] - DT) < 1e-9


def test_drift_shrinks_after_bias_removal():
    s = stats(simulate(STAND_IN, N, DT)[0])
    assert abs(s["drift_raw"] - np.degrees(STAND_IN.gyro_bias * 30)) < 1.0
    assert abs(s["drift_fix"]) < 0.1 * abs(s["drift_raw"])


def test_allan_white_noise_falls_as_sqrt_tau():
    a = allan(simulate(STAND_IN, N, DT)[0]["gz"], DT)
    assert [t for t, _ in a] == [0.01, 0.1, 1.0]  # 10 s 以上は 30 s のログでは出さない
    assert 0.2 < a[1][1] / a[0][1] < 0.45  # 1/sqrt(10) ≈ 0.32


def test_turn_matches_truth():
    cmds = [Command(0.0, 0.0)] * 100 + [Command(-0.3, 0.3)] * 40 + [Command(0.0, 0.0)] * 200
    log, truth = simulate(STAND_IN, len(cmds) + 1, DT, seed=2, cmds=cmds)
    assert abs(yaw_deg(log, STAND_IN.gyro_bias) - truth) < 1.0


def test_r2s_sim_matches_real(tmp_path):
    real = simulate(STAND_IN, N, DT, seed=5)[0]
    p = fit(real)
    a, b = stats(real), stats(simulate(p, N, DT, seed=6)[0])
    assert abs(a["std"]["gz"] - b["std"]["gz"]) < 0.002
    assert abs(a["drift_raw"] - b["drift_raw"]) < 1.5


def test_cli_runs(tmp_path, capsys):
    still, turn = str(tmp_path / "s.csv"), str(tmp_path / "t.csv")
    stand_in(still, turn)
    assert len(read_csv(still)["t"]) == N
    main(["still", still])
    main(["turn", turn])
    main(["r2s", still, "--out", str(tmp_path / "p.json")])
    out = capsys.readouterr().out
    assert "Allan" in out and "尺度" in out and "直した sim" in out

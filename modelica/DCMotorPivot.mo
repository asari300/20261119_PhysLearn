// motor.py の mujoco_model() と同じ定数の DC モーター + 慣性（MSL の部品をつなぐ形）。
model DCMotorPivot
  import Modelica.Electrical.Analog.Basic;
  import Modelica.Mechanics.Rotational.Components;
  parameter Real u = 0.5 "duty（平均電圧 = V*u とみなす）";
  parameter Real V = 1.0, R = 1.0, L = 1e-6, Kt = 0.05;
  parameter Real b = 0.05/30 - Kt^2 "傾きを MuJoCo の 0.05/30 に合わせる粘性";
  parameter Real Jeff = 1.1222e-4 "その場旋回で 1 輪が見る慣性 (motor.py)";
  Modelica.Electrical.Analog.Sources.ConstantVoltage src(V = V*u);
  Basic.Resistor res(R = R);
  Basic.Inductor ind(L = L);
  Basic.RotationalEMF emf(k = Kt);
  Basic.Ground gnd;
  Components.Inertia load(J = Jeff);
  Components.Damper fric(d = b);
  Modelica.Mechanics.Rotational.Components.Fixed fix;
  Real yaw = load.w * 2 * 0.03 / 0.10 "ヨー角速度 rad/s";
equation
  connect(src.p, res.p);
  connect(res.n, ind.p);
  connect(ind.n, emf.p);
  connect(emf.n, src.n);
  connect(src.n, gnd.p);
  connect(emf.flange, load.flange_a);
  connect(load.flange_b, fric.flange_a);
  connect(fric.flange_b, fix.flange);
end DCMotorPivot;

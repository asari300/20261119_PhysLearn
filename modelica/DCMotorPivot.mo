// motor.py の mujoco_model() と同じ定数の DC モーター + 慣性（MSL の部品をつなぐ形）。
model DCMotorPivot
  import Modelica.Electrical.Analog.Basic;
  import Modelica.Mechanics.Rotational.Components;
  parameter Real u = 0.5 "duty（平均電圧 = V*u とみなす）";
  parameter Real Kt = 0.05, L = 1e-6;
  parameter Real R = Kt^2/(0.05/30) "傾き Kt^2/R を MuJoCo の 0.05/30 に合わせる (1.5)";
  parameter Real V = 0.05*R/Kt "停動 Kt*V/R を 0.05 に合わせる (1.5)";
  parameter Real b = 0 "粘性なし（傾きは全部が逆起電力）";
  parameter Real Rbat = 0 "電池の内部抵抗（13 章 演習 3。-override Rbat=0.5 など）";
  parameter Real Jeff = 1.1222e-4 "その場旋回で 1 輪が見る慣性 (motor.py)";
  Modelica.Electrical.Analog.Sources.ConstantVoltage src(V = V*u);
  Basic.Resistor res(R = R + Rbat);
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

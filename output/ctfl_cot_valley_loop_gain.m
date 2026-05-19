%% 电流模式COT谷值控制 - 环路增益验证
% 使用Nayan/Ridley采样数据模型
% 单相COT（Constant On-Time），谷值比较
%
% 参考: 
%   - Ridley, "A new continuous-time model for current-mode control"
%   - Nayan组采样保持模型
%
% 作者: Pandai Plus
% 日期: 2026-05-17

clear; clc; close all;

%% ======================== 系统参数 ========================
% Buck变换器参数
Vin = 12;           % 输入电压 (V)
Vout = 1.2;         % 输出电压 (V)
L = 0.47e-6;        % 电感 (H)
C = 470e-6;         % 输出电容 (F)
Resr = 5e-3;        % 电容ESR (Ohm)
Rload = 1.2;        % 负载电阻 (Ohm)  (= Vout/Iout, Iout=1A)
D = Vout/Vin;       % 稳态占空比
Dp = 1 - D;         % 1-D

% COT参数
fsw = 500e3;        % 开关频率 (Hz)
Tsw = 1/fsw;        % 开关周期 (s)
Ton = D * Tsw;      % 导通时间 (s)

% 电流采样参数
Rs = 0.1;           % 电流采样电阻 (Ohm)
Ri = Rs;            % 电流采样增益

% 斜坡补偿 (谷值控制用上升沿补偿)
% 对于谷值控制，斜坡补偿方向相反
Ma = 0;             % 斜坡补偿斜率 (A/s), 0表示无补偿

%% ======================== 电流纹波计算 ========================
% 电感电流纹波斜率
m1 = (Vin - Vout) / L;     % 上升斜率 (A/s)
m2 = Vout / L;              % 下降斜率 (A/s)

% 峰峰值纹波
delta_iL = m2 * Dp * Tsw;

% 谷值电流 (稳态)
Iout = Vout / Rload;
Ivalley = Iout - delta_iL / 2;

fprintf('=== 系统参数 ===\n');
fprintf('Vin = %.1f V, Vout = %.2f V, D = %.3f\n', Vin, Vout, D);
fprintf('L = %.2f uH, C = %.0f uF\n', L*1e6, C*1e6);
fprintf('fsw = %.0f kHz, Ton = %.1f ns\n', fsw/1e3, Ton*1e9);
fprintf('Iout = %.2f A, delta_iL = %.3f A\n', Iout, delta_iL);
fprintf('Ivalley = %.3f A\n\n', Ivalley);

%% ======================== 传递函数计算 ========================
s = tf('s');
wz = 1 / (Resr * C);           % ESR零点
wp = 1 / (Rload * C);          % 极点 (RC)
wesr = wz;                      % ESR零点频率

% ----- 1. 功率级传递函数 (连续时间，电压模式) -----
% 控制到输出 (Gvc): Vout(s)/D(s)
Gvc = Vin * (1 + s/wz) / (1 + s/(wp*Q) + s^2/(wp^2));
% 注意：对于Buck，更准确的是：
% Gvc(s) = Vin * (1 + s/wz) / (1 + s*Rload*C + s^2*L*C)
Gvc_volt = Vin * (1 + s*Resr*C) / (1 + s*Rload*C + s^2*L*C);

% 音频纹波衰减 (Gvg): Vout(s)/Vin(s)
Gvg = D * (1 + s*Resr*C) / (1 + s*Rload*C + s^2*L*C);

% ----- 2. 电流环内功率级 (电流模式) -----
% 对于电流模式控制，功率级被"内环"电流反馈改变
% 使用Nayan/Ridley的采样保持模型

% 采样保持效应
% H(s) = (1 - e^(-s*Tsw)) / (s*Tsw)  -> 一阶Pade近似
% 对于COT谷值控制，占空比调制不同

% 电流模式功率级传递函数 (Ridley模型)
% Gvc_cm(s) = Fm * H(s) * Gvc(s) / (1 + Fm * H(s) * Ri * Fi(s) * Gvc(s))
% 其中 Fi(s) 是电流采样滤波器

% 电感电流到占空比传递函数
Gid = Vin / (s*L);  % 简化：电感电流/占空比 = Vin/(sL)

% ----- 3. 调制器增益 Fm -----
% 对于COT谷值控制：
% Fm = 1 / (Rs * (m1 + m2) * Ton)   [Ridley模型]
% 或者更准确的：
% Fm = Tsw / (Rs * (m1 - (-Ma)))    [考虑斜坡补偿]

if Ma == 0
    Fm = 1 / (Ri * (m1 + m2) * Ton);
else
    % 带斜坡补偿
    Fm = 1 / (Ri * (m1 + Ma));
end

fprintf('=== 调制器参数 ===\n');
fprintf('m1 = %.2e A/s (上升斜率)\n', m1);
fprintf('m2 = %.2e A/s (下降斜率)\n', m2);
fprintf('Fm = %.4f (调制器增益)\n\n', Fm);

%% ======================== 电流模式建模 (Nayan/Ridley) ========================
% Ridley电流模式小信号模型
%
%          ┌─────────┐     ┌─────────┐
% Vc ──►──┤  调制器  ├────►│ 功率级  ├──► Vout
%          │   Fm    │     │  Gp(s)  │
%          └─────────┘     └────┬────┘
%               ▲               │
%               │    ┌─────┐    │
%               └────┤ Ri  │◄───┘
%                    │Fm*H │
%                    └─────┘
%                    电流反馈

% ----- 采样保持传递函数 -----
% 一阶近似 (有效采样)
% Hs(s) ≈ 1 / (1 + s/(pi*fsw))   [低频近似]
w_sample = pi * fsw;

% 更精确的采样保持 (考虑谷值控制延迟)
% 对于COT谷值控制，采样在谷值时刻
% 延迟 ≈ Dp*Tsw/2
td = Dp * Tsw / 2;
Hs_delay = exp(-s * td);

% ----- 电流环路增益 -----
% Ti(s) = Fm * Ri * Gid(s) * Hs(s)
Ti = Fm * Ri * Gid * 1/(1 + s/w_sample);

% ----- 电压环功率级 (电流模式等效) -----
% Gvc_cm(s) = Gvc(s) / (1 + Ti(s))
% 简化后：
% Gvc_cm(s) ≈ Rs * Rload / (2*Ri) * (1 + s/wz) / (1 + s/wp_cm)
wp_cm = 2 / (Rload * C);  % 电流模式主极点

% 更精确的电流模式功率级 (考虑采样)
% 使用Middlebrook的平均模型
Gvc_cm = Gvc_volt / (1 + Ti);

% ----- 调制器传递函数 (包含采样) -----
Fm_total = Fm * 1/(1 + s/w_sample) * Hs_delay;

fprintf('=== 电流模式参数 ===\n');
fprintf('采样频率: w_sample = pi*fsw = %.2e rad/s\n', w_sample);
fprintf('采样延迟: td = %.1f ns\n', td*1e9);
fprintf('电流模式主极点: wp_cm = %.2e rad/s (%.1f kHz)\n', wp_cm, wp_cm/(2*pi*1e3));
fprintf('ESR零点: wz = %.2e rad/s (%.1f kHz)\n\n', wz, wz/(2*pi*1e3));

%% ======================== 补偿器设计 ========================
% Type III 补偿器 (或者用Type II)
% 针对电流模式，通常用Type II就够了

% 补偿器参数
fc = fsw / 10;          % 穿越频率 (fs/10)
phi_m = 60;             % 目标相位裕度 (度)

% Type II补偿器: Gc(s) = Kc * (1 + s/wz_c) / (s * (1 + s/wp_c))
% 简化设计
R1 = 10e3;              % 补偿器电阻
C1 = 1e-9;              % 补偿器电容
C2 = 100e-12;           % 补偿器电容2

% 补偿器传递函数
Gc = (1 + s*R1*C1) / (s * R1 * (C1 + C2) * (1 + s*R1*C1*C2/(C1+C2)));

% 反馈分压
Rtop = 100e3;           % 上分压电阻
Rbot = 100e3;           % 下分压电阻
Hfb = Rbot / (Rtop + Rbot);  % 反馈系数

fprintf('=== 补偿器参数 ===\n');
fprintf('穿越频率目标: fc = %.1f kHz\n', fc/1e3);
fprintf('反馈系数: Hfb = %.3f\n\n', Hfb);

%% ======================== 环路增益计算 ========================
% ----- 环路增益 T(s) -----
% T(s) = Gc(s) * Fm_total(s) * Gvc(s) * Hfb
% 对于电流模式：
% T(s) = Gc(s) * Gvc_cm(s) * Hfb

T_loop = Gc * Gvc_cm * Hfb;

% ----- 开环传递函数 (不含反馈) -----
T_open = Gc * Fm_total * Gvc_volt * Hfb;

% ----- 闭环传递函数 -----
% Vout/Vref = Gvc_cm * Gc / (1 + T_loop)
Gcl = Gvc_cm * Gc / (1 + T_loop);

% 输入到输出 (闭环)
Gcl_vin = Gvg / (1 + T_loop);

% 音频衰减 (闭环)
PSRR = Gcl_vin;

%% ======================== 绘制波特图 ========================
f = logspace(1, 7, 1000);   % 10 Hz 到 10 MHz
w = 2*pi*f;

figure('Name', '电流模式COT谷值控制 - 环路增益分析', 'Position', [100 100 1200 800]);

% ----- 子图1: 功率级传递函数 -----
subplot(2,3,1);
[mag_vc, phase_vc] = bode(Gvc_volt, w);
mag_vc = squeeze(mag_vc);
phase_vc = squeeze(phase_vc);

yyaxis left;
semilogx(f, 20*log10(mag_vc), 'b-', 'LineWidth', 1.5);
ylabel('幅值 (dB)');
yyaxis right;
semilogx(f, phase_vc, 'r--', 'LineWidth', 1);
ylabel('相位 (度)');
grid on;
title('功率级 G_{vc}(s) (电压模式)');
xlabel('频率 (Hz)');
legend('幅值', '相位', 'Location', 'southwest');
xlim([10 1e7]);

% ----- 子图2: 调制器传递函数 -----
subplot(2,3,2);
[mag_fm, phase_fm] = bode(Fm_total, w);
mag_fm = squeeze(mag_fm);
phase_fm = squeeze(phase_fm);

yyaxis left;
semilogx(f, 20*log10(mag_fm), 'b-', 'LineWidth', 1.5);
ylabel('幅值 (dB)');
yyaxis right;
semilogx(f, phase_fm, 'r--', 'LineWidth', 1);
ylabel('相位 (度)');
grid on;
title('调制器 F_m(s) (含采样保持)');
xlabel('频率 (Hz)');
legend('幅值', '相位', 'Location', 'southwest');
xlim([10 1e7]);

% ----- 子图3: 电流模式功率级 -----
subplot(2,3,3);
[mag_cm, phase_cm] = bode(Gvc_cm, w);
mag_cm = squeeze(mag_cm);
phase_cm = squeeze(phase_cm);

yyaxis left;
semilogx(f, 20*log10(mag_cm), 'b-', 'LineWidth', 1.5);
ylabel('幅值 (dB)');
yyaxis right;
semilogx(f, phase_cm, 'r--', 'LineWidth', 1);
ylabel('相位 (度)');
grid on;
title('电流模式功率级 G_{vc,cm}(s)');
xlabel('频率 (Hz)');
legend('幅值', '相位', 'Location', 'southwest');
xlim([10 1e7]);

% ----- 子图4: 环路增益 -----
subplot(2,3,4);
[mag_loop, phase_loop] = bode(T_loop, w);
mag_loop = squeeze(mag_loop);
phase_loop = squeeze(phase_loop);

yyaxis left;
semilogx(f, 20*log10(mag_loop), 'b-', 'LineWidth', 1.5);
ylabel('幅值 (dB)');
hold on;
% 标记0dB线
yline(0, 'k--', 'LineWidth', 0.5);
yyaxis right;
semilogx(f, phase_loop, 'r-', 'LineWidth', 1.5);
ylabel('相位 (度)');
hold on;
yline(-180, 'k--', 'LineWidth', 0.5);
grid on;
title('环路增益 T(s)');
xlabel('频率 (Hz)');
legend('幅值', '', '相位', '', 'Location', 'southwest');
xlim([10 1e7]);

% 计算相位裕度
[Gm, Pm, Wcg, Wcp] = margin(T_loop);
fprintf('=== 环路增益指标 ===\n');
fprintf('增益裕度: %.1f dB @ %.1f kHz\n', 20*log10(Gm), Wcg/(2*pi*1e3));
fprintf('相位裕度: %.1f 度 @ %.1f kHz\n', Pm, Wcp/(2*pi*1e3));
fprintf('穿越频率: %.1f kHz\n\n', Wcp/(2*pi*1e3));

% ----- 子图5: 闭环传递函数 -----
subplot(2,3,5);
[mag_cl, phase_cl] = bode(Gcl, w);
mag_cl = squeeze(mag_cl);
phase_cl = squeeze(phase_cl);

yyaxis left;
semilogx(f, 20*log10(mag_cl), 'b-', 'LineWidth', 1.5);
ylabel('幅值 (dB)');
yyaxis right;
semilogx(f, phase_cl, 'r--', 'LineWidth', 1);
ylabel('相位 (度)');
grid on;
title('闭环传递函数 V_{out}/V_{ref}');
xlabel('频率 (Hz)');
legend('幅值', '相位', 'Location', 'southwest');
xlim([10 1e7]);

% ----- 子图6: 音频衰减 (PSRR) -----
subplot(2,3,6);
[mag_psrr, phase_psrr] = bode(PSRR, w);
mag_psrr = squeeze(mag_psrr);
phase_psrr = squeeze(phase_psrr);

yyaxis left;
semilogx(f, 20*log10(mag_psrr), 'b-', 'LineWidth', 1.5);
ylabel('幅值 (dB)');
yyaxis right;
semilogx(f, phase_psrr, 'r--', 'LineWidth', 1);
ylabel('相位 (度)');
grid on;
title('音频衰减 PSRR (V_{out}/V_{in})');
xlabel('频率 (Hz)');
legend('幅值', '相位', 'Location', 'southwest');
xlim([10 1e7]);

% 保存图片
saveas(gcf, '/home/rosemary/pandai-plus/output/loop_gain_bode.png');
fprintf('波特图已保存: /home/rosemary/pandai-plus/output/loop_gain_bode.png\n\n');

%% ======================== 阶跃响应验证 ========================
figure('Name', '瞬态响应', 'Position', [100 100 800 400]);

% 负载阶跃响应 (闭环)
t_step = 0:1e-7:1e-3;   % 0到1ms
% 等效负载扰动 -> 输出电压变化
% 使用闭环传递函数
sys_cl = ss(Gcl);
[y_cl, t_out] = step(sys_cl, t_step);

subplot(1,2,1);
plot(t_out*1e3, y_cl, 'b-', 'LineWidth', 1.5);
grid on;
title('参考电压阶跃响应 (闭环)');
xlabel('时间 (ms)');
ylabel('V_{out} 归一化');
xlim([0 0.5]);

% 开环阶跃响应
sys_open = ss(Gvc_cm);
[y_open, t_open] = step(sys_open, t_step);

subplot(1,2,2);
plot(t_open*1e3, y_open, 'r-', 'LineWidth', 1.5);
grid on;
title('参考电压阶跃响应 (开环功率级)');
xlabel('时间 (ms)');
ylabel('V_{out} 归一化');
xlim([0 0.5]);

saveas(gcf, '/home/rosemary/pandai-plus/output/step_response.png');
fprintf('阶跃响应已保存: /home/rosemary/pandai-plus/output/step_response.png\n\n');

%% ======================== 详细传递函数输出 ========================
fprintf('========================================\n');
fprintf('         传递函数汇总\n');
fprintf('========================================\n\n');

fprintf('1. 功率级 (电压模式) Gvc(s):\n');
disp(Gvc_volt);

fprintf('\n2. 电流模式功率级 Gvc_cm(s):\n');
disp(Gvc_cm);

fprintf('\n3. 调制器 Fm_total(s):\n');
disp(Fm_total);

fprintf('\n4. 环路增益 T(s):\n');
disp(T_loop);

fprintf('\n5. 闭环传递函数 Gcl(s):\n');
disp(Gcl);

%% ======================== 频率特性关键点 ========================
fprintf('========================================\n');
fprintf('         频率特性关键点\n');
fprintf('========================================\n');

% 找关键频率点
f_points = [100, 1e3, 10e3, 100e3, fsw, fsw/2];
for fi = f_points
    w_i = 2*pi*fi;
    [mag_i, phase_i] = bode(T_loop, w_i);
    fprintf('f = %8.0f Hz: |T| = %6.1f dB, phase = %6.1f deg\n', ...
            fi, 20*log10(squeeze(mag_i)), squeeze(phase_i));
end

fprintf('\n');
fprintf('ESR零点: f_esr = %.1f kHz\n', wz/(2*pi*1e3));
fprintf('电流模式极点: f_cm = %.1f kHz\n', wp_cm/(2*pi*1e3));
fprintf('采样频率/2: f_nyquist = %.0f kHz\n', fsw/2/1e3);

fprintf('\n完成！\n');

% ===============================
%   V1.0
% ===============================
% function sim_out = run_buck_sim(T_sim, vin_time, vin_value, load_time, load_value)
%     % =========================================================================
%     % 函数名: run_buck_sim
%     % 功能: 供 Python 引擎调用的标准化接口，用于动态注入参数并静默运行 Simulink 模型
%     % 输入参数:
%     %   T_sim      - 仿真总时长 (秒), 例如 0.1
%     %   vin_time   - 输入电压时间戳数组, 例如 [0, 0.03, 0.03, 0.05, 0.05, 0.1]
%     %   vin_value  - 输入电压幅值数组, 例如 [16, 16, 20, 20, 16, 16]
%     %   load_time  - 负载扰动开关时间戳数组, 例如 [0, 0.02, 0.02, 0.1]
%     %   load_value - 负载扰动开关状态数组 (1为闭合并联，0为断开), 例如 [1, 1, 0, 0]
%     % 输出参数:
%     %   sim_out    - 包含所有 Outport 数据的 Simulink 仿真结果对象
%     % =========================================================================
% 
%     % 1. 读取模糊控制规则并注入基础工作区 (Base Workspace)
%     % Simulink 的 Fuzzy Logic Controller 模块默认在 Base Workspace 查找变量
%     fis_obj = readfis('data\fuzzy_rules.fis');
%     assignin('base', 'fuzzy_rules', fis_obj);
% 
%     % 2. 构造外部输入信号的数据集 (Dataset)
%     % 将 Python 传进来的离散一维数组转换为 MATLAB 的 timeseries 对象
%     vin_ts = timeseries(vin_value, vin_time);
%     load_ts = timeseries(load_value, load_time);
% 
%     % 打包进 Dataset (名字必须与 Configuration Parameters 中填写的完全一致)
%     Input_Signals = Simulink.SimulationData.Dataset();
%     Input_Signals = Input_Signals.addElement(vin_ts, 'Vin_in');    % 对应名为 Vin_in 的 Inport
%     Input_Signals = Input_Signals.addElement(load_ts, 'Load_g_in'); % 对应名为 Load_g_in 的 Inport
% 
%     % 将 Dataset 注入基础工作区，供 Simulink 的 Input 读取
%     assignin('base', 'Input_Signals', Input_Signals);
% 
%     % 3. 配置并静默运行仿真
%     model_name = 'plant_model'; % 你实际的 .slx 文件名
%     load_system(model_name);    % 后台加载模型，不弹出图形界面，防止阻塞 Python
% 
%     % 构造仿真输入对象，动态覆盖仿真结束时间
%     simIn = Simulink.SimulationInput(model_name);
%     simIn = simIn.setModelParameter('StopTime', num2str(T_sim));
% 
%     % 运行仿真 (静默模式)
%     sim_out = sim(simIn);
% end

% ===============================
%   V2.0
% ===============================
% function sim_out = run_buck_sim(T_sim, vin_time, vin_value, load_time, load_value)
% 
% %     % =========================================================================
% %     % 函数名: run_buck_sim
% %     % 功能: 供 Python 引擎调用的标准化接口，用于动态注入参数并静默运行 Simulink 模型
% %     % 输入参数:
% %     %   T_sim      - 仿真总时长 (秒), 例如 0.1
% %     %   vin_time   - 输入电压时间戳数组, 例如 [0, 0.03, 0.03, 0.05, 0.05, 0.1]
% %     %   vin_value  - 输入电压幅值数组, 例如 [16, 16, 20, 20, 16, 16]
% %     %   load_time  - 负载扰动开关时间戳数组, 例如 [0, 0.02, 0.02, 0.1]
% %     %   load_value - 负载扰动开关状态数组 (1为闭合并联，0为断开), 例如 [1, 1, 0, 0]
% %     % 输出参数:
% %     %   sim_out    - 包含所有 Outport 数据的 Simulink 仿真结果对象
% %     % =========================================================================
% 
%     % 1. 读取模糊规则
%     fis_obj = readfis('data\fuzzy_rules.fis');
%     assignin('base', 'fuzzy_rules', fis_obj);
% 
%     % 2. 将输入的数组转换为 timeseries，并打包进 Dataset
%     vin_ts = timeseries(vin_value, vin_time);
%     load_ts = timeseries(load_value, load_time);
% 
%     Input_Signals = Simulink.SimulationData.Dataset();
%     Input_Signals = Input_Signals.addElement(vin_ts, 'Vin_in');
%     Input_Signals = Input_Signals.addElement(load_ts, 'Load_g_in');
% 
%     % 注入到基础工作区
%     assignin('base', 'Input_Signals', Input_Signals);
% 
%     % 3. 配置仿真并静默运行
%     model_name = 'plant_model'; % 确保名字与你的 slx 文件一致
%     load_system(model_name);
% 
%     simIn = Simulink.SimulationInput(model_name);
%     simIn = simIn.setModelParameter('StopTime', num2str(T_sim));
% 
%     sim_out = sim(simIn);
% end


% ===============================
%   V3.0
% ===============================
% 注意：输出参数变成了三个纯数组：时间 t_out，电压 vout_data，电流 i_ind_data
function [t_out, vout_data, i_ind_data] = run_buck_sim(T_sim, vin_time, vin_value, load_time, load_value)
    % 1. 读取模糊规则
    fis_obj = readfis('data\fuzzy_rules.fis');
    assignin('base', 'fuzzy_rules', fis_obj);

    % 2. 构造 Dataset 并注入
    vin_ts = timeseries(vin_value, vin_time);
    load_ts = timeseries(load_value, load_time);

    Input_Signals = Simulink.SimulationData.Dataset();
    Input_Signals = Input_Signals.addElement(vin_ts, 'Vin_in');
    Input_Signals = Input_Signals.addElement(load_ts, 'Load_g_in');
    assignin('base', 'Input_Signals', Input_Signals);

    % 3. 运行仿真
    model_name = 'plant_model'; 
    load_system(model_name);
    
    simIn = Simulink.SimulationInput(model_name);
    simIn = simIn.setModelParameter('StopTime', num2str(T_sim));
    sim_out = sim(simIn);
    
    % 4. 【新增】在 MATLAB 内部把复杂对象解包成一维纯数字数组，再发给 Python
    vout_obj = sim_out.yout.getElement('Vout_out').Values;
    i_ind_obj = sim_out.yout.getElement('I_ind_out').Values;
    
    t_out      = vout_obj.Time;
    vout_data  = vout_obj.Data;
    i_ind_data = i_ind_obj.Data;
end

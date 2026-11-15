# test_buck_robustness.py
import pytest
import numpy as np
import matplotlib.pyplot as plt
import os
from src import matlab_engine_api
from src.matlab_engine_api import BuckSimEngine

# 从数据模块中导入数据 
from test_data import T_SIM, VIN_TIME, LOAD_TIME, TEST_CASES

# ==========================================
# 引擎生命周期管理 (Fixture)
# ==========================================
@pytest.fixture(scope="session")
def engine():
    print("\n[System] 初始化自动化测试环境...")
    os.makedirs("test_reports", exist_ok=True)
    
    eng = BuckSimEngine()
    yield eng  
    eng.close() 

# ==========================================
# 核心测试与智能断言逻辑
# ==========================================
@pytest.mark.parametrize("case_name, vin_val, load_val, criteria", TEST_CASES)
def test_fuzzy_controller_robustness(engine, case_name, vin_val, load_val, criteria):
    print(f"\n[Test] 正在执行: {case_name}")
    
    # 1. 执行仿真
    result = engine.run_simulation(T_SIM, VIN_TIME, vin_val, LOAD_TIME, load_val)
    time_array = result['time']
    vout_array = result['vout']
    
    # 2. 自动生成测试波形报告
    plt.figure(figsize=(10, 5))
    plt.plot(time_array, vout_array, label="Vout (Fuzzy PID)", color='#1f77b4', linewidth=2)
    plt.axhline(y=12.0, color='black', linestyle=':', label='Target (12V)')
    
    if vin_val[0] != vin_val[-1]: 
        plt.axvline(x=0.015, color='red', linestyle='--', alpha=0.7, label='Vin Disturbance')
    if load_val[0] != load_val[-1]: 
        plt.axvline(x=0.030, color='green', linestyle='--', alpha=0.7, label='Load Disturbance')
        
    plt.title(f"Robustness Test: {case_name}")
    plt.xlabel("Time (s)")
    plt.ylabel("Output Voltage (V)")
    plt.ylim(10.0, 14.0)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    
    report_path = f"test_reports/{case_name}.png"
    plt.savefig(report_path, dpi=150)
    plt.close()
    
    # ==========================================
    # 3. 动态断言判断 (根据数据文件中传入的标准)
    # ==========================================
    
    # A. 所有用例都必须通过的“稳态测试”
    steady_state_mask = time_array > 0.045
    steady_vout = vout_array[steady_state_mask]
    final_avg_voltage = np.mean(steady_vout)
    steady_error = abs(final_avg_voltage - 12.0)
    
    tolerance = criteria.get("steady_tolerance", 0.2)
    assert steady_error <= tolerance, f"稳态恢复失败: 当前误差 {steady_error:.3f}V，超出允许范围 {tolerance}V"
    
    # B. 针对性动态过程测试
    case_type = criteria.get("type")
    
    if case_type == "nominal":
        max_v = np.max(vout_array)
        assert max_v < criteria["max_overshoot"], f"启动超调过大: {max_v:.2f}V"
        
    elif case_type == "high_vin":
        # 只抓取 0.015 - 0.030 期间的峰值
        window_mask = (time_array > 0.015) & (time_array < 0.030)
        max_v = np.max(vout_array[window_mask])
        assert max_v < criteria["max_overshoot"], f"抗过压能力不足，超调: {max_v:.2f}V"
        
    elif case_type in ["low_vin", "heavy_load", "combined"]:
        # 抓取对应扰动后的最低谷
        window_mask = time_array > (0.015 if case_type == "low_vin" else 0.030)
        min_v = np.min(vout_array[window_mask])
        assert min_v > criteria["min_undershoot"], f"电压跌落过深: {min_v:.2f}V"
        
    print(f"[Test] {case_name} 验收通过！稳态误差: {steady_error:.4f}V")


"""
import pytest
import numpy as np
import matplotlib.pyplot as plt
import os
import time
from src import matlab_engine_api
from src.matlab_engine_api import BuckSimEngine  # 导入你写好的引擎类

# ==========================================
# 1. 引擎生命周期管理 (Fixture)
# ==========================================
@pytest.fixture(scope="session")
def engine():
    
    #全局共享的 MATLAB 引擎实例。
    #所有 5 个用例都会复用这个引擎，跑完后自动释放。
    
    # 建立测试报告存放目录
    os.makedirs("test_reports", exist_ok=True)
    
    eng = BuckSimEngine()
    yield eng  # 将控制权交给测试用例
    eng.close() # 所有测试结束后执行清理

# ==========================================
# 2. 测试用例数据矩阵 (参数化)
# ==========================================
# 统一定义仿真时长
T_SIM = 0.05 

# 统一的时间轴 (0.015s 发生电压扰动，0.03s 发生负载扰动)
VIN_TIME = [0.0, 0.015, 0.015, 0.05]
LOAD_TIME = [0.0, 0.030, 0.030, 0.05]

# 用例格式: ("用例名称", vin_value数组, load_value数组)
# 物理映射: load_value = 0 (10欧姆), load_value = 1 (5欧姆重载)
demo_cases = [
    (
        "Case1_Nominal", 
        [24.0, 24.0, 24.0, 24.0],  # Vin 全程 24V
        [0.0, 0.0, 0.0, 0.0]       # 负载全程 10欧
    ),
    (
        "Case2_High_Vin", 
        [24.0, 24.0, 28.0, 28.0],  # 0.015s 突变至 28V
        [0.0, 0.0, 0.0, 0.0]
    ),
    (
        "Case3_Low_Vin", 
        [24.0, 24.0, 20.0, 20.0],  # 0.015s 跌落至 20V
        [0.0, 0.0, 0.0, 0.0]
    ),
    (
        "Case4_Heavy_Load", 
        [24.0, 24.0, 24.0, 24.0], 
        [0.0, 0.0, 1.0, 1.0]       # 0.030s 信号变为 1 (5欧重载)
    ),
    (
        "Case5_Combined_Extreme", 
        [24.0, 24.0, 28.0, 28.0],  # 0.015s 高压冲击
        [0.0, 0.0, 1.0, 1.0]       # 0.030s 重载冲击
    )
]

# ==========================================
# 3. 核心测试与断言逻辑
# ==========================================
@pytest.mark.parametrize("case_name, vin_val, load_val", demo_cases)
def test_fuzzy_controller_robustness(engine, case_name, vin_val, load_val):
    print(f"\n[Test] 正在执行用例: {case_name}")
    
    # 1. 触发仿真引擎
    result = engine.run_simulation(T_SIM, VIN_TIME, vin_val, LOAD_TIME, load_val)
    
    time_array = result['time']
    vout_array = result['vout']
    
    # 2. 自动生成并保存波形报告 (面试高分项)
    plt.figure(figsize=(10, 6))
    
    # 绘制主波形
    plt.plot(time_array, vout_array, label="Vout (Fuzzy PID)", color='#1f77b4', linewidth=2)
    
    # 绘制参考线与扰动事件线
    plt.axhline(y=12.0, color='black', linestyle=':', label='Target (12V)')
    
    if vin_val[0] != vin_val[-1]: # 如果存在电压扰动
        plt.axvline(x=0.015, color='red', linestyle='--', alpha=0.7, label='Vin Disturbance')
    if load_val[0] != load_val[-1]: # 如果存在负载扰动
        plt.axvline(x=0.030, color='green', linestyle='--', alpha=0.7, label='Load Disturbance (5Ω)')
        
    plt.title(f"Robustness Test: {case_name}")
    plt.xlabel("Time (s)")
    plt.ylabel("Output Voltage (V)")
    plt.ylim(10.0, 14.0)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right')
    
    report_path = f"test_reports/{case_name}.png"
    plt.savefig(report_path, dpi=150)
    plt.close()
    print(f"[Test] 波形已保存至: {report_path}")
    
    # 3. 数据切片与自动化裁判 (断言)
    # 提取 0.045s 到 0.050s (即负载扰动 15ms 后) 的数据，验证最终稳态
    steady_state_mask = time_array > 0.045
    steady_vout = vout_array[steady_state_mask]
    
    # 计算均值以滤除开关纹波的影响
    final_avg_voltage = np.mean(steady_vout)
    steady_error = abs(final_avg_voltage - 12.0)
    
    print(f"[Test] {case_name} 稳态误差: {steady_error:.4f}V")
    
    # 工程容忍度设定为 0.2V。如果误差大于 0.2V，用例标红报错！
    assert steady_error <= 0.2, f"稳态恢复失败！当前最终电压为 {final_avg_voltage:.2f}V，误差超过 0.2V 限值"
"""
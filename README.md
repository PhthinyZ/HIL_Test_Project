## 环境依赖 (Environment & Dependencies)

本项目使用 Conda 进行虚拟环境管理。核心运行环境为 **Python 3.10** 与 **MATLAB R2024b**。

### 核心 Python 依赖包

项目依赖可主要划分为以下三个模块：

**1. 引擎与通信 (Engine & API)**
* `matlabengine (24.2.2)`: MATLAB 官方提供的 Python API，用于实现 Python 对 Simulink 模型的跨语言后台调度与生命周期管理。

**2. 自动化测试框架 (Testing Framework)**
* `pytest (9.1.1)`: 核心测试驱动框架，支持基于数据驱动 (DDT) 的批量工况注入。
* `pytest-html (4.2.0)`: 用于在测试执行结束后，自动生成包含超调量、调节时间等关键电学指标的可视化测试报告。
* `pytest-rerunfailures (16.7)`: 提供仿真超时或引擎意外阻断时的自动重试容错机制。
* `pytest-xdist (3.8.0)`: （预留）用于测试任务的分布式或并发调度。

**3. 数据分析与可视化 (Data Processing)**
* `numpy (2.2.5)` & `pandas (2.3.3)`: 用于处理 Simulink 返回的遥测时间序列数据，执行稳态误差、峰值时间的计算与自动化断言。
* `matplotlib (3.10.9)`: 用于绘制并输出阶跃响应波形与模糊控制规则曲面。

### 环境复现说明

可以通过仓库提供的 `environment.yml` 文件一键还原开发环境：
```bash
conda env create -f environment.yml
conda activate py310

## 数据流向架构 (Data Flow Architecture)

本项目的数据流呈现单向闭环特征，实现了从“测试意图”到“物理仿真”再到“结果判定”的全自动化。具体流向分为以下五个阶段：

### 1. 测试数据组装 (Data Preparation) -> Python 端
* **流向**: `test_data.py` -> `pytest.mark.parametrize`
* **机制**: Python 读取预先定义的测试工况矩阵。这些工况包括：模糊控制器的初始规则权重、输入电压突变设定值、负载电阻跳变时间点等。Pytest 的参数化机制将这些矩阵解构为独立的测试实例。

### 2. 跨语言参数注入 (Parameter Injection) -> Python to MATLAB
* **流向**: Python 变量 -> `matlabengine` -> MATLAB Base Workspace
* **机制**: 通过 MATLAB Engine API API，Python 将当前测试实例的参数（如 `Kp`, `Ki`, `Load_R` 等）以键值对的形式，强制写入 MATLAB 的基础工作区。这一步完成了测试参数从 Python 内存到 MATLAB 内存的跨界转换。

### 3. 仿真模型触发 (Simulation Execution) -> MATLAB to Simulink
* **流向**: MATLAB Workspace -> `sim()` 函数 -> Simulink Model
* **机制**: Python 发送执行指令（例如 `eng.sim('DC_DC_Buck_Fuzzy')`）。Simulink 模型启动，自动抓取 Workspace 中刚被注入的模糊控制参数和硬件工况进行求解运算。此时，控制权短暂交接给底层电气求解器。

### 4. 遥测数据回传 (Data Extraction) -> Simulink to Python
* **流向**: Simulink Outport -> MATLAB Workspace -> `matlabengine` -> Python
* **机制**: 仿真结束后，Simulink 将输出电压、电感电流等关键时间序列数据（Timeseries/Array）输出至工作区。Python 通过引擎 API 重新接管控制权，将这些 double 类型的数组拉取回 Python 内存，并转化为 Numpy/Pandas 格式以便后续处理。

### 5. 指标计算与断言 (Assertion & Visualization) -> Python 端
* **流向**: 原始数据数组 -> 核心算法计算 -> Pytest `assert` / Matplotlib
* **机制**: Python 脚本对回传的电压波形进行清洗，自动计算出三大核心电学指标：**超调量 (Overshoot)**、**调节时间 (Settling Time)** 和 **稳态误差 (Steady-state Error)**。
  * 将计算结果与预设阈值进行 `assert` 比对，判定测试用例通过 (Pass) 或失败 (Fail)。
  * 触发 Matplotlib 绘制当前工况的阶跃响应曲线，并与测试报告 (`pytest-html`) 绑定输出。
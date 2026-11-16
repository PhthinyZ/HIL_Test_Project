## Environment & Dependencies

This project uses Conda for virtual environment management. The core runtime environment consists of **Python 3.10** and **MATLAB R2024b**.

### Core Python dependencies

**1. Engine & API**
* `matlabengine (24.2.2)`: The official Python API provided by MATLAB, designed to enable cross-language background scheduling and lifecycle management of Simulink models from Python.

**2. Testing Framework**
* `pytest (9.1.1)`: Core test-driven framework, supporting batch scenario injection based on data-driven testing (DDT).
* `pytest-html (4.2.0)`: Used to automatically generate a visual test report—containing key electrical metrics such as overshoot and settling time—upon completion of test execution.
* `pytest-rerunfailures (16.7)`: Provides an automated retry and fault-tolerance mechanism for cases where a simulation times out or the engine is unexpectedly interrupted.
* `pytest-xdist (3.8.0)`: (Reserved) For distributed or concurrent scheduling of test tasks.

**3. Data Processing**
* `numpy (2.2.5)` & `pandas (2.3.3)`: Used for processing telemetry time-series data returned by Simulink, performing calculations for steady-state error and peak time, and executing automated assertions.
* `matplotlib (3.10.9)`: Used for plotting and outputting step response.

### Instructions for Environment Reproduction

You can restore the development environment in one step using the `environment.yml` file provided in the repository:
```bash
conda env create -f environment.yml
conda activate py310
```

## Data Flow Architecture

### 1. Data Preparation -> Python
* **Workflow**: `test_data.py` -> `pytest.mark.parametrize`
* **Mechanism**: Python reads a pre-defined matrix of test scenarios. These scenarios encompass parameters such as the initial rule weights of the fuzzy controller, setpoint values ​​for sudden input voltage changes, and the timing of load resistance shifts. The parameterization mechanism in Pytest then deconstructs this matrix into individual test cases.

### 2. Parameter Injection -> Python to MATLAB
* **Workflow**: Python variables → `matlabengine` → MATLAB Base Workspace
* **Mechanism**: Using the MATLAB Engine API, Python injects the parameters of the current test instance (such as `Kp`, `Ki`, `Load_R`, etc.) into the MATLAB Base Workspace as key-value pairs. This process facilitates the transfer of test parameters from Python memory into MATLAB memory.

### 3. Simulation Execution -> MATLAB to Simulink
* **Workflow**: MATLAB Workspace -> `sim()` function -> Simulink Model
* **Mechanism**: Python issues an execution command (e.g., `eng.sim('DC_DC_Buck_Fuzzy')`). The Simulink model launches and automatically retrieves the fuzzy control parameters and hardware operating conditions—which have just been injected into the Workspace—to perform its computations.

### 4. Data Extraction -> Simulink to Python
* **Workflow**: Simulink Outport → MATLAB Workspace → `matlabengine` → Python
* **Mechanism**: Upon completion of the simulation, Simulink exports key time-series data—such as output voltage and inductor current—to the MATLAB workspace. Python then regains control via the engine API, retrieves these arrays (of type `double`) into its own memory, and converts them into NumPy/Pandas formats for further processing.

### 5. Assertion & Visualization -> Python
* **Workflow**: Raw data array → Core algorithmic computation → Pytest `assert` / Matplotlib
* **Mechanism**: A Python script processes the returned voltage waveforms and automatically calculates three key electrical parameters: **Overshoot**, **Settling Time**, and **Steady-state Error**.
  * The calculated results are compared against predefined thresholds using `assert` statements to determine whether a test case passes or fails.
  * Matplotlib is triggered to plot the step response curve for the current operating condition, with the resulting plot integrated into the test report (`pytest-html`).
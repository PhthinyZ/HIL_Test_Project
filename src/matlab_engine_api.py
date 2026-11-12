"""
import matlab.engine

eng = matlab.engine.start_matlab()

# 传入 0-0.1s 的仿真时间，以及阶跃的电压和负载参数
result = eng.run_buck_sim(0.1, 
                          matlab.double([0, 0.03, 0.03, 0.05, 0.05, 0.1]), 
                          matlab.double([16, 16, 20, 20, 16, 16]),
                          matlab.double([0, 0.02, 0.02, 0.1]),
                          matlab.double([1, 1, 0, 0]))
"""

import matlab.engine
import numpy as np
import time

class BuckSimEngine:
    """
    def __init__(self):
        
        #初始化并启动 MATLAB 引擎。
        #这一步通常需要十几秒，建议在网络服务端启动时或 Pytest 的 fixture 里全局执行一次。
        
        print("[System] 正在启动 MATLAB 引擎，请稍候...")
        start_time = time.time()
        self.eng = matlab.engine.start_matlab()
        print(f"[System] MATLAB 引擎启动成功! 耗时: {time.time() - start_time:.2f}s")
        
        # 可选：如果你的 python 执行路径不在项目根目录，可以强制让 MATLAB cd 过去
        # import os
        # root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        # self.eng.cd(root_dir, nargout=0)
    """
    def __init__(self):
        """
        #初始化并启动 MATLAB 引擎。
        #这一步通常需要十几秒，建议在网络服务端启动时或 Pytest 的 fixture 里全局执行一次。
        """
        print("[System] 正在启动 MATLAB 引擎，请稍候...")
        start_time = time.time()
        self.eng = matlab.engine.start_matlab()
        print(f"[System] MATLAB 引擎启动成功! 耗时: {time.time() - start_time:.2f}s")
        
        import os
        # 1. 动态获取项目的根目录 (当前文件 src 的上一级)
        # 即自动定位到 D:\HIL_Test_Project
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # 2. 强制让 MATLAB 将项目根目录及其所有子文件夹 (models, src, data等) 加入搜索路径
        # genpath 会自动遍历所有子文件夹，addpath 会将它们加入 MATLAB 环境变量
        self.eng.addpath(self.eng.genpath(root_dir), nargout=0)
        
        # 3. 强制 MATLAB 将工作空间切换到根目录
        # 这样 run_buck_sim.m 里的 readfis('data\fuzzy_rules.fis') 相对路径才能精确匹配
        self.eng.cd(root_dir, nargout=0)
        
        print(f"[System] 已将工作目录和搜索路径绑定至: {root_dir}")

    def run_simulation(self, T_sim, vin_time, vin_value, load_time, load_value):
        """
        调用 MATLAB 端的 run_buck_sim.m 进行仿真
        """
        print(f"[Engine] 收到仿真任务，正在下发参数 (时长: {T_sim}s)...")
        print("[Engine] 【仿真运行中，请稍候】")
        
        # 1. 类型转换：将 Python 的 list 转换为 matlab.double，这是引擎通信的强制要求
        vin_time_mat = matlab.double(vin_time)
        vin_value_mat = matlab.double(vin_value)
        load_time_mat = matlab.double(load_time)
        load_value_mat = matlab.double(load_value)
        
        # 2. 调用 MATLAB 函数
        # nargout=3 告诉 MATLAB 引擎：我们期待收到 3 个返回值 (t, v, i)
        t_out, vout, i_ind = self.eng.run_buck_sim(
            float(T_sim), 
            vin_time_mat, 
            vin_value_mat, 
            load_time_mat, 
            load_value_mat,
            nargout=3
        )
        
        # 3. 数据清洗：将 MATLAB 返回的多维 list 转回平铺的 numpy 数组，方便 Python 后续处理
        result = {
            "time": np.array(t_out).flatten(),
            "vout": np.array(vout).flatten(),
            "i_ind": np.array(i_ind).flatten()
        }
        
        #print("[Engine] 仿真完成，成功获取数据包！")
        return result

    def close(self):
        """关闭引擎，释放内存"""
        print("[System] 正在关闭 MATLAB 引擎...")
        self.eng.quit()
        print("[System] 引擎已关闭。")

# ==========================================
# 本地测试模块 (直接运行此脚本时触发)
# ==========================================
if __name__ == '__main__':
    # 实例化引擎类
    engine = BuckSimEngine()
    
    try:
        # 构造和你在 MATLAB 里一样的测试用例
        T_sim = 0.1
        vin_time = [0.0, 0.03, 0.03, 0.05, 0.05, 0.1]
        vin_value = [16.0, 16.0, 20.0, 20.0, 16.0, 16.0]
        load_time = [0.0, 0.02, 0.02, 0.1]
        load_value = [1.0, 1.0, 0.0, 0.0]
        
        # 跑仿真
        result = engine.run_simulation(T_sim, vin_time, vin_value, load_time, load_value)
        
        # 简单校验数据
        time_array = result['time']
        vout_array = result['vout']
        
        print("\n--- 仿真结果摘要 ---")
        #print(f"总计获取了 {len(time_array)} 个数据点。")
        print(f"最大输出电压: {np.max(vout_array):.2f} V")
        print(f"稳态最终电压: {vout_array[-1]:.2f} V")
        print("--------------------\n")
        
        # 如果你想在 Python 里画图，取消下面几行的注释并确保装了 matplotlib
        """
        import matplotlib.pyplot as plt
        plt.plot(result['time'], result['vout'])
        plt.title('Buck Converter Output Voltage (Python Plot)')
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (V)')
        plt.grid(True)
        plt.show()
        """
        
    finally:
        # 确保无论是否报错，引擎都会被正常关闭
        engine.close()
# Description: iPhone电量实时图表绘制模块（基于Qt）
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com

"""
电量实时图表绘制模块
使用Qt和pyqtgraph提供实时电量监控图表功能
"""

from datetime import datetime, timedelta
import threading
import time

# 尝试导入Qt和pyqtgraph（优先使用PySide2，开源版本）
try:
    from PySide2.QtCore import QDateTime
except:
    try:
        from PySide6.QtCore import QDateTime
    except:
        try:
            from PyQt5.QtCore import QDateTime
        except:
            QDateTime = None

# 尝试导入Qt和pyqtgraph（优先使用PySide2，开源版本）
try:
    # 优先使用PySide2（Qt for Python，LGPL开源许可证）
    from PySide2.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
    from PySide2.QtCore import QTimer, Qt
    from PySide2.QtGui import QFont
    import pyqtgraph as pg
    HAS_QT = True
    QT_BACKEND = 'PySide2'
except ImportError:
    try:
        # 备选：PySide6（Qt6版本）
        from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
        from PySide6.QtCore import QTimer, Qt
        from PySide6.QtGui import QFont
        import pyqtgraph as pg
        HAS_QT = True
        QT_BACKEND = 'PySide6'
    except ImportError:
        try:
            # 最后备选：PyQt5（如果PySide不可用）
            from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
            from PyQt5.QtCore import QTimer, Qt
            from PyQt5.QtGui import QFont
            import pyqtgraph as pg
            HAS_QT = True
            QT_BACKEND = 'PyQt5'
        except ImportError:
            HAS_QT = False
            QT_BACKEND = None


class CustomDateAxisItem(pg.AxisItem):
    """自定义时间轴，显示 [YYYY-MM-DD HH:MM:SS] 格式"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base_time = None  # 存储基准时间（第一个时间戳）
    
    def setBaseTime(self, base_time):
        """设置基准时间（第一个时间戳）"""
        self.base_time = base_time
    
    def tickStrings(self, values, scale, spacing):
        """自定义时间标签格式"""
        strings = []
        for v in values:
            try:
                # pyqtgraph传入的values是数据坐标系统的值
                # 如果设置了基准时间，说明v是相对时间（秒），需要加上基准时间
                if self.base_time is not None:
                    # v是相对时间（秒），加上基准时间得到绝对时间
                    absolute_time = self.base_time + timedelta(seconds=v)
                    time_str = absolute_time.strftime('[%Y-%m-%d %H:%M:%S]')
                else:
                    # 没有基准时间，假设v是Unix时间戳（秒）
                    if v > 1e10:  # 可能是毫秒时间戳
                        v = v / 1000.0
                    dt = datetime.fromtimestamp(v)
                    time_str = dt.strftime('[%Y-%m-%d %H:%M:%S]')
                strings.append(time_str)
            except Exception as e:
                # 如果转换失败，显示原始值（用于调试）
                strings.append(f'{v:.0f}')
        return strings


class BatteryPlotWindow(QMainWindow):
    """电量图表窗口"""
    
    def __init__(self, timestamps, battery_levels, charge_modes):
        super().__init__()
        self.timestamps = timestamps
        self.battery_levels = battery_levels
        self.charge_modes = charge_modes
        self.base_time = None  # 基准时间（第一个时间戳）
        
        self.setWindowTitle('iPhone电量实时监控')
        self.setGeometry(100, 100, 1200, 600)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 创建图表widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', '电量 (%)', color='black', size='12pt')
        self.plot_widget.setLabel('bottom', '时间', color='black', size='12pt')
        self.plot_widget.setTitle('iPhone电量实时监控', color='black', size='14pt')
        self.plot_widget.setBackground('white')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setYRange(0, 100, padding=0)
        
        # 设置X轴为自定义时间轴，显示 [YYYY-MM-DD HH:MM:SS] 格式
        self.date_axis = CustomDateAxisItem(orientation='bottom')
        self.date_axis.setLabel(text='时间', units='')
        self.plot_widget.setAxisItems({'bottom': self.date_axis})
        
        # 创建曲线
        self.curve_battery = self.plot_widget.plot([], [], pen=pg.mkPen(color='blue', width=2), name='电量')
        self.curve_fast_charge = self.plot_widget.plot([], [], pen=pg.mkPen(color='red', width=3, style=Qt.DashLine), name='全速充电')
        self.curve_slow_charge = self.plot_widget.plot([], [], pen=pg.mkPen(color='green', width=3, style=Qt.DashLine), name='保持连接')
        
        # 添加图例
        self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)
        
        # 创建定时器用于更新图表
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(1000)  # 每秒更新一次
        
        # 初始化时间范围
        self.max_display_seconds = 30 * 60  # 30分钟
        
    def update_plot(self):
        """更新图表数据"""
        if len(self.timestamps) == 0:
            return
        
        try:
            # 准备数据
            times = []
            battery_data = []
            fast_x, fast_y = [], []
            slow_x, slow_y = [], []
            
            # 使用相对时间（秒），相对于第一个时间戳
            # 这样更稳定，避免时间戳过大导致的问题
            base_time = self.timestamps[0] if len(self.timestamps) > 0 else None
            if base_time is not None and base_time != self.base_time:
                # 更新基准时间
                self.base_time = base_time
                # 设置基准时间到时间轴
                if hasattr(self.date_axis, 'setBaseTime'):
                    self.date_axis.setBaseTime(base_time)
            
            for i, ts in enumerate(self.timestamps):
                if i >= len(self.battery_levels):
                    break
                # 使用相对时间（秒），相对于第一个时间戳
                if base_time is not None:
                    time_diff = (ts - base_time).total_seconds()
                else:
                    time_diff = 0
                times.append(time_diff)
                battery_data.append(self.battery_levels[i])
                
                # 根据充电模式分类
                mode = self.charge_modes[i] if i < len(self.charge_modes) else 'none'
                if mode == 'fast':
                    fast_x.append(time_diff)
                    fast_y.append(self.battery_levels[i])
                elif mode == 'slow':
                    slow_x.append(time_diff)
                    slow_y.append(self.battery_levels[i])
            
            # 更新曲线数据
            if len(times) > 0:
                self.curve_battery.setData(times, battery_data)
                self.curve_fast_charge.setData(fast_x, fast_y)
                self.curve_slow_charge.setData(slow_x, slow_y)
                
                # 自动调整x轴范围（显示最近30分钟的数据）
                if len(times) > 1:
                    current_time = times[-1]
                    time_range_seconds = current_time - times[0]
                    if time_range_seconds > self.max_display_seconds:
                        # 显示最近30分钟
                        self.plot_widget.setXRange(current_time - self.max_display_seconds, current_time, padding=0)
                    else:
                        # 显示全部数据
                        self.plot_widget.setXRange(times[0], current_time, padding=0)
                
                # 自动调整y轴范围（确保电量在0-100之间可见）
                if len(battery_data) > 0:
                    min_battery = max(0, min(battery_data) - 5)
                    max_battery = min(100, max(battery_data) + 5)
                    self.plot_widget.setYRange(min_battery, max_battery, padding=0)
        except Exception as e:
            # 忽略更新错误，避免影响主程序
            pass


class BatteryPlotter:
    """电量实时图表绘制类"""
    
    def __init__(self):
        """初始化图表绘制器"""
        self.app = None
        self.window = None
        self.timestamps = None
        self.battery_levels = None
        self.charge_modes = None
        self.event_thread = None
        self._running = True
        
    def _run_event_loop(self):
        """在单独线程中运行Qt事件循环（处理非关键事件）"""
        if self.app:
            # 运行事件循环，但允许定期检查是否应该退出
            while self._running:
                try:
                    # 处理所有待处理的事件，包括用户输入
                    self.app.processEvents()
                    time.sleep(0.01)  # 短暂休眠，避免CPU占用过高
                except:
                    break
    
    def setup_plot(self, timestamps, battery_levels, charge_modes):
        """
        设置图表
        
        Args:
            timestamps: 时间戳数据（deque）
            battery_levels: 电量数据（deque）
            charge_modes: 充电模式数据（deque）
        """
        if not HAS_QT:
            print("提示: 安装PySide2和pyqtgraph可启用实时图表功能:")
            print("  pip install PySide2 pyqtgraph")
            print("  或者使用: pip install PySide6 pyqtgraph")
            return False
        
        if QT_BACKEND:
            print(f"使用Qt后端: {QT_BACKEND}")
        
        self.timestamps = timestamps
        self.battery_levels = battery_levels
        self.charge_modes = charge_modes
        
        # 检查是否已有QApplication实例
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        
        # 创建窗口
        self.window = BatteryPlotWindow(timestamps, battery_levels, charge_modes)
        self.window.show()
        
        # 处理初始事件，确保窗口显示
        self.app.processEvents()
        
        # 在后台线程中持续处理Qt事件，避免界面卡顿
        self._running = True
        self.event_thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.event_thread.start()
        
        print("✓ 实时图表已启动（基于Qt）")
        return True
    
    def update(self):
        """更新图表显示（处理Qt事件，确保界面响应）"""
        if not HAS_QT or self.app is None:
            return
        
        try:
            # 处理Qt事件，包括用户输入事件，避免界面卡顿
            # 使用ExcludeUserInputEvents可能不够，改为处理所有事件
            self.app.processEvents()
        except:
            pass
    
    def close(self, keep_open=False):
        """
        关闭图表
        
        Args:
            keep_open: 如果为True，保持窗口打开直到用户关闭
        """
        if not HAS_QT or self.window is None:
            return
        
        if keep_open:
            print("\n图表窗口将保持打开，关闭窗口退出...")
            # 保持窗口打开，等待用户关闭
            if self.app:
                try:
                    # 运行事件循环直到窗口关闭
                    while self.window.isVisible():
                        self.app.processEvents()
                        time.sleep(0.1)
                except:
                    pass
        else:
            try:
                self._running = False
                if self.event_thread and self.event_thread.is_alive():
                    # 等待事件线程结束（最多等待1秒）
                    self.event_thread.join(timeout=1.0)
                if self.window:
                    self.window.close()
            except:
                pass

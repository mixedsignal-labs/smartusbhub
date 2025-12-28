# iPhone功耗循环测试

这个文件夹包含iPhone功耗循环测试的相关代码。

## 文件说明

- `iphone_power_cycle_test.py` - 主测试程序，实现iPhone功耗循环测试逻辑
- `battery_plotter.py` - 电量实时图表绘制模块，提供图表显示功能

## 功能

- 通过蓝牙获取iPhone电量
- 根据电量自动切换快充/慢充模式
- 实时显示电量变化图表

## 使用方法

```bash
cd iphone_power_test
python iphone_power_cycle_test.py
```

## 依赖

- `smartusbhub` - SmartUSBHub库
- `PySide2` 或 `PySide6` - Qt for Python（开源版本，用于图表显示，可选）
- `pyqtgraph` - 高性能实时图表库（可选）
- `bleak` 或 `bluepy` - 蓝牙通信（可选，用于获取真实电量）

## 安装依赖

```bash
# 安装Qt图表相关依赖（推荐使用PySide2，开源LGPL许可证）
pip install PySide2 pyqtgraph

# 或者使用Qt6版本
pip install PySide6 pyqtgraph

# 安装蓝牙库（用于获取真实电量）
pip install bleak
```

## 关于Qt版本

- **推荐使用 PySide2**：Qt官方的Python绑定，使用LGPL开源许可证，适合商业项目
- PySide6：Qt6版本，功能更新但可能兼容性稍差
- PyQt5：备选方案，如果PySide不可用时使用


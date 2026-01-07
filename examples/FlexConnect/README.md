# FlexConnect 示例程序

FlexConnect 产品的演示程序和工具脚本，从快速入门到高级应用。

---

## 文件列表

### 快速开始示例

| 文件 | 类型 | 说明 |
|-----|------|------|
| `basic_usage.py` | 入门示例 | 基础使用入门，演示连接、查询、切换等基本操作 |
| `flexconnect_mode_switch_demo.py` | 交互演示 | 交互式模式切换演示，循环切换各种模式 |

### 诊断工具

| 文件 | 类型 | 说明 |
|-----|------|------|
| `diagnose_params.py` | 诊断工具 | 读取并显示所有相关参数，用于排查问题 |

---

## 详细说明

### basic_usage.py - 基础使用入门

**功能：** 演示 FlexConnect 产品的基本使用方法。

**运行方法：**
```bash
python examples/FlexConnect/basic_usage.py
```

**演示内容：**
1. 扫描并连接设备
2. 获取设备信息（型号、版本、序列号等）
3. 查询当前状态（模式、掉电恢复、按键状态、设备地址）
4. 设备地址设置和获取演示
5. 模式切换演示（PC 模式 ↔ U 盘模式）
6. 验证切换结果

**适用场景：**
- 快速入门和学习
- 验证设备连接
- 基本功能测试
- 学习 API 使用方法

**预期输出：**
```
======================================================
FlexConnect 基础使用示例
======================================================

[步骤1] 扫描并连接设备...
成功连接到设备

[步骤2] 获取设备信息...
设备信息:
  产品名称: SmartUSBSwitch FlexConnect
  产品类型: 0x14
  硬件版本: v1.0
  固件版本: v1.0.0
  
[步骤3] 获取当前状态...
  当前模式: PC 模式（ADB 调试）
  掉电恢复: 已禁用
  按键控制: 已启用
  设备地址: 0x0000
  
[步骤4] 设备地址演示...
  当前设备地址: 0x0000
  设置设备地址为 0x0001...
  设置成功
  验证成功: 当前设备地址为 0x0001
  恢复原始设备地址 0x0000...
  恢复成功
  验证成功: 设备地址已恢复为 0x0000
  
[步骤5] 模式切换演示...
  切换到 PC 模式...
  切换成功
  验证成功: 当前为 PC 模式
  
基础功能测试完成！
```

---

### flexconnect_mode_switch_demo.py - 交互式模式切换

**功能：** 交互式演示 FlexConnect 产品的模式切换功能。

**运行方法：**
```bash
python examples/FlexConnect/flexconnect_mode_switch_demo.py
```

**使用方法：**
1. 程序启动后会自动连接第一个可用的 FlexConnect 设备
2. 显示当前模式和故障状态
3. 按回车键循环切换模式：PC → UDISK1 → UDISK2 → PC → ...
4. 输入 `q` 退出程序

**现象效果：**
- 实时显示当前模式（PC/UDISK1/UDISK2）
- 显示故障状态（如果有）
- 每次切换后自动验证模式是否正确设置
- 支持优雅退出，退出时恢复设备状态

**适用场景：**
- 快速演示模式切换功能
- 验证设备响应
- 测试模式切换的稳定性
- 学习 FlexConnect API 使用

---

### diagnose_params.py - 参数诊断工具

**功能：** 读取并显示 FlexConnect 设备的所有相关参数，用于排查掉电恢复逻辑问题。

**运行方法：**
```bash
python examples/FlexConnect/diagnose_params.py
```

**输出信息：**
- 设备基本信息（端口、硬件版本、固件版本）
- 当前 FlexConnect 模式
- 上电默认模式
- 掉电恢复状态（启用/禁用）
- 通道电源状态
- 其他相关参数

**适用场景：**
- 排查掉电恢复逻辑问题
- 调试设备参数设置
- 验证参数持久化
- 检查设备配置状态

---

## 学习路径

推荐按以下顺序学习：

### 入门阶段
1. **basic_usage.py** - 了解基本连接和控制方法
2. **flexconnect_mode_switch_demo.py** - 练习交互式操作

### 进阶阶段
3. **diagnose_params.py** - 学会使用诊断工具
4. 参考完整测试套件（位于 `test/FlexConnect/`）

---

## 代码模板

### 最简单的连接和切换

```python
from smartusbhub import SmartUSBHub, FLEXCONNECT_MODE_PC, FLEXCONNECT_MODE_UDISK1

# 连接
hub = SmartUSBHub.scan_and_connect()

# 设置设备地址（多设备场景）
hub.set_device_address(0x0001)

# 切换到 PC 模式
hub.set_flexconnect_mode(FLEXCONNECT_MODE_PC)

# 切换到 U 盘模式
hub.set_flexconnect_mode(FLEXCONNECT_MODE_UDISK1)

# 断开
hub.disconnect()
```



**最后更新**: 2026-01-07  
**版本**: 1.0.0

© 2026 makerlabtools. All Rights Reserved.

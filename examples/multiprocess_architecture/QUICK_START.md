# 快速开始指南

## 前置条件

1. **安装依赖**
   ```bash
   pip install pyserial colorlog numpy
   ```

2. **连接设备**
   - 确保SmartUSBHub设备已通过USB连接到电脑
   - 确保串口驱动已正确安装

## 运行方式

### 方式1：使用库模块（推荐）✨

这是使用新集成的库模块的方式，更简洁：

```bash
cd examples/multiprocess_architecture
python usage_example.py
```

**特点：**
- 使用 `smartusbhub.smartusbhub_multiprocess` 模块
- 代码更简洁
- 推荐使用

### 方式2：使用原始示例代码

这是使用 `examples/multiprocess_architecture` 目录下的原始示例代码：

```bash
cd examples/multiprocess_architecture
python run_all.py
```

**特点：**
- 使用独立的示例代码文件
- 功能相同，但代码结构不同

## 运行效果

运行后你会看到：

```
============================================================
SmartUSBHub 多进程架构示例（使用可选模块）
============================================================

[Main] 启动SmartUSBHub服务进程...
[Server] 正在初始化SmartUSBHub...
[Server] SmartUSBHub已连接: COM3
[Server] 硬件版本: V1.3
[Server] 固件版本: V1.15
[Server] 服务进程已启动，等待请求...
[Main] 服务进程已启动

[Main] 启动业务进程...
[BusinessProcess-1] 业务进程启动，控制通道 1
[BusinessProcess-2] 业务进程启动，控制通道 2
[BusinessProcess-3] 业务进程启动，控制通道 3
[BusinessProcess-4] 业务进程启动，控制通道 4

[BusinessProcess-1] 迭代 1: 开启通道 1 电源
[BusinessProcess-1] ✓ 通道 1 电源已开启
[BusinessProcess-1] 通道 1 电源状态: 1
...
```

## 停止程序

按 `Ctrl+C` 可以优雅地停止所有进程。

## 常见问题

### 1. 找不到设备

**错误信息：**
```
[Server] 错误: 无法找到或连接SmartUSBHub设备
```

**解决方法：**
- 检查USB连接
- 检查串口驱动
- 检查是否有其他程序占用串口

### 2. 导入错误

**错误信息：**
```
ModuleNotFoundError: No module named 'smartusbhub'
```

**解决方法：**
```bash
# 确保在正确的目录
cd examples/multiprocess_architecture

# 或者安装库
pip install -e ..
```

### 3. 权限错误（Linux/Mac）

**错误信息：**
```
PermissionError: [Errno 13] Permission denied: '/dev/ttyUSB0'
```

**解决方法：**
```bash
# 添加用户到dialout组（Linux）
sudo usermod -a -G dialout $USER
# 然后重新登录
```

## 自定义业务逻辑

你可以修改 `usage_example.py` 中的 `business_process_example` 函数来实现自己的业务逻辑：

```python
def business_process_example(channel: int, request_queue: Queue, response_dict: dict):
    client = SmartUSBHubClient(request_queue, response_dict)
    
    # 在这里添加你的业务逻辑
    # 例如：读取电压、电流，控制数据线等
    client.set_channel_power(channel, state=1)
    voltage = client.get_channel_voltage(channel)
    current = client.get_channel_current(channel)
    # ...
```

## 下一步

- 查看 `README.md` 了解详细架构
- 查看 `TECHNICAL_EXPLANATION.md` 了解技术原理
- 查看 `INTEGRATION_GUIDE.md` 了解如何集成到你的项目








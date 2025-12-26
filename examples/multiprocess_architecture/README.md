# SmartUSBHub 多进程架构

## 概述

本目录包含了一个多进程架构的实现，用于解决多进程访问SmartUSBHub时ACK报错的问题。

### 架构设计

- **1个服务进程** (`smartusbhub_server.py`): 负责管理SmartUSBHub实例，接收来自业务进程的请求并执行USB操作
- **4个业务进程** (`business_process_1.py` ~ `business_process_4.py`): 每个进程控制一个USB端口，执行自己的测试业务
- **客户端代理** (`smartusbhub_client.py`): 提供与SmartUSBHub相同的API接口，通过进程间通信调用服务进程

### 工作原理

1. 服务进程初始化并连接SmartUSBHub设备
2. 业务进程通过客户端代理发送请求到服务进程
3. 服务进程执行USB操作并返回结果
4. 所有USB操作都在服务进程中串行执行，避免了多进程竞争导致的ACK错误

## 文件说明

- `smartusbhub_server.py`: SmartUSBHub服务进程，负责所有USB操作
- `smartusbhub_client.py`: 客户端代理，提供与SmartUSBHub相同的API接口
- `business_process_1.py`: 业务进程1，控制USB端口1
- `business_process_2.py`: 业务进程2，控制USB端口2
- `business_process_3.py`: 业务进程3，控制USB端口3
- `business_process_4.py`: 业务进程4，控制USB端口4
- `business_process_template.py`: 业务进程模板，可用于创建新的业务进程
- `run_all.py`: 主启动脚本，启动所有进程
- `stress_test.py`: 压力测试程序，覆盖各种并发冲突场景

## 使用方法

### 快速启动

运行主启动脚本：

```bash
python run_all.py
```

这将启动：
1. 1个SmartUSBHub服务进程
2. 4个业务进程（每个控制一个USB端口）

### 压力测试

运行压力测试程序来验证多进程架构的稳定性和正确性：

```bash
# 使用默认配置运行混合场景测试
python stress_test.py

# 指定工作进程数和测试时长
python stress_test.py --workers 20 --duration 120

# 测试同一通道的并发冲突
python stress_test.py --test-type same_channel_conflict --workers 15 --duration 60
```

详细说明请参考 [STRESS_TEST_GUIDE.md](./STRESS_TEST_GUIDE.md)

### 自定义业务进程

1. 复制 `business_process_template.py` 创建新的业务进程
2. 修改业务逻辑部分（在 `main` 函数中）
3. 在 `run_all.py` 中添加新的业务进程启动代码

### 客户端API

客户端代理提供以下API（与SmartUSBHub相同）：

- `set_channel_power(*channels, state)`: 设置通道电源状态
- `get_channel_power_status(*channels)`: 获取通道电源状态
- `set_channel_usb2_dataline(*channels, state)`: 设置USB2数据线状态
- `get_channel_usb2_dataline_status(*channels)`: 获取USB2数据线状态
- `set_channel_usb3_dataline(*channels, state)`: 设置USB3数据线状态
- `get_channel_usb3_dataline_status(*channels)`: 获取USB3数据线状态
- `get_channel_voltage(channel)`: 获取通道电压
- `get_channel_current(channel)`: 获取通道电流
- `set_channel_low_current(*channels, state)`: 设置通道低电流模式
- `get_channel_low_current_status(*channels)`: 获取通道低电流模式状态

## 进程间通信

使用Python的 `multiprocessing.Queue` 和 `multiprocessing.Manager` 实现进程间通信：

- **请求队列**: 业务进程通过 `request_queue` 发送请求到服务进程
- **响应字典**: 服务进程通过 `response_dict` 返回结果给业务进程

## 注意事项

1. 确保只有一个服务进程在运行
2. 业务进程应该只通过客户端代理访问USB功能，不要直接创建SmartUSBHub实例
3. 所有USB操作都在服务进程中串行执行，确保线程安全
4. 使用 Ctrl+C 可以优雅地关闭所有进程

## 故障排除

### 服务进程无法启动

- 检查SmartUSBHub设备是否已连接
- 检查串口是否被其他程序占用
- 查看服务进程的日志输出

### 业务进程无法通信

- 确保服务进程已成功启动
- 检查请求队列和响应字典是否正确共享
- 查看客户端和服务进程的日志输出

### ACK错误仍然出现

- 确保所有业务进程都使用客户端代理，而不是直接创建SmartUSBHub实例
- 检查是否有其他程序直接访问SmartUSBHub设备

## 相关文档

- [技术讲解](./TECHNICAL_EXPLANATION.md): 详细的技术原理和实现说明
- [集成指南](./INTEGRATION_GUIDE.md): 如何将多进程架构集成到你的项目中
- [压力测试指南](./STRESS_TEST_GUIDE.md): 压力测试的详细使用说明


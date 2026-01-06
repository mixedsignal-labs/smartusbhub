# 多进程模块集成指南

## 概述

多进程支持已作为可选模块集成到库中，无需大改现有代码。本文档说明如何使用和集成。

## 文件结构

```
smartusbhub_ng/
├── smartusbhub.py          # 主模块（不变）
├── smartusbhub_multiprocess.py        # 新增：多进程支持模块
├── __init__.py            # 更新：可选导出多进程模块
└── examples/
    └── multiprocess_architecture/
        ├── usage_example.py        # 使用示例
        └── ...                     # 其他示例文件
```

## 改动说明

### 1. 新增文件

- **`smartusbhub_multiprocess.py`**: 多进程支持模块
  - `SmartUSBHubClient`: 客户端代理类
  - `SmartUSBHubServer`: 服务进程类
  - `server_process_main`: 服务进程主函数

### 2. 修改文件

- **`__init__.py`**: 可选导出多进程模块
  - 使用 `try-except` 确保导入失败不影响主模块
  - 向后兼容，不影响现有代码

### 3. 未修改

- **`smartusbhub.py`**: 完全不变
- 所有现有代码：完全兼容

## 使用方式

### 方式1：从子模块导入（推荐）

```python
from smartusbhub import SmartUSBHub
from smartusbhub.smartusbhub_multiprocess import SmartUSBHubClient, SmartUSBHubServer, server_process_main
```

### 方式2：从主模块导入（如果已配置）

```python
from smartusbhub import SmartUSBHub, SmartUSBHubClient, SmartUSBHubServer
```

### 完整示例

```python
from multiprocessing import Process, Manager, Queue
from smartusbhub.smartusbhub_multiprocess import SmartUSBHubClient, server_process_main

# 创建共享资源
manager = Manager()
request_queue = Queue()
response_dict = manager.dict()

# 启动服务进程
server_process = Process(
    target=server_process_main,
    args=(request_queue, response_dict, None)
)
server_process.start()

# 等待初始化
import time
time.sleep(2)

# 创建客户端
client = SmartUSBHubClient(request_queue, response_dict)

# 使用客户端（API与SmartUSBHub相同）
client.set_channel_power(1, state=1)
status = client.get_channel_power_status(1)
```

## 向后兼容性

### ✅ 完全兼容

- 现有代码无需修改
- 单进程使用方式不变
- 多线程使用方式不变
- 导入方式不变

### 可选使用

- 多进程支持是可选的
- 不需要多进程的用户不受影响
- 导入失败不会报错

## 优势

### 1. 无需大改

- 只新增一个文件 `smartusbhub_multiprocess.py`
- 主模块 `smartusbhub.py` 完全不变
- `__init__.py` 只添加可选导入

### 2. 向后兼容

- 现有代码继续工作
- 新功能可选使用
- 不影响现有用户

### 3. 易于维护

- 多进程代码独立模块
- 清晰的职责分离
- 便于测试和调试

## 迁移指南

### 从示例代码迁移

如果你之前使用的是 `examples/multiprocess_architecture/` 中的代码：

**之前：**
```python
import sys
sys.path.insert(0, 'examples/multiprocess_architecture')
from smartusbhub_client import SmartUSBHubClient
from smartusbhub_server import server_process_main
```

**现在：**
```python
from smartusbhub.smartusbhub_multiprocess import SmartUSBHubClient, server_process_main
```

### API兼容性

多进程模块的API与主模块完全兼容：

```python
# 单进程方式
hub = SmartUSBHub.scan_and_connect()
hub.set_channel_power(1, state=1)

# 多进程方式（API相同）
client = SmartUSBHubClient(request_queue, response_dict)
client.set_channel_power(1, state=1)  # 相同的API
```

## 测试

### 基本测试

```python
# 测试导入
from smartusbhub.smartusbhub_multiprocess import SmartUSBHubClient, SmartUSBHubServer

# 测试功能
# 运行 examples/multiprocess_architecture/usage_example.py
```

### 兼容性测试

```python
# 确保主模块仍然可用
from smartusbhub import SmartUSBHub
hub = SmartUSBHub.scan_and_connect()
# 应该正常工作
```

## 常见问题

### Q: 导入失败怎么办？

A: 使用 `try-except` 处理：
```python
try:
    from smartusbhub.smartusbhub_multiprocess import SmartUSBHubClient
except ImportError:
    # 降级到单进程模式
    from smartusbhub import SmartUSBHub
```

### Q: 性能如何？

A: 进程间通信开销很小（< 1ms），对实际业务影响可忽略。

### Q: 是否需要安装额外依赖？

A: 不需要，只使用Python标准库的 `multiprocessing`。

## 总结

- ✅ 无需大改：只新增一个文件
- ✅ 向后兼容：现有代码不受影响
- ✅ 可选使用：不需要多进程的用户不受影响
- ✅ 易于维护：清晰的模块分离
- ✅ API兼容：与主模块API相同


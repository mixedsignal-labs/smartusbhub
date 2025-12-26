"""
SmartUSBHub 压力测试程序
覆盖各种并发冲突场景，验证多进程架构的稳定性和正确性
"""
import sys
import os
import time
import signal
import random
import threading
from multiprocessing import Process, Manager, Queue
from collections import defaultdict
from datetime import datetime

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, os.path.dirname(__file__))
from smartusbhub_server import server_process_main
from smartusbhub_client import SmartUSBHubClient


# 定义可序列化的工厂函数（用于 defaultdict）
def _default_operation_stats():
    """操作统计的默认值工厂函数"""
    return {'success': 0, 'fail': 0}


def _default_channel_stats():
    """通道统计的默认值工厂函数"""
    return {'operations': 0, 'conflicts': 0}


class StressTestStats:
    """压力测试统计信息（使用 Manager 创建的共享对象）"""
    
    def __init__(self, manager=None):
        """
        初始化统计对象
        
        Args:
            manager: multiprocessing.Manager 实例，如果为 None 则使用普通变量（仅主进程使用）
        """
        if manager is None:
            # 主进程模式：使用普通变量和线程锁
            self.total_requests = 0
            self.successful_requests = 0
            self.failed_requests = 0
            self.timeout_errors = 0
            self.runtime_errors = 0
            self.conflict_errors = 0
            self.operation_stats = defaultdict(_default_operation_stats)
            self.channel_stats = defaultdict(_default_channel_stats)
            self.lock = threading.Lock()
            self._use_manager = False
        else:
            # 多进程模式：使用 Manager 创建的共享对象
            self.manager = manager  # 保存 manager 引用
            self.total_requests = manager.Value('i', 0)
            self.successful_requests = manager.Value('i', 0)
            self.failed_requests = manager.Value('i', 0)
            self.timeout_errors = manager.Value('i', 0)
            self.runtime_errors = manager.Value('i', 0)
            self.conflict_errors = manager.Value('i', 0)
            self.operation_stats = manager.dict()
            self.channel_stats = manager.dict()
            self.lock = manager.Lock()
            self._use_manager = True
        
    def _get_operation_stats(self, operation):
        """获取操作统计，如果不存在则创建"""
        if operation not in self.operation_stats:
            if self._use_manager:
                self.operation_stats[operation] = self.manager.dict({'success': 0, 'fail': 0})
            else:
                self.operation_stats[operation] = {'success': 0, 'fail': 0}
        return self.operation_stats[operation]
    
    def _get_channel_stats(self, channel):
        """获取通道统计，如果不存在则创建"""
        if channel not in self.channel_stats:
            if self._use_manager:
                self.channel_stats[channel] = self.manager.dict({'operations': 0, 'conflicts': 0})
            else:
                self.channel_stats[channel] = {'operations': 0, 'conflicts': 0}
        return self.channel_stats[channel]
        
    def record_success(self, operation, channel=None):
        with self.lock:
            if self._use_manager:
                self.total_requests.value += 1
                self.successful_requests.value += 1
            else:
                self.total_requests += 1
                self.successful_requests += 1
                
            op_stats = self._get_operation_stats(operation)
            if self._use_manager:
                if 'success' not in op_stats:
                    op_stats['success'] = 0
                op_stats['success'] += 1
            else:
                op_stats['success'] += 1
                
            if channel:
                ch_stats = self._get_channel_stats(channel)
                if self._use_manager:
                    if 'operations' not in ch_stats:
                        ch_stats['operations'] = 0
                    ch_stats['operations'] += 1
                else:
                    ch_stats['operations'] += 1
                
    def record_failure(self, operation, error_type, channel=None, error_msg=""):
        with self.lock:
            if self._use_manager:
                self.total_requests.value += 1
                self.failed_requests.value += 1
            else:
                self.total_requests += 1
                self.failed_requests += 1
                
            op_stats = self._get_operation_stats(operation)
            if self._use_manager:
                if 'fail' not in op_stats:
                    op_stats['fail'] = 0
                op_stats['fail'] += 1
            else:
                op_stats['fail'] += 1
            
            if 'timeout' in error_msg.lower() or 'Timeout' in error_msg:
                if self._use_manager:
                    self.timeout_errors.value += 1
                else:
                    self.timeout_errors += 1
            elif 'RuntimeError' in error_msg or 'Runtime' in error_msg:
                if self._use_manager:
                    self.runtime_errors.value += 1
                else:
                    self.runtime_errors += 1
            else:
                if self._use_manager:
                    self.conflict_errors.value += 1
                else:
                    self.conflict_errors += 1
                
            if channel:
                ch_stats = self._get_channel_stats(channel)
                if self._use_manager:
                    if 'operations' not in ch_stats:
                        ch_stats['operations'] = 0
                    if 'conflicts' not in ch_stats:
                        ch_stats['conflicts'] = 0
                    ch_stats['operations'] += 1
                    ch_stats['conflicts'] += 1
                else:
                    ch_stats['operations'] += 1
                    ch_stats['conflicts'] += 1
                
    def get_summary(self):
        with self.lock:
            if self._use_manager:
                total = self.total_requests.value
                success = self.successful_requests.value
                fail = self.failed_requests.value
                timeout = self.timeout_errors.value
                runtime = self.runtime_errors.value
                conflict = self.conflict_errors.value
                
                # 转换 Manager 字典为普通字典
                op_stats = {}
                for op, stats in self.operation_stats.items():
                    if hasattr(stats, 'get'):
                        # Manager 字典
                        op_stats[op] = {
                            'success': stats.get('success', 0),
                            'fail': stats.get('fail', 0)
                        }
                    else:
                        # 普通字典
                        op_stats[op] = dict(stats) if isinstance(stats, dict) else {'success': 0, 'fail': 0}
                
                ch_stats = {}
                for ch, stats in self.channel_stats.items():
                    if hasattr(stats, 'get'):
                        # Manager 字典
                        ch_stats[ch] = {
                            'operations': stats.get('operations', 0),
                            'conflicts': stats.get('conflicts', 0)
                        }
                    else:
                        # 普通字典
                        ch_stats[ch] = dict(stats) if isinstance(stats, dict) else {'operations': 0, 'conflicts': 0}
            else:
                total = self.total_requests
                success = self.successful_requests
                fail = self.failed_requests
                timeout = self.timeout_errors
                runtime = self.runtime_errors
                conflict = self.conflict_errors
                op_stats = dict(self.operation_stats)
                ch_stats = dict(self.channel_stats)
                
            success_rate = (success / total * 100) if total > 0 else 0
            return {
                'total_requests': total,
                'successful_requests': success,
                'failed_requests': fail,
                'success_rate': success_rate,
                'timeout_errors': timeout,
                'runtime_errors': runtime,
                'conflict_errors': conflict,
                'operation_stats': op_stats,
                'channel_stats': ch_stats
            }


class StressTestWorker:
    """压力测试工作进程"""
    
    def __init__(self, worker_id, request_queue, response_dict, stats, test_config):
        self.worker_id = worker_id
        self.request_queue = request_queue
        self.response_dict = response_dict
        self.stats = stats
        self.config = test_config
        self.client = SmartUSBHubClient(request_queue, response_dict, timeout=test_config.get('timeout', 5.0))
        self.running = True
        
    def run(self):
        """运行压力测试"""
        test_type = self.config.get('test_type', 'mixed')
        
        if test_type == 'same_channel_conflict':
            self._test_same_channel_conflict()
        elif test_type == 'different_channels':
            self._test_different_channels()
        elif test_type == 'rapid_requests':
            self._test_rapid_requests()
        elif test_type == 'read_write_mix':
            self._test_read_write_mix()
        elif test_type == 'channel_switching':
            self._test_channel_switching()
        elif test_type == 'mixed':
            self._test_mixed()
        else:
            print(f"[Worker-{self.worker_id}] 未知的测试类型: {test_type}")
            
    def _test_same_channel_conflict(self):
        """测试场景1: 同一通道的并发冲突"""
        channel = self.config.get('channel', 1)
        iterations = self.config.get('iterations', 100)
        
        print(f"[Worker-{self.worker_id}] 开始测试: 同一通道并发冲突 (通道{channel}, {iterations}次迭代)")
        
        for i in range(iterations):
            if not self.running:
                break
                
            # 随机选择操作
            operation = random.choice(['power', 'dataline', 'voltage', 'current'])
            
            try:
                if operation == 'power':
                    state = random.choice([0, 1])
                    result = self.client.set_channel_power(channel, state=state)
                    if result:
                        self.stats.record_success('set_channel_power', channel)
                    else:
                        self.stats.record_failure('set_channel_power', 'failure', channel, "操作返回False")
                        
                elif operation == 'dataline':
                    state = random.choice([0, 1])
                    result = self.client.set_channel_usb2_dataline(channel, state=state)
                    if result:
                        self.stats.record_success('set_channel_usb2_dataline', channel)
                    else:
                        self.stats.record_failure('set_channel_usb2_dataline', 'failure', channel, "操作返回False")
                        
                elif operation == 'voltage':
                    result = self.client.get_channel_voltage(channel)
                    if result is not None:
                        self.stats.record_success('get_channel_voltage', channel)
                    else:
                        self.stats.record_failure('get_channel_voltage', 'timeout', channel, "返回None")
                        
                elif operation == 'current':
                    result = self.client.get_channel_current(channel)
                    if result is not None:
                        self.stats.record_success('get_channel_current', channel)
                    else:
                        self.stats.record_failure('get_channel_current', 'timeout', channel, "返回None")
                        
            except TimeoutError as e:
                self.stats.record_failure(operation, 'timeout', channel, str(e))
            except RuntimeError as e:
                self.stats.record_failure(operation, 'runtime', channel, str(e))
            except Exception as e:
                self.stats.record_failure(operation, 'unknown', channel, str(e))
                
            # 随机延迟，模拟真实场景
            time.sleep(random.uniform(0.01, 0.1))
            
    def _test_different_channels(self):
        """测试场景2: 不同通道的并发操作"""
        iterations = self.config.get('iterations', 100)
        channels = self.config.get('channels', [1, 2, 3, 4])
        
        print(f"[Worker-{self.worker_id}] 开始测试: 不同通道并发操作 (通道{channels}, {iterations}次迭代)")
        
        for i in range(iterations):
            if not self.running:
                break
                
            channel = random.choice(channels)
            state = random.choice([0, 1])
            
            try:
                result = self.client.set_channel_power(channel, state=state)
                if result:
                    self.stats.record_success('set_channel_power', channel)
                else:
                    self.stats.record_failure('set_channel_power', 'failure', channel, "操作返回False")
                    
                time.sleep(random.uniform(0.01, 0.05))
                
            except Exception as e:
                self.stats.record_failure('set_channel_power', 'error', channel, str(e))
                
    def _test_rapid_requests(self):
        """测试场景3: 快速连续请求（测试队列积压和超时）"""
        iterations = self.config.get('iterations', 200)
        channel = self.config.get('channel', 1)
        
        print(f"[Worker-{self.worker_id}] 开始测试: 快速连续请求 (通道{channel}, {iterations}次请求)")
        
        for i in range(iterations):
            if not self.running:
                break
                
            try:
                # 快速连续发送请求，不等待
                result = self.client.get_channel_voltage(channel)
                if result is not None:
                    self.stats.record_success('get_channel_voltage', channel)
                else:
                    self.stats.record_failure('get_channel_voltage', 'timeout', channel, "返回None")
                    
            except TimeoutError:
                self.stats.record_failure('get_channel_voltage', 'timeout', channel, "请求超时")
            except Exception as e:
                self.stats.record_failure('get_channel_voltage', 'error', channel, str(e))
                
            # 最小延迟，测试系统极限
            time.sleep(0.001)
            
    def _test_read_write_mix(self):
        """测试场景4: 读写混合操作"""
        iterations = self.config.get('iterations', 100)
        channel = self.config.get('channel', 1)
        
        print(f"[Worker-{self.worker_id}] 开始测试: 读写混合操作 (通道{channel}, {iterations}次迭代)")
        
        for i in range(iterations):
            if not self.running:
                break
                
            # 随机选择读写操作
            if random.random() < 0.5:  # 50% 写操作
                try:
                    state = random.choice([0, 1])
                    result = self.client.set_channel_power(channel, state=state)
                    if result:
                        self.stats.record_success('set_channel_power', channel)
                    else:
                        self.stats.record_failure('set_channel_power', 'failure', channel, "操作返回False")
                except Exception as e:
                    self.stats.record_failure('set_channel_power', 'error', channel, str(e))
            else:  # 50% 读操作
                try:
                    if random.random() < 0.5:
                        result = self.client.get_channel_voltage(channel)
                        op_name = 'get_channel_voltage'
                    else:
                        result = self.client.get_channel_current(channel)
                        op_name = 'get_channel_current'
                        
                    if result is not None:
                        self.stats.record_success(op_name, channel)
                    else:
                        self.stats.record_failure(op_name, 'timeout', channel, "返回None")
                except Exception as e:
                    op_name = 'get_channel_voltage' if random.random() < 0.5 else 'get_channel_current'
                    self.stats.record_failure(op_name, 'error', channel, str(e))
                    
            time.sleep(random.uniform(0.01, 0.05))
            
    def _test_channel_switching(self):
        """测试场景5: 通道快速切换"""
        iterations = self.config.get('iterations', 100)
        channels = self.config.get('channels', [1, 2, 3, 4])
        
        print(f"[Worker-{self.worker_id}] 开始测试: 通道快速切换 (通道{channels}, {iterations}次迭代)")
        
        for i in range(iterations):
            if not self.running:
                break
                
            # 快速切换通道
            channel = random.choice(channels)
            state = random.choice([0, 1])
            
            try:
                result = self.client.set_channel_power(channel, state=state)
                if result:
                    self.stats.record_success('set_channel_power', channel)
                else:
                    self.stats.record_failure('set_channel_power', 'failure', channel, "操作返回False")
                    
                # 立即读取状态
                status = self.client.get_channel_power_status(channel)
                if status is not None:
                    self.stats.record_success('get_channel_power_status', channel)
                else:
                    self.stats.record_failure('get_channel_power_status', 'timeout', channel, "返回None")
                    
            except Exception as e:
                self.stats.record_failure('set_channel_power', 'error', channel, str(e))
                
            time.sleep(0.01)
            
    def _test_mixed(self):
        """测试场景6: 混合所有场景"""
        iterations = self.config.get('iterations', 200)
        
        print(f"[Worker-{self.worker_id}] 开始测试: 混合场景 ({iterations}次迭代)")
        
        for i in range(iterations):
            if not self.running:
                break
                
            # 随机选择测试场景
            scenario = random.choice(['same_channel', 'different_channels', 'rapid', 'read_write'])
            channel = random.choice([1, 2, 3, 4])
            
            try:
                if scenario == 'same_channel':
                    state = random.choice([0, 1])
                    result = self.client.set_channel_power(channel, state=state)
                    if result:
                        self.stats.record_success('set_channel_power', channel)
                    else:
                        self.stats.record_failure('set_channel_power', 'failure', channel, "操作返回False")
                        
                elif scenario == 'different_channels':
                    # 同时操作多个通道
                    channels = random.sample([1, 2, 3, 4], random.randint(1, 3))
                    state = random.choice([0, 1])
                    result = self.client.set_channel_power(*channels, state=state)
                    if result:
                        for ch in channels:
                            self.stats.record_success('set_channel_power', ch)
                    else:
                        for ch in channels:
                            self.stats.record_failure('set_channel_power', 'failure', ch, "操作返回False")
                            
                elif scenario == 'rapid':
                    result = self.client.get_channel_voltage(channel)
                    if result is not None:
                        self.stats.record_success('get_channel_voltage', channel)
                    else:
                        self.stats.record_failure('get_channel_voltage', 'timeout', channel, "返回None")
                        
                elif scenario == 'read_write':
                    if random.random() < 0.5:
                        state = random.choice([0, 1])
                        result = self.client.set_channel_power(channel, state=state)
                        if result:
                            self.stats.record_success('set_channel_power', channel)
                        else:
                            self.stats.record_failure('set_channel_power', 'failure', channel, "操作返回False")
                    else:
                        result = self.client.get_channel_voltage(channel)
                        if result is not None:
                            self.stats.record_success('get_channel_voltage', channel)
                        else:
                            self.stats.record_failure('get_channel_voltage', 'timeout', channel, "返回None")
                            
            except TimeoutError as e:
                self.stats.record_failure('operation', 'timeout', channel, str(e))
            except RuntimeError as e:
                self.stats.record_failure('operation', 'runtime', channel, str(e))
            except Exception as e:
                self.stats.record_failure('operation', 'unknown', channel, str(e))
                
            time.sleep(random.uniform(0.001, 0.05))


class StressTestManager:
    """压力测试管理器"""
    
    def __init__(self):
        self.processes = []
        self.running = True
        self.stats = None  # 将在 run_stress_test 中使用 Manager 创建
        
    def signal_handler(self, sig, frame):
        """信号处理函数"""
        print("\n收到中断信号，正在停止压力测试...")
        self.running = False
        self.stop_all()
        
    def stop_all(self):
        """停止所有进程"""
        print("[StressTestManager] 正在停止所有进程...")
        for process in self.processes:
            if process.is_alive():
                print(f"[StressTestManager] 终止进程: {process.name}")
                process.terminate()
                process.join(timeout=2)
                if process.is_alive():
                    print(f"[StressTestManager] 强制终止进程: {process.name}")
                    process.kill()
                    process.join()
        print("[StressTestManager] 所有进程已停止")
        
    def run_stress_test(self, num_workers=10, test_type='mixed', duration=60, **kwargs):
        """
        运行压力测试
        
        Args:
            num_workers: 工作进程数量
            test_type: 测试类型 ('same_channel_conflict', 'different_channels', 'rapid_requests', 
                                 'read_write_mix', 'channel_switching', 'mixed')
            duration: 测试持续时间（秒）
            **kwargs: 其他测试配置参数
        """
        print("=" * 80)
        print("SmartUSBHub 压力测试程序")
        print("=" * 80)
        print(f"测试类型: {test_type}")
        print(f"工作进程数: {num_workers}")
        print(f"测试时长: {duration}秒")
        print("=" * 80)
        
        # 创建共享资源
        shared_manager = Manager()
        request_queue = Queue()
        response_dict = shared_manager.dict()
        
        # 创建共享统计对象（使用 Manager）
        self.stats = StressTestStats(shared_manager)
        
        # 启动服务进程
        print("\n[StressTest] 启动SmartUSBHub服务进程...")
        server_process = Process(
            target=server_process_main,
            args=(request_queue, response_dict, None),
            name="SmartUSBHub-Server"
        )
        server_process.daemon = False
        server_process.start()
        self.processes.append(server_process)
        
        # 等待服务进程初始化
        print("[StressTest] 等待服务进程初始化...")
        time.sleep(3)
        
        if not server_process.is_alive():
            print("[StressTest] 错误: 服务进程启动失败")
            return
            
        print("[StressTest] 服务进程已启动")
        
        # 准备测试配置
        test_config = {
            'test_type': test_type,
            'timeout': kwargs.get('timeout', 5.0),
            'iterations': kwargs.get('iterations', 1000),
            'channel': kwargs.get('channel', 1),
            'channels': kwargs.get('channels', [1, 2, 3, 4])
        }
        
        # 创建工作进程
        print(f"\n[StressTest] 启动 {num_workers} 个工作进程...")
        workers = []
        
        for i in range(num_workers):
            worker = StressTestWorker(i, request_queue, response_dict, self.stats, test_config)
            worker_process = Process(
                target=worker.run,
                name=f"StressWorker-{i}"
            )
            worker_process.daemon = False
            worker_process.start()
            workers.append((worker, worker_process))
            self.processes.append(worker_process)
            print(f"[StressTest] Worker-{i} 已启动")
            time.sleep(0.1)  # 错开启动时间
            
        print("\n[StressTest] 所有工作进程已启动，开始压力测试...")
        print(f"[StressTest] 测试将持续 {duration} 秒，按 Ctrl+C 可提前停止\n")
        
        # 启动统计报告线程
        report_thread = threading.Thread(target=self._report_stats, args=(duration,), daemon=True)
        report_thread.start()
        
        try:
            # 等待测试完成或超时
            start_time = time.time()
            while time.time() - start_time < duration and self.running:
                time.sleep(1)
                
                # 检查服务进程
                if not server_process.is_alive():
                    print("[StressTest] 警告: 服务进程已退出")
                    break
                    
                # 检查工作进程
                dead_workers = [w for _, w in workers if not w.is_alive()]
                if dead_workers:
                    for _, worker_process in dead_workers:
                        print(f"[StressTest] 警告: {worker_process.name} 已退出")
                        
        except KeyboardInterrupt:
            print("\n[StressTest] 收到中断信号")
        finally:
            # 停止所有工作进程
            print("\n[StressTest] 停止所有工作进程...")
            for worker, worker_process in workers:
                worker.running = False
                if worker_process.is_alive():
                    worker_process.join(timeout=2)
                    
            # 停止服务进程
            print("[StressTest] 停止服务进程...")
            self.stop_all()
            
            # 打印最终统计报告
            self._print_final_report()
            
    def _report_stats(self, duration):
        """定期报告统计信息"""
        start_time = time.time()
        report_interval = 10  # 每10秒报告一次
        
        while time.time() - start_time < duration and self.running:
            time.sleep(report_interval)
            elapsed = time.time() - start_time
            summary = self.stats.get_summary()
            
            print(f"\n[统计报告] 已运行 {elapsed:.1f}秒")
            print(f"  总请求数: {summary['total_requests']}")
            print(f"  成功: {summary['successful_requests']} | 失败: {summary['failed_requests']}")
            if summary['total_requests'] > 0:
                print(f"  成功率: {summary['success_rate']:.2f}%")
            print(f"  超时错误: {summary['timeout_errors']} | 运行时错误: {summary['runtime_errors']} | 冲突错误: {summary['conflict_errors']}")
            
    def _print_final_report(self):
        """打印最终测试报告"""
        print("\n" + "=" * 80)
        print("压力测试最终报告")
        print("=" * 80)
        
        summary = self.stats.get_summary()
        
        print(f"\n总体统计:")
        print(f"  总请求数: {summary['total_requests']}")
        print(f"  成功请求: {summary['successful_requests']}")
        print(f"  失败请求: {summary['failed_requests']}")
        print(f"  成功率: {summary['success_rate']:.2f}%")
        
        print(f"\n错误统计:")
        print(f"  超时错误: {summary['timeout_errors']}")
        print(f"  运行时错误: {summary['runtime_errors']}")
        print(f"  冲突错误: {summary['conflict_errors']}")
        
        print(f"\n操作统计:")
        for op, stats in summary['operation_stats'].items():
            total = stats['success'] + stats['fail']
            success_rate = (stats['success'] / total * 100) if total > 0 else 0
            print(f"  {op}:")
            print(f"    成功: {stats['success']} | 失败: {stats['fail']} | 成功率: {success_rate:.2f}%")
            
        print(f"\n通道统计:")
        for channel, stats in sorted(summary['channel_stats'].items()):
            conflict_rate = (stats['conflicts'] / stats['operations'] * 100) if stats['operations'] > 0 else 0
            print(f"  通道{channel}:")
            print(f"    操作数: {stats['operations']} | 冲突数: {stats['conflicts']} | 冲突率: {conflict_rate:.2f}%")
            
        print("=" * 80)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SmartUSBHub 压力测试程序')
    parser.add_argument('--workers', type=int, default=10, help='工作进程数量 (默认: 10)')
    parser.add_argument('--duration', type=int, default=60, help='测试持续时间（秒）(默认: 60)')
    parser.add_argument('--test-type', type=str, default='mixed',
                       choices=['same_channel_conflict', 'different_channels', 'rapid_requests',
                                'read_write_mix', 'channel_switching', 'mixed'],
                       help='测试类型 (默认: mixed)')
    parser.add_argument('--channel', type=int, default=1, help='测试通道（用于单通道测试）(默认: 1)')
    parser.add_argument('--iterations', type=int, default=1000, help='每个工作进程的迭代次数 (默认: 1000)')
    parser.add_argument('--timeout', type=float, default=5.0, help='请求超时时间（秒）(默认: 5.0)')
    
    args = parser.parse_args()
    
    manager = StressTestManager()
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    manager.run_stress_test(
        num_workers=args.workers,
        test_type=args.test_type,
        duration=args.duration,
        channel=args.channel,
        iterations=args.iterations,
        timeout=args.timeout
    )


if __name__ == "__main__":
    main()


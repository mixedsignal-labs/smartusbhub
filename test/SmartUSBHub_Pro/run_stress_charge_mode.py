#!/usr/bin/env python
"""
SmartUSBHub Pro 充电模式切换压力测试运行脚本

使用方法:
    python test/SmartUSBHub_Pro/run_stress_charge_mode.py                # 运行测试并自动打开报告
    python test/SmartUSBHub_Pro/run_stress_charge_mode.py --no-open     # 运行测试但不打开报告
    python test/SmartUSBHub_Pro/run_stress_charge_mode.py --no-html     # 运行测试但不生成HTML报告
"""
import sys
import os
import argparse

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if __name__ == '__main__':
    import pytest
    
    parser = argparse.ArgumentParser(description="运行 SmartUSBHub Pro 充电模式切换压力测试")
    parser.add_argument("--no-open", action="store_true", help="不自动打开HTML报告")
    parser.add_argument("--no-html", action="store_true", help="不生成HTML报告")
    parser.add_argument("--count", type=int, help="测试次数（覆盖默认值）")
    args, pytest_args = parser.parse_known_args()
    
    # 如果指定了测试次数，通过环境变量传递
    if args.count:
        os.environ['STRESS_TEST_COUNT'] = str(args.count)
    
    # 确定测试文件
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(test_dir, "test_stress_charge_mode_switch.py")
    report_name = "report_stress_charge_mode.html"
    
    # 检查测试文件是否存在
    if not os.path.exists(test_file):
        print(f"[ERROR] 测试文件不存在: {test_file}")
        sys.exit(1)
    
    # 默认参数
    test_args = [
        test_file,
        '-v',                    # 详细输出
        '-s',                    # 显示print输出
        '--log-cli-level=INFO',  # 日志级别
        '--tb=short',            # 简短错误信息
    ]
    
    # 添加pytest命令行参数
    if pytest_args:
        test_args.extend(pytest_args)
    
    # 检查是否安装 pytest-html 插件
    report_path = None
    try:
        import pytest_html
        html_available = True
    except ImportError:
        html_available = False
    
    # 生成HTML报告
    if html_available and not args.no_html:
        report_dir = os.path.join(test_dir, "report")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, report_name)
        test_args.extend([
            "--html", report_path,
            "--self-contained-html"
        ])
        print(f"将生成HTML报告: {report_path}")
    elif not html_available:
        print("[WARNING] pytest-html 插件未安装，跳过HTML报告生成")
        print("  安装命令: pip install pytest-html")
    
    print("\n" + "="*70)
    print("SmartUSBHub Pro - 充电模式切换压力测试")
    print("="*70)
    if args.count:
        print(f"测试次数: {args.count}")
    print()
    
    exit_code = pytest.main(test_args)
    
    # 测试完成后，如果报告存在，自动打开
    if not args.no_open and report_path:
        report_abs_path = os.path.abspath(report_path)
        if os.path.exists(report_abs_path):
            print(f"\n[OK] HTML报告已生成: {report_abs_path}")
            try:
                import webbrowser
                if os.name == 'nt':  # Windows
                    report_url = report_abs_path.replace('\\', '/')
                    if not report_url.startswith('/'):
                        report_url = '/' + report_url
                    report_url = f"file://{report_url}"
                else:  # macOS/Linux
                    report_url = f"file://{report_abs_path}"
                webbrowser.open(report_url)
                print("[OK] 已在浏览器中打开报告")
            except Exception as e:
                print(f"[WARNING] 无法自动打开浏览器: {e}")
                print(f"  请手动打开: {report_abs_path}")
        else:
            print(f"\n[WARNING] 报告文件未找到: {report_abs_path}")
    
    sys.exit(exit_code)



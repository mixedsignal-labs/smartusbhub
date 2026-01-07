#!/usr/bin/env python
"""
SmartUSBHub Pro 测试运行脚本

使用方法:
    python SmartUSBHub_Pro/run_tests.py --type integration          # 运行接口测试
    python SmartUSBHub_Pro/run_tests.py --type stress               # 运行核心功能压力测试
    python SmartUSBHub_Pro/run_tests.py --type stress_charge_mode   # 运行充电模式切换压力测试
    python SmartUSBHub_Pro/run_tests.py --type stress_charge_mode --count 1000  # 指定测试次数
    python SmartUSBHub_Pro/run_tests.py --all                      # 运行所有测试
    python SmartUSBHub_Pro/run_tests.py --no-open                  # 不自动打开报告
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
    
    parser = argparse.ArgumentParser(description="运行 SmartUSBHub Pro 测试")
    parser.add_argument("--type", 
                       choices=["integration", "stress", "stress_charge_mode", "all"], 
                       default="all",
                       help="测试类型: integration(接口测试), stress(核心功能压力测试), stress_charge_mode(充电模式切换压力测试), all(全部)")
    parser.add_argument("--no-open", action="store_true", help="不自动打开HTML报告")
    parser.add_argument("--no-html", action="store_true", help="不生成HTML报告")
    parser.add_argument("--count", type=int, help="压力测试次数（仅用于 stress_charge_mode）")
    args, pytest_args = parser.parse_known_args()
    
    # 如果指定了测试次数，通过环境变量传递
    if args.count:
        os.environ['STRESS_TEST_COUNT'] = str(args.count)
    
    # 设置产品信息和测试类型到环境变量（供 conftest.py 使用）
    os.environ['TEST_PRODUCT'] = 'SmartUSBHub Pro'
    if args.type == "integration":
        os.environ['TEST_TYPE'] = '接口测试'
    elif args.type == "stress":
        os.environ['TEST_TYPE'] = '核心功能压力测试'
    elif args.type == "stress_charge_mode":
        os.environ['TEST_TYPE'] = '充电模式切换压力测试'
    else:  # all
        os.environ['TEST_TYPE'] = '全部测试'
    
    # 确定测试文件
    test_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.join(test_dir, "tests")
    if args.type == "integration":
        test_files = [os.path.join(tests_dir, "test_integration.py")]
        report_name = "report_integration.html"
    elif args.type == "stress":
        test_files = [os.path.join(tests_dir, "test_stress.py")]
        report_name = "report_stress.html"
    elif args.type == "stress_charge_mode":
        test_files = [os.path.join(tests_dir, "test_stress_charge_mode_switch.py")]
        report_name = "report_stress_charge_mode.html"
    else:  # all
        test_files = [
            os.path.join(tests_dir, "test_integration.py"),
            os.path.join(tests_dir, "test_stress.py"),
            os.path.join(tests_dir, "test_stress_charge_mode_switch.py")
        ]
        report_name = "report_all.html"
    
    # 默认参数
    test_args = test_files + [
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
    print(f"开始运行 SmartUSBHub Pro 测试 ({args.type})...")
    if args.count:
        print(f"测试次数: {args.count}")
    print("="*70 + "\n")
    
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


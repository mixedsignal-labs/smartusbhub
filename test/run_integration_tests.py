#!/usr/bin/env python
"""
运行集成测试 - 直接连接真实设备

使用方法:
    python test/run_integration_tests.py              # 运行所有测试并自动打开HTML报告
    python test/run_integration_tests.py --no-open    # 运行测试但不自动打开报告
    python test/run_integration_tests.py -k voltage   # 运行包含voltage的测试
    python test/run_integration_tests.py --tb=short   # 简短错误信息
"""
import sys
import os
import argparse

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == '__main__':
    import pytest
    
    parser = argparse.ArgumentParser(description="运行 SmartUSBHub 集成测试")
    parser.add_argument("--no-open", action="store_true", help="不自动打开HTML报告（默认会自动打开）")
    parser.add_argument("--no-html", action="store_true", help="不生成HTML报告")
    # 解析已知参数，剩余参数传递给pytest
    args, pytest_args = parser.parse_known_args()
    
    # 默认参数
    test_args = [
        'test/test_integration.py',
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
    
    # 默认总是生成HTML报告（如果插件可用且未指定 --no-html）
    if html_available and not args.no_html:
        report_path = os.path.join(os.path.dirname(__file__), "report.html")
        test_args.extend([
            "--html", report_path,
            "--self-contained-html"
        ])
        print(f"将生成HTML报告: {report_path}")
    elif not html_available:
        print("[WARNING] pytest-html 插件未安装，跳过HTML报告生成")
        print("  安装命令: pip install pytest-html")
    
    print("\n" + "="*70)
    print("开始运行集成测试...")
    print("="*70 + "\n")
    
    exit_code = pytest.main(test_args)
    
    # 测试完成后，如果报告存在，自动打开（除非指定了 --no-open）
    if not args.no_open:
        if os.path.exists(report_path):
            print(f"\n[OK] HTML报告已生成: {report_path}")
            try:
                import webbrowser
                webbrowser.open_new_tab(f"file:///{os.path.abspath(report_path)}")
                print("[OK] 已在浏览器中打开报告")
            except Exception as e:
                print(f"[WARNING] 无法自动打开浏览器: {e}")
                print(f"  请手动打开: {os.path.abspath(report_path)}")
        else:
            print(f"\n[WARNING] 报告文件未找到: {report_path}")
    
    sys.exit(exit_code)


@echo off
REM SmartUSBHub 压力测试快速启动脚本 (Windows)

echo SmartUSBHub 压力测试 - 快速启动
echo ================================
echo.
echo 请选择测试场景:
echo 1. 混合场景测试 (推荐，默认)
echo 2. 同一通道并发冲突测试
echo 3. 不同通道并发操作测试
echo 4. 快速连续请求测试
echo 5. 读写混合操作测试
echo 6. 通道快速切换测试
echo 7. 自定义测试
echo.
set /p choice="请输入选项 (1-7, 默认1): "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo 运行混合场景测试...
    python stress_test.py --test-type mixed --workers 10 --duration 60
) else if "%choice%"=="2" (
    echo 运行同一通道并发冲突测试...
    set /p channel="请输入通道号 (1-4, 默认1): "
    if "%channel%"=="" set channel=1
    python stress_test.py --test-type same_channel_conflict --workers 15 --channel %channel% --duration 60
) else if "%choice%"=="3" (
    echo 运行不同通道并发操作测试...
    python stress_test.py --test-type different_channels --workers 16 --duration 90
) else if "%choice%"=="4" (
    echo 运行快速连续请求测试...
    python stress_test.py --test-type rapid_requests --workers 30 --duration 30 --timeout 3.0
) else if "%choice%"=="5" (
    echo 运行读写混合操作测试...
    set /p channel="请输入通道号 (1-4, 默认1): "
    if "%channel%"=="" set channel=1
    python stress_test.py --test-type read_write_mix --workers 10 --channel %channel% --duration 60
) else if "%choice%"=="6" (
    echo 运行通道快速切换测试...
    python stress_test.py --test-type channel_switching --workers 12 --duration 60
) else if "%choice%"=="7" (
    echo 自定义测试配置...
    set /p test_type="测试类型 (mixed/same_channel_conflict/different_channels/rapid_requests/read_write_mix/channel_switching): "
    set /p workers="工作进程数 (默认10): "
    if "%workers%"=="" set workers=10
    set /p duration="测试时长/秒 (默认60): "
    if "%duration%"=="" set duration=60
    set /p channel="通道号 (默认1): "
    if "%channel%"=="" set channel=1
    python stress_test.py --test-type %test_type% --workers %workers% --duration %duration% --channel %channel%
) else (
    echo 无效选项，运行默认混合场景测试...
    python stress_test.py --test-type mixed --workers 10 --duration 60
)

pause



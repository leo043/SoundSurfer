import time
import json
import os
import sys
import logging
from screeninfo import get_monitors
import pygetwindow as gw
import subprocess

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./audio_switcher.log"),
        logging.StreamHandler()
    ]
)

def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 创建默认配置
        default_config = {
            "window_titles": ["Edge"],
            "screen_devices": {
                "DISPLAY1": "扬声器",
                "DISPLAY2": "Mi Monitor"
            },
            "not_found_threshold": 3,
            "check_interval": 1
        }
        with open('./config.json', 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        logging.info("已创建默认配置文件 config.json")
        return default_config
    
def set_audio_device(device_name):
    """设置默认音频设备"""
    try:
        command = f'nircmd setdefaultsounddevice "{device_name}"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"已切换到 {device_name}")
            return True
        else:
            logging.error(f"切换设备失败: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"执行命令时出错: {e}")
        return False
    
def get_screen_of_window(window_title):
    """获取窗口所在的屏幕"""
    try:
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            return None
        window = windows[0]
        rect = window._rect
        window_center_x = rect.left + (rect.right - rect.left) // 2
        window_center_y = rect.top + (rect.bottom - rect.top) // 2
        for monitor in get_monitors():
            if (monitor.x <= window_center_x <= monitor.x + monitor.width and
                    monitor.y <= window_center_y <= monitor.y + monitor.height):
                return monitor.name
        return None
    except Exception as e:
        logging.error(f"获取窗口屏幕时出错: {e}")
        return None
    
def monitor_window_movement(config):
    """监控窗口移动并切换音频设备"""
    prev_screen = None
    not_found_count = 0
    window_titles = config["window_titles"]
    screen_devices = config["screen_devices"]
    not_found_threshold = config["not_found_threshold"]
    check_interval = config["check_interval"]
    logging.info(f"开始监控窗口: {window_titles}")
    logging.info(f"程序将在检测不到窗口{not_found_threshold}次后自动退出")

    while True:
        # 尝试找到任一窗口
        screen_name = None
        found_window = None
        for title in window_titles:
            screen_name = get_screen_of_window(title)
            if screen_name:
                found_window = title
                break
        # 检查窗口是否存在
        if screen_name is None:
            not_found_count += 1
            logging.info(f"窗口未找到! ({not_found_count}/{not_found_threshold})")
            if not_found_count >= not_found_threshold:
                logging.info("窗口已关闭。程序退出...")
                return
        else:
            not_found_count = 0
            # 仅当屏幕变化时执行设备切换
            if screen_name != prev_screen:
                prev_screen = screen_name
                logging.info(f"窗口 '{found_window}' 移动到屏幕: {screen_name}")
                # 查找匹配的设备
                device_name = None
                for display_key, device in screen_devices.items():
                    if display_key in screen_name:
                        device_name = device
                        break
                # 切换设备
                if device_name:
                    set_audio_device(device_name)
                else:
                    logging.warning(f"未找到屏幕 {screen_name} 对应的音频设备")
        time.sleep(check_interval)

        
if __name__ == "__main__":
    try:
        config = load_config()
        monitor_window_movement(config)
    except KeyboardInterrupt:
        logging.info("用户中断，程序退出")
    except Exception as e:
        logging.error(f"程序异常: {e}")
    finally:
        logging.info("程序已退出")

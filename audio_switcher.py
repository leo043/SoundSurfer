import time
import json
import os
import sys
import logging
from screeninfo import get_monitors
import pygetwindow as gw
import subprocess
import threading
import keyboard

# 自动创建日志文件夹
log_dir = "./log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "audio_switcher.log")),
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
    
use_headphone = False  # 新增全局变量

def listen_for_space_switch():
    """监听 Ctrl+空格 切换 Headphone/自动模式"""
    global use_headphone
    while True:
        if keyboard.is_pressed('ctrl+space'):
            use_headphone = not use_headphone
            if use_headphone:
                logging.info("已切换到耳机模式")
                set_audio_device("Headphone")
            else:
                logging.info("已恢复到自动模式")
                # 主动触发一次自动切换
                try:
                    config = load_config()
                    window_titles = config["window_titles"]
                    screen_devices = config["screen_devices"]
                    # 查找当前窗口所在屏幕
                    screen_name = None
                    for title in window_titles:
                        screen_name = get_screen_of_window(title)
                        if screen_name:
                            break
                    if screen_name:
                        device_name = None
                        for display_key, device in screen_devices.items():
                            if display_key in screen_name:
                                device_name = device
                                break
                        if device_name:
                            set_audio_device(device_name)
                        else:
                            logging.warning(f"未找到屏幕 {screen_name} 对应的音频设备")
                    else:
                        logging.info("自动模式恢复时未找到目标窗口")
                except Exception as e:
                    logging.error(f"自动模式恢复时切换设备出错: {e}")
            # 防止多次触发，等待按键松开
            while keyboard.is_pressed('ctrl+space'):
                time.sleep(0.1)
        time.sleep(0.1)

def monitor_window_movement(config):
    """监控窗口移动并切换音频设备"""
    global use_headphone
    prev_screen = None
    not_found_count = 0
    window_titles = config["window_titles"]
    screen_devices = config["screen_devices"]
    not_found_threshold = config["not_found_threshold"]
    check_interval = config["check_interval"]
    logging.info(f"开始监控窗口: {window_titles}")
    logging.info(f"程序将在检测不到窗口{not_found_threshold}次后自动退出")

    while True:
        if use_headphone:
            time.sleep(check_interval)
            continue
        
        screen_name = None
        found_window = None
        for title in window_titles:
            screen_name = get_screen_of_window(title)
            if screen_name:
                found_window = title
                break
        
        if screen_name is None:
            not_found_count += 1
            logging.info(f"窗口未找到! ({not_found_count}/{not_found_threshold})")
            if not_found_count >= not_found_threshold:
                logging.info("窗口已关闭。程序退出...")
                return
        else:
            not_found_count = 0
            if screen_name != prev_screen:
                prev_screen = screen_name
                logging.info(f"窗口 '{found_window}' 移动到屏幕: {screen_name}")
                device_name = None
                for display_key, device in screen_devices.items():
                    if display_key in screen_name:
                        device_name = device
                        break
                if device_name:
                    set_audio_device(device_name)
                else:
                    logging.warning(f"未找到屏幕 {screen_name} 对应的音频设备")
        time.sleep(check_interval)
        
if __name__ == "__main__":
    try:
        config = load_config()
         # 启动监听线程
        threading.Thread(target=listen_for_space_switch, daemon=True).start()
        monitor_window_movement(config)
    except KeyboardInterrupt:
        logging.info("用户中断，程序退出")
    except Exception as e:
        logging.error(f"程序异常: {e}")
    finally:
        logging.info("程序已退出")

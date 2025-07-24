import json
import logging
import os
from tkinter import Tk, Frame, Label, messagebox, StringVar, Scrollbar, Canvas, VERTICAL, Button
from tkinter.ttk import Radiobutton, Style
import pygetwindow as gw
import win32gui
import re

# 自动创建日志文件夹
log_dir = "./log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "select_window.log")),
        logging.StreamHandler()
    ]
)

# 无关窗口标题的关键词黑名单
EXCLUDED_KEYWORDS = [
    "设置",
    "输入体验",
    "Program Manager",
    "Default IME",
    "MSCTFIME UI"
]

# 浏览器标识（用于简化标题）
BROWSER_NAMES = ["Edge", "Google Chrome", "Firefox", "Opera", "Safari", "Brave", "Vivaldi"]

def simplify_title(title):
    """简化浏览器窗口标题，只保留浏览器名称"""
    for browser in BROWSER_NAMES:
        if browser in title:
            return browser
    return title

def load_config():
    """加载配置文件"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("未找到配置文件 config.json，请确保该文件存在！")
        messagebox.showerror("错误", "未找到配置文件 config.json，请确保该文件存在！")
        return None

def save_config(config):
    """保存配置文件"""
    try:
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logging.info("配置文件已更新")
    except Exception as e:
        logging.error(f"保存配置文件时出错: {e}")
        messagebox.showerror("错误", f"保存配置文件时出错: {e}")

def is_window_visible(hwnd):
    """检查窗口是否可见"""
    return win32gui.IsWindowVisible(hwnd)

def filter_windows(windows):
    """过滤无效窗口并简化浏览器标题"""
    valid_windows = []
    for window in windows:
        # 过滤空标题或黑名单中的窗口
        if window.strip() and not any(keyword in window for keyword in EXCLUDED_KEYWORDS):
            # 通过窗口句柄检查可见性
            try:
                hwnd = gw.getWindowsWithTitle(window)[0]._hWnd
                if is_window_visible(hwnd):
                    # 简化浏览器窗口标题
                    simplified_title = simplify_title(window)
                    valid_windows.append(simplified_title)
            except IndexError:
                continue
    return valid_windows

def select_window():
    """弹窗让用户选择窗口"""
    config = load_config()
    if not config:
        return

    def on_select():
        selected = selected_var.get()
        if not selected:
            messagebox.showwarning("未选择", "请先选择一个窗口")
            return
        config["window_titles"] = [selected]
        save_config(config)
        messagebox.showinfo("成功", f"已将监控窗口设置为: {selected}")
        root.destroy()
    
    def on_mousewheel(event):
        """处理鼠标滚轮事件"""
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # 创建主窗口
    root = Tk()
    root.title("SoundSurfer")
    root.geometry("600x500")
    root.resizable(False, False)
    root.configure(bg="#f0f0f5")  # 背景颜色
    
    # 设置样式
    style = Style()
    style.configure("TRadiobutton", font=("Microsoft YaHei", 12), padding=5)
    
    # 使用顶部区域包装标题和滚动区域
    top_frame = Frame(root, bg="#f0f0f5")
    top_frame.pack(side="top", fill="both", expand=True, padx=20, pady=(20, 10))
    
    # 标题标签
    title_label = Label(top_frame, text="请选择一个窗口进行监控：", font=("Microsoft YaHei", 14), bg="#f0f0f5", anchor="w")
    title_label.pack(fill="x", pady=(0, 10))
    
    # 创建滚动区域
    canvas = Canvas(top_frame, bg="#f0f0f5", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)
    
    scrollbar = Scrollbar(top_frame, orient=VERTICAL, command=canvas.yview)
    scrollbar.pack(side="right", fill="y")
    
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollable_frame = Frame(canvas, bg="#f0f0f5")
    
    # 绑定鼠标滚轮事件
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    
    # 加载并过滤窗口
    windows = filter_windows(gw.getAllTitles())
    
    # 动态生成单选按钮
    selected_var = StringVar()
    for window in windows:
        # 包裹单选按钮的 Frame，使整个行可以点击
        row_frame = Frame(scrollable_frame, bg="#ffffff", highlightbackground="#d9d9d9", highlightthickness=1)
        row_frame.pack(fill="x", pady=2)
        
        rb = Radiobutton(
            row_frame,
            text=window,
            value=window,
            variable=selected_var,
            style="TRadiobutton",
            width=65,  # 宽度设置为足够填满整行
        )
        rb.pack(fill="x", padx=5, pady=5)
        
        # 绑定点击事件，让行的背景颜色变化
        def on_row_click(event, value=window):
            selected_var.set(value)
        
        row_frame.bind("<Button-1>", on_row_click)
    
    # 创建底部区域，用于放置"确定"按钮
    bottom_frame = Frame(root, bg="#f0f0f5")
    bottom_frame.pack(side="bottom", fill="x", pady=(5, 10))
    
    # 确定按钮
    btn_select = Button(
        bottom_frame,
        text="确定",
        command=on_select,
        bg="#e0e0e0",  # 使用灰色背景（默认按钮背景色）
        fg="black",
        font=("Microsoft YaHei", 12)
    )
    btn_select.pack(ipadx=10, ipady=5)
    
    root.mainloop()

if __name__ == "__main__":
    try:
        select_window()
    except Exception as e:
        logging.error(f"程序异常: {e}")
        messagebox.showerror("错误", f"程序异常: {e}")
    finally:
        logging.info("窗口选择工具已退出")
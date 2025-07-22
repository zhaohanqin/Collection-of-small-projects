import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

def start_app():
    try:
        # 尝试导入新版本
        import importlib.util
        spec = importlib.util.spec_from_file_location("crypto_app_v3", os.path.join(os.path.dirname(__file__), "加密解密器_v3.0.py"))
        crypto_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(crypto_app)
        
        # 关闭启动器窗口
        root.destroy()
        
        # 启动新版本
        app_root = tk.Tk()
        app = crypto_app.ModernCryptoApp(app_root)
        app_root.mainloop()
    except Exception as e:
        messagebox.showerror("启动错误", f"无法启动加密解密器 v3.0: {str(e)}")

# 创建启动器窗口
root = tk.Tk()
root.title("加密解密器启动器")
root.geometry("400x200")
root.configure(bg="#f5f7fa")

# 设置样式
style = ttk.Style()
style.configure("TButton", font=("Microsoft YaHei", 12), padding=10)
style.configure("TLabel", font=("Microsoft YaHei", 14, "bold"), background="#f5f7fa")

# 创建界面
frame = ttk.Frame(root, padding=20)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="加密解密工具启动器").pack(pady=(10, 30))

ttk.Button(frame, text="启动加密解密器 v3.0", command=start_app).pack(fill="x", pady=10)

# 启动窗口
root.mainloop() 
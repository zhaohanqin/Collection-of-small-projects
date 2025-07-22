import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import base64
from PIL import Image, ImageTk
import os
import random
import string


class ModernCryptoApp:
    def __init__(self, master):
        self.master = master
        master.title("🔒 加密解密器 v3.0 🔓")
        master.geometry("780x580")
        master.configure(bg="#f5f7fa")
        
        # 颜色方案 - 浅色系
        self.colors = {
            "bg": "#f5f7fa",           # 背景色
            "primary": "#a5d8ff",      # 主色
            "primary_light": "#d0ebff", # 主色浅色
            "secondary": "#d8f5a5",    # 次色
            "text": "#495057",         # 文字颜色
            "border": "#dee2e6",       # 边框颜色
            "button": "#91c4f8",       # 按钮颜色
            "button_hover": "#74b3f8", # 按钮悬停颜色
            "error": "#ff8787",        # 错误颜色
            "success": "#8ce99a"       # 成功颜色
        }
        
        # 设置字体
        self.fonts = {
            "title": ("Microsoft YaHei", 16, "bold"),
            "heading": ("Microsoft YaHei", 14, "bold"),
            "normal": ("Microsoft YaHei", 12),
            "small": ("Microsoft YaHei", 10)
        }
        
        # 初始化变量
        self.mode_var = tk.StringVar(value="加密")
        self.algorithm_var = tk.StringVar(value="Unicode偏移")
        self.shift_var = tk.StringVar(value="3")
        self.key_var = tk.StringVar(value="")
        
        # 创建自定义样式
        self.create_styles()
        
        # 创建主界面
        self.create_widgets()
        
        # 绑定事件
        self.algorithm_var.trace_add("write", self.update_input_options)
        
        # 初始设置
        self.update_input_options()
        
        # 随机生成密钥
        self.generate_random_key()

    def create_styles(self):
        """创建自定义样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 使用clam主题作为基础
        
        # 配置全局样式
        self.style.configure(".", 
                            font=self.fonts["normal"],
                            background=self.colors["bg"],
                            foreground=self.colors["text"])
        
        # 标签样式
        self.style.configure("TLabel", 
                            background=self.colors["bg"],
                            foreground=self.colors["text"])
        
        # 标签框样式
        self.style.configure("TLabelframe", 
                            background=self.colors["bg"],
                            foreground=self.colors["text"])
        self.style.configure("TLabelframe.Label", 
                            font=self.fonts["heading"],
                            background=self.colors["bg"],
                            foreground=self.colors["text"])
        
        # 按钮样式
        self.style.configure("TButton", 
                            font=self.fonts["normal"],
                            background=self.colors["button"],
                            foreground=self.colors["text"],
                            borderwidth=0,
                            focusthickness=0,
                            padding=8)
        self.style.map("TButton",
                      background=[('active', self.colors["button_hover"])],
                      relief=[('pressed', 'sunken')])
        
        # 单选按钮样式
        self.style.configure("TRadiobutton", 
                            background=self.colors["bg"],
                            foreground=self.colors["text"],
                            font=self.fonts["normal"])
        
        # 下拉菜单样式
        self.style.configure("TCombobox", 
                            font=self.fonts["normal"],
                            background=self.colors["bg"],
                            fieldbackground=self.colors["bg"])
        
        # 主按钮样式
        self.style.configure("Primary.TButton", 
                            font=self.fonts["normal"],
                            background=self.colors["primary"],
                            foreground=self.colors["text"])
        self.style.map("Primary.TButton",
                      background=[('active', self.colors["primary_light"])])
        
        # 次要按钮样式
        self.style.configure("Secondary.TButton", 
                            font=self.fonts["normal"],
                            background=self.colors["secondary"],
                            foreground=self.colors["text"])

    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.master, style="TFrame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 顶部标题
        title_frame = ttk.Frame(main_frame, style="TFrame")
        title_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ttk.Label(title_frame, 
                               text="加密解密工具", 
                               font=self.fonts["title"],
                               foreground=self.colors["text"],
                               background=self.colors["bg"])
        title_label.pack(side="left")
        
        # 模式选择区域
        mode_frame = ttk.LabelFrame(main_frame, text="操作模式", style="TLabelframe")
        mode_frame.pack(fill="x", pady=(0, 15), ipady=5)
        
        mode_inner_frame = ttk.Frame(mode_frame, style="TFrame")
        mode_inner_frame.pack(fill="x", padx=15, pady=10)
        
        # 水平布局模式选择
        encrypt_radio = ttk.Radiobutton(mode_inner_frame, 
                                      text="加密", 
                                      variable=self.mode_var,
                                      value="加密", 
                                      style="TRadiobutton")
        encrypt_radio.pack(side="left", padx=(0, 30))
        
        decrypt_radio = ttk.Radiobutton(mode_inner_frame, 
                                      text="解密", 
                                      variable=self.mode_var,
                                      value="解密", 
                                      style="TRadiobutton")
        decrypt_radio.pack(side="left")
        
        # 算法选择区域
        algo_frame = ttk.LabelFrame(main_frame, text="加密算法", style="TLabelframe")
        algo_frame.pack(fill="x", pady=(0, 15), ipady=5)
        
        algo_inner_frame = ttk.Frame(algo_frame, style="TFrame")
        algo_inner_frame.pack(fill="x", padx=15, pady=10)
        
        # 算法选择下拉菜单
        ttk.Label(algo_inner_frame, text="选择算法:", style="TLabel").pack(side="left", padx=(0, 10))
        
        algorithms = ["Unicode偏移", "Base64编码", "凯撒密码", "异或加密"]
        algo_combobox = ttk.Combobox(algo_inner_frame, 
                                   textvariable=self.algorithm_var,
                                   values=algorithms,
                                   state="readonly",
                                   width=15)
        algo_combobox.pack(side="left")
        
        # 输入参数区域
        params_frame = ttk.LabelFrame(main_frame, text="参数设置", style="TLabelframe")
        params_frame.pack(fill="x", pady=(0, 15), ipady=5)
        
        self.params_inner_frame = ttk.Frame(params_frame, style="TFrame")
        self.params_inner_frame.pack(fill="x", padx=15, pady=10)
        
        # 输入区域
        input_frame = ttk.LabelFrame(main_frame, text="输入文本", style="TLabelframe")
        input_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        input_inner_frame = ttk.Frame(input_frame, style="TFrame")
        input_inner_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # 创建带有圆角和边框的文本输入框
        self.input_text = tk.Text(input_inner_frame, 
                                wrap="word",
                                font=self.fonts["normal"],
                                bg="#ffffff",
                                fg=self.colors["text"],
                                relief="flat",
                                bd=0,
                                highlightthickness=1,
                                highlightbackground=self.colors["border"],
                                highlightcolor=self.colors["primary"])
        self.input_text.pack(fill="both", expand=True)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame, style="TFrame")
        button_frame.pack(fill="x", pady=(0, 15))
        
        # 创建操作按钮
        self.process_button = ttk.Button(button_frame, 
                                      text="执行操作", 
                                      command=self.process_text,
                                      style="Primary.TButton")
        self.process_button.pack(side="left", padx=(0, 10))
        
        self.clear_button = ttk.Button(button_frame, 
                                    text="清空", 
                                    command=self.clear_text,
                                    style="TButton")
        self.clear_button.pack(side="left", padx=(0, 10))
        
        self.save_button = ttk.Button(button_frame, 
                                   text="保存结果", 
                                   command=self.save_result,
                                   style="TButton")
        self.save_button.pack(side="left")
        
        # 结果区域
        output_frame = ttk.LabelFrame(main_frame, text="结果输出", style="TLabelframe")
        output_frame.pack(fill="both", expand=True)
        
        output_inner_frame = ttk.Frame(output_frame, style="TFrame")
        output_inner_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # 创建带有圆角和边框的文本输出框
        self.output_text = tk.Text(output_inner_frame, 
                                 wrap="word",
                                 font=self.fonts["normal"],
                                 bg="#ffffff",
                                 fg=self.colors["text"],
                                 relief="flat",
                                 bd=0,
                                 highlightthickness=1,
                                 highlightbackground=self.colors["border"],
                                 highlightcolor=self.colors["primary"],
                                 state="disabled")
        self.output_text.pack(fill="both", expand=True)
        
        # 状态栏
        status_frame = ttk.Frame(main_frame, style="TFrame")
        status_frame.pack(fill="x", pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, 
                                    text="就绪", 
                                    font=self.fonts["small"],
                                    foreground=self.colors["text"],
                                    background=self.colors["bg"])
        self.status_label.pack(side="left")
        
        # 版本信息
        version_label = ttk.Label(status_frame, 
                                text="v3.0", 
                                font=self.fonts["small"],
                                foreground=self.colors["text"],
                                background=self.colors["bg"])
        version_label.pack(side="right")

    def update_input_options(self, *args):
        """根据选择的算法更新输入选项"""
        # 清除现有的参数控件
        for widget in self.params_inner_frame.winfo_children():
            widget.destroy()
            
        algorithm = self.algorithm_var.get()
        
        if algorithm == "Unicode偏移":
            ttk.Label(self.params_inner_frame, text="偏移量:", style="TLabel").pack(side="left", padx=(0, 10))
            shift_entry = ttk.Entry(self.params_inner_frame, 
                                  textvariable=self.shift_var,
                                  width=8,
                                  font=self.fonts["normal"])
            shift_entry.pack(side="left")
            
        elif algorithm == "Base64编码":
            # Base64不需要额外参数
            ttk.Label(self.params_inner_frame, text="Base64编码不需要额外参数", style="TLabel").pack(side="left")
            
        elif algorithm == "凯撒密码":
            ttk.Label(self.params_inner_frame, text="偏移量:", style="TLabel").pack(side="left", padx=(0, 10))
            shift_entry = ttk.Entry(self.params_inner_frame, 
                                  textvariable=self.shift_var,
                                  width=8,
                                  font=self.fonts["normal"])
            shift_entry.pack(side="left")
            
        elif algorithm == "异或加密":
            ttk.Label(self.params_inner_frame, text="密钥:", style="TLabel").pack(side="left", padx=(0, 10))
            key_entry = ttk.Entry(self.params_inner_frame, 
                                textvariable=self.key_var,
                                width=20,
                                font=self.fonts["normal"])
            key_entry.pack(side="left", padx=(0, 10))
            
            generate_button = ttk.Button(self.params_inner_frame, 
                                       text="生成随机密钥", 
                                       command=self.generate_random_key,
                                       style="Secondary.TButton")
            generate_button.pack(side="left")

    def generate_random_key(self):
        """生成随机密钥"""
        # 生成16位随机字符串作为密钥
        key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.key_var.set(key)

    def unicode_encrypt(self, text, shift):
        """Unicode偏移加密"""
        return ''.join([chr(ord(c) + shift) for c in text])
        
    def unicode_decrypt(self, text, shift):
        """Unicode偏移解密"""
        return ''.join([chr(ord(c) - shift) for c in text])
        
    def base64_encrypt(self, text):
        """Base64加密"""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')
        
    def base64_decrypt(self, text):
        """Base64解密"""
        try:
            return base64.b64decode(text.encode('utf-8')).decode('utf-8')
        except Exception as e:
            raise ValueError("无效的Base64编码")
            
    def caesar_encrypt(self, text, shift):
        """凯撒密码加密"""
        result = ""
        # 对字母进行偏移
        for char in text:
            if char.isalpha():
                ascii_offset = ord('a') if char.islower() else ord('A')
                # 计算偏移后的字符
                result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
            else:
                result += char
        return result
        
    def caesar_decrypt(self, text, shift):
        """凯撒密码解密"""
        return self.caesar_encrypt(text, 26 - (shift % 26))
        
    def xor_encrypt(self, text, key):
        """异或加密"""
        result = ""
        for i in range(len(text)):
            result += chr(ord(text[i]) ^ ord(key[i % len(key)]))
        return result
        
    def xor_decrypt(self, text, key):
        """异或解密 (与加密相同)"""
        return self.xor_encrypt(text, key)

    def process_text(self):
        """处理文本"""
        try:
            text = self.input_text.get("1.0", "end").strip()
            if not text:
                self.show_status("请输入要处理的文本", "error")
                return
                
            algorithm = self.algorithm_var.get()
            mode = self.mode_var.get()
            
            # 根据算法和模式处理文本
            if algorithm == "Unicode偏移":
                try:
                    shift = int(self.shift_var.get())
                except ValueError:
                    self.show_status("偏移量必须为整数", "error")
                    return
                    
                if mode == "加密":
                    result = self.unicode_encrypt(text, shift)
                else:
                    result = self.unicode_decrypt(text, shift)
                    
            elif algorithm == "Base64编码":
                if mode == "加密":
                    result = self.base64_encrypt(text)
                else:
                    result = self.base64_decrypt(text)
                    
            elif algorithm == "凯撒密码":
                try:
                    shift = int(self.shift_var.get())
                except ValueError:
                    self.show_status("偏移量必须为整数", "error")
                    return
                    
                if mode == "加密":
                    result = self.caesar_encrypt(text, shift)
                else:
                    result = self.caesar_decrypt(text, shift)
                    
            elif algorithm == "异或加密":
                key = self.key_var.get()
                if not key:
                    self.show_status("请输入密钥", "error")
                    return
                    
                if mode == "加密":
                    result = self.xor_encrypt(text, key)
                else:
                    result = self.xor_decrypt(text, key)
            
            self.show_result(result)
            self.show_status(f"{mode}完成", "success")
            
        except ValueError as e:
            self.show_status(str(e), "error")
        except Exception as e:
            self.show_status(f"处理错误: {str(e)}", "error")

    def show_result(self, text):
        """显示结果"""
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
        self.output_text.config(state="disabled")

    def clear_text(self):
        """清空输入和输出"""
        self.input_text.delete("1.0", "end")
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.config(state="disabled")
        self.show_status("已清空", "info")

    def save_result(self):
        """保存结果到文件"""
        content = self.output_text.get("1.0", "end").strip()
        if not content:
            self.show_status("没有可保存的内容", "error")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.show_status(f"文件已保存: {os.path.basename(file_path)}", "success")
            except Exception as e:
                self.show_status(f"保存失败: {str(e)}", "error")

    def show_status(self, message, status_type="info"):
        """显示状态信息"""
        if status_type == "error":
            color = self.colors["error"]
        elif status_type == "success":
            color = self.colors["success"]
        else:
            color = self.colors["text"]
            
        self.status_label.config(text=message, foreground=color)


if __name__ == "__main__":
    root = tk.Tk()
    app = ModernCryptoApp(root)
    root.mainloop()

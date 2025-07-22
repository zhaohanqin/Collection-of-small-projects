import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class EncryptApp:
    """
    文本加密器应用程序类，用于创建一个图形用户界面 (GUI) 应用程序，
    实现文本加密、结果展示和保存功能。
    """
    def __init__(self, master):
        """
        初始化 EncryptApp 类的实例。

        :param master: tkinter 根窗口对象，作为应用程序的主窗口。
        """
        self.master = master  # 保存主窗口对象
        master.title("文本加密器 v2.0")  # 设置主窗口的标题
        master.geometry("680x420")  # 设置主窗口的初始大小

        # 样式配置
        self.style = ttk.Style()  # 创建 ttk 样式对象
        # 配置按钮样式，设置字体为微软雅黑 12 号，内边距为 5
        self.style.configure('TButton', font=('Microsoft YaHei', 12), padding=5)
        # 配置标签样式，设置字体为微软雅黑 12 号
        self.style.configure('TLabel', font=('Microsoft YaHei', 12))
        # 配置标签框架样式，设置字体为微软雅黑 14 号加粗
        self.style.configure('TLabelframe', font=('Microsoft YaHei', 14, 'bold'))

        self.create_widgets()  # 调用创建界面组件的方法

    def create_widgets(self):
        """
        创建并布局应用程序的所有 GUI 组件。
        """
        main_frame = ttk.Frame(self.master)  # 创建主框架
        # 主框架填充整个窗口，可扩展，设置外边距
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 输入区
        input_frame = ttk.LabelFrame(main_frame, text="待加密内容")  # 创建输入区域的标签框架
        input_frame.pack(fill="x", pady=10)  # 输入区域框架水平填充，设置垂直外边距
        # 创建文本输入框，设置高度、换行模式和字体
        self.input_text = tk.Text(input_frame, height=6, wrap="word", font=('Microsoft YaHei', 12))
        # 文本输入框水平填充，设置内边距
        self.input_text.pack(fill="x", padx=10, pady=10)

        # 偏移量设置
        shift_frame = ttk.Frame(main_frame)  # 创建偏移量设置框架
        shift_frame.pack(fill="x", pady=10)  # 偏移量设置框架水平填充，设置垂直外边距
        # 创建标签，提示用户输入加密强度
        ttk.Label(shift_frame, text="加密强度 (1-9):").pack(side="left")
        # 创建输入框，用于用户输入加密强度，设置宽度和字体
        self.shift_entry = ttk.Entry(shift_frame, width=5, font=('Microsoft YaHei', 12))
        self.shift_entry.pack(side="left", padx=5)  # 输入框靠左布局，设置水平外边距
        self.shift_entry.insert(0, "3")  # 在输入框中默认插入 3

        # 操作按钮
        btn_frame = ttk.Frame(main_frame)  # 创建按钮框架
        btn_frame.pack(fill="x", pady=15)  # 按钮框架水平填充，设置垂直外边距
        # 创建“开始加密”按钮，点击时调用 process_text 方法
        ttk.Button(btn_frame, text="开始加密", command=self.process_text).pack(side="left", padx=5)
        # 创建“保存结果”按钮，点击时调用 save_result 方法
        ttk.Button(btn_frame, text="保存结果", command=self.save_result).pack(side="right", padx=5)

        # 结果展示
        output_frame = ttk.LabelFrame(main_frame, text="加密结果")  # 创建结果展示的标签框架
        output_frame.pack(fill="both", expand=True)  # 结果展示框架填充整个区域，可扩展
        # 创建文本展示框，设置高度、换行模式，初始状态为禁用
        self.output_text = tk.Text(output_frame, height=6, wrap="word", state="disabled")
        # 文本展示框填充整个区域，可扩展，设置内边距
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)

    @staticmethod
    def encrypt(text: str, shift: int = 3) -> str:
        """
        对输入的文本进行简单的字符偏移加密。

        该方法通过将输入文本中每个字符的 Unicode 码点加上指定的偏移量，
        从而实现对文本的加密。

        :param text: 待加密的文本，字符串类型。
        :param shift: 字符偏移量，整数类型，默认值为 3。
        :return: 加密后的文本，字符串类型。
        """
        # 使用列表推导式遍历输入文本中的每个字符，将其 Unicode 码点加上偏移量后转换回字符，
        # 最后使用空字符串将这些字符拼接成一个字符串并返回
        return ''.join([chr(ord(c) + shift) for c in text])

    def process_text(self):
        """
        处理用户输入的文本，进行加密操作并显示加密结果。
        若输入的加密强度不符合要求或出现类型转换错误，会弹出错误提示框。
        """
        try:
            # 从文本输入框中获取用户输入的文本，并去除首尾空白字符
            text = self.input_text.get("1.0", "end").strip()
            # 将用户输入的加密强度转换为整数类型
            shift = int(self.shift_entry.get())
            # 检查加密强度是否在 1 到 9 的有效范围内
            if not 1 <= shift <= 9:
                # 若不在有效范围内，抛出 ValueError 异常
                raise ValueError("加密强度需在1-9之间")
            # 调用 encrypt 方法对文本进行加密
            result = self.encrypt(text, shift)
            # 调用 show_result 方法显示加密后的结果
            self.show_result(result)
        except ValueError as e:
            # 捕获 ValueError 异常，并弹出错误提示框显示错误信息
            messagebox.showerror("错误", str(e))

    def show_result(self, text):
        """
        在结果展示区域显示加密后的文本。

        :param text: 要显示的加密后的文本，字符串类型。
        """
        # 将文本展示框的状态设置为可编辑，以便进行内容操作
        self.output_text.config(state="normal")
        # 删除文本展示框中现有的所有内容
        self.output_text.delete("1.0", "end")
        # 在文本展示框的起始位置插入加密后的文本
        self.output_text.insert("1.0", text)
        # 将文本展示框的状态设置为禁用，防止用户编辑其中的内容
        self.output_text.config(state="disabled")

    def save_result(self):
        content = self.output_text.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("警告", "没有可保存的内容")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("成功", "文件保存成功！")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EncryptApp(root)
    root.mainloop()

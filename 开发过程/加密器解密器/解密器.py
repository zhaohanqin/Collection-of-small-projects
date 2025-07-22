import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class DecryptApp:
    def __init__(self, master):
        self.master = master
        master.title("🔓 文件解密器 v2.0 🔓")
        master.geometry("680x420")

        # 样式配置
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Microsoft YaHei', 12), padding=5)
        self.style.configure('TLabel', font=('Microsoft YaHei', 12))
        self.style.configure('TLabelframe', font=('Microsoft YaHei', 14, 'bold'))

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.master)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 输入区
        input_frame = ttk.LabelFrame(main_frame, text="待解密内容")
        input_frame.pack(fill="x", pady=10)
        self.input_text = tk.Text(input_frame, height=6, wrap="word", font=('Microsoft YaHei', 12))
        self.input_text.pack(fill="x", padx=10, pady=10)

        # 偏移量设置
        shift_frame = ttk.Frame(main_frame)
        shift_frame.pack(fill="x", pady=10)
        ttk.Label(shift_frame, text="解密强度 (1-9):").pack(side="left")
        self.shift_entry = ttk.Entry(shift_frame, width=5, font=('Microsoft YaHei', 12))
        self.shift_entry.pack(side="left", padx=5)
        self.shift_entry.insert(0, "3")

        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=15)
        ttk.Button(btn_frame, text="开始解密", command=self.process_text).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="保存结果", command=self.save_result).pack(side="right", padx=5)

        # 结果展示
        output_frame = ttk.LabelFrame(main_frame, text="解密结果")
        output_frame.pack(fill="both", expand=True)
        self.output_text = tk.Text(output_frame, height=6, wrap="word", state="disabled")
        self.output_text.pack(fill="both", expand=True, padx=10, pady=10)

    @staticmethod
    def decrypt(text: str, shift: int = 3) -> str:
        return ''.join([chr(ord(c) - shift) for c in text])

    def process_text(self):
        try:
            text = self.input_text.get("1.0", "end").strip()
            shift = int(self.shift_entry.get())
            if not 1 <= shift <= 9:
                raise ValueError("解密强度需在1-9之间")
            result = self.decrypt(text, shift)
            self.show_result(result)
        except ValueError as e:
            messagebox.showerror("错误", str(e))

    # show_result 和 save_result 方法与加密器相同
    def show_result(self, text):
        self.output_text.config(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", text)
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
    app = DecryptApp(root)
    root.mainloop()
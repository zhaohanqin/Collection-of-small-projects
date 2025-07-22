# SimpleSheet2Chiptune - main_audio_only.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import easyocr
import os
import re
import logging
from pydub import AudioSegment
from pydub.generators import Square, Sine, Triangle, Sawtooth
from pydub.playback import play as pydub_play  # For playing audio
import threading
import sys
import subprocess  # For opening folder
import json
from datetime import datetime
import cv2
import numpy as np

# --- Configuration ---
OUTPUT_DIR = "output"
DEFAULT_BPM = 120  # Beats per minute
BASE_OCTAVE = 4  # C4, D4, etc. (C4 = MIDI 60)
LOG_DIR = "logs"

# 设置日志
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SimpleSheet2Chiptune")

# 保存配置
def save_config(config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# 加载配置
def load_config():
    default_config = {
        "bpm": DEFAULT_BPM,
        "volume": -18,
        "waveform": "square",
        "octave": BASE_OCTAVE
    }
    try:
        if os.path.exists("config.json"):
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
    return default_config

# --- 1. GUI Module ---
class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("简谱转8位音乐 (v2.0 改进版)")
        self.root.geometry("850x800")  # 增加窗口大小

        self.image_path = None
        self.original_image = None # 存储原始PIL图像
        self.sheet_music_text = ""
        self.parsed_notes = []
        self.generated_audio_path = None
        self.processed_image_path = None  # 存储预处理后的图像路径
        
        # 加载配置
        self.config = load_config()
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建左右分栏
        self.left_frame = ttk.Frame(self.main_frame, padding="5")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = ttk.Frame(self.main_frame, padding="5")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Image Preview Frame
        self.preview_frame = tk.LabelFrame(self.left_frame, text="图片预览", padx=10, pady=10)
        self.preview_frame.pack(padx=10, pady=10, fill="x")
        self.image_label = tk.Label(self.preview_frame, text="未选择图片")
        self.image_label.pack()

        # 图像预处理控制框架
        self.image_process_frame = tk.LabelFrame(self.left_frame, text="图像预处理", padx=10, pady=10)
        self.image_process_frame.pack(padx=10, pady=5, fill="x")
        
        # 对比度调整
        self.contrast_frame = ttk.Frame(self.image_process_frame)
        self.contrast_frame.pack(fill="x", pady=2)
        ttk.Label(self.contrast_frame, text="对比度:").pack(side=tk.LEFT)
        self.contrast_var = tk.DoubleVar(value=1.5)
        self.contrast_scale = ttk.Scale(self.contrast_frame, from_=0.5, to=3.0, orient=tk.HORIZONTAL, 
                                       variable=self.contrast_var, command=self.update_contrast_label)
        self.contrast_scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.contrast_label = ttk.Label(self.contrast_frame, text="1.5")
        self.contrast_label.pack(side=tk.LEFT)
        
        # 二值化
        self.binary_frame = ttk.Frame(self.image_process_frame)
        self.binary_frame.pack(fill="x", pady=2)
        self.binary_var = tk.BooleanVar(value=True)
        self.binary_check = ttk.Checkbutton(self.binary_frame, text="启用二值化", variable=self.binary_var)
        self.binary_check.pack(side=tk.LEFT)
        
        self.threshold_frame = ttk.Frame(self.image_process_frame)
        self.threshold_frame.pack(fill="x", pady=2)
        ttk.Label(self.threshold_frame, text="自适应阈值C:").pack(side=tk.LEFT)
        self.threshold_var = tk.IntVar(value=7)
        self.threshold_scale = ttk.Scale(self.threshold_frame, from_=1, to=25, orient=tk.HORIZONTAL, 
                                         variable=self.threshold_var, command=self.update_threshold_label)
        self.threshold_scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.threshold_label = ttk.Label(self.threshold_frame, text="7")
        self.threshold_label.pack(side=tk.LEFT)
        
        # 应用预处理按钮
        self.process_button = ttk.Button(self.image_process_frame, text="应用预处理", 
                                        command=self.apply_image_processing, state=tk.DISABLED)
        self.process_button.pack(pady=5)
        
        self.reset_process_button = ttk.Button(self.image_process_frame, text="重置为原图",
                                              command=self.reset_image_processing, state=tk.DISABLED)
        self.reset_process_button.pack(pady=2)


        # Controls Frame
        self.controls_frame = tk.Frame(self.right_frame, padx=10, pady=10)
        self.controls_frame.pack(fill="x")

        self.upload_button = ttk.Button(self.controls_frame, text="上传简谱图片", command=self.upload_image)
        self.upload_button.pack(pady=5, fill="x")

        self.ocr_button = ttk.Button(self.controls_frame, text="1. OCR识别", command=self.run_ocr,
                                     state=tk.DISABLED)
        self.ocr_button.pack(pady=5, fill="x")

        self.parse_button = ttk.Button(self.controls_frame, text="2. 解析简谱", command=self.run_parse,
                                       state=tk.DISABLED)
        self.parse_button.pack(pady=5, fill="x")

        self.music_button = ttk.Button(self.controls_frame, text="3. 生成8位音频",
                                       command=self.run_generate_audio, state=tk.DISABLED)
        self.music_button.pack(pady=5, fill="x")

        self.play_audio_button = ttk.Button(self.controls_frame, text="播放生成的音频", command=self.play_audio,
                                            state=tk.DISABLED)
        self.play_audio_button.pack(pady=5, fill="x")
        
        # 参数设置框架
        self.settings_frame = tk.LabelFrame(self.right_frame, text="参数设置", padx=10, pady=10)
        self.settings_frame.pack(padx=10, pady=10, fill="x")
        
        # BPM设置
        self.bpm_frame = ttk.Frame(self.settings_frame)
        self.bpm_frame.pack(fill="x", pady=5)
        ttk.Label(self.bpm_frame, text="BPM:").pack(side=tk.LEFT)
        self.bpm_var = tk.IntVar(value=self.config["bpm"])
        self.bpm_scale = ttk.Scale(self.bpm_frame, from_=60, to=240, orient=tk.HORIZONTAL, 
                                  variable=self.bpm_var, command=self.update_bpm)
        self.bpm_scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.bpm_label = ttk.Label(self.bpm_frame, text=str(self.bpm_var.get()))
        self.bpm_label.pack(side=tk.LEFT)
        
        # 音量设置
        self.volume_frame = ttk.Frame(self.settings_frame)
        self.volume_frame.pack(fill="x", pady=5)
        ttk.Label(self.volume_frame, text="音量:").pack(side=tk.LEFT)
        self.volume_var = tk.IntVar(value=self.config["volume"])
        self.volume_scale = ttk.Scale(self.volume_frame, from_=-40, to=0, orient=tk.HORIZONTAL, 
                                     variable=self.volume_var, command=self.update_volume)
        self.volume_scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.volume_label = ttk.Label(self.volume_frame, text=str(self.volume_var.get()))
        self.volume_label.pack(side=tk.LEFT)
        
        # 音色选择
        self.waveform_frame = ttk.Frame(self.settings_frame)
        self.waveform_frame.pack(fill="x", pady=5)
        ttk.Label(self.waveform_frame, text="音色:").pack(side=tk.LEFT)
        self.waveform_var = tk.StringVar(value=self.config["waveform"])
        self.waveform_combo = ttk.Combobox(self.waveform_frame, textvariable=self.waveform_var, 
                                          values=["square", "sine", "triangle", "sawtooth"],
                                          state="readonly")
        self.waveform_combo.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.waveform_combo.bind("<<ComboboxSelected>>", self.update_waveform)
        
        # 八度设置
        self.octave_frame = ttk.Frame(self.settings_frame)
        self.octave_frame.pack(fill="x", pady=5)
        ttk.Label(self.octave_frame, text="八度:").pack(side=tk.LEFT)
        self.octave_var = tk.IntVar(value=self.config["octave"])
        self.octave_scale = ttk.Scale(self.octave_frame, from_=1, to=7, orient=tk.HORIZONTAL, 
                                     variable=self.octave_var, command=self.update_octave)
        self.octave_scale.pack(side=tk.LEFT, fill="x", expand=True, padx=5)
        self.octave_label = ttk.Label(self.octave_frame, text=str(self.octave_var.get()))
        self.octave_label.pack(side=tk.LEFT)
        
        # 保存设置按钮
        self.save_settings_button = ttk.Button(self.settings_frame, text="保存设置", command=self.save_settings)
        self.save_settings_button.pack(pady=10)

        # Progress and Log
        self.progress = ttk.Progressbar(self.left_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=5, fill="x")

        self.log_label = tk.Label(self.left_frame, text="状态: 空闲", wraplength=380)
        self.log_label.pack(pady=5)

        self.ocr_output_label = tk.Label(self.right_frame, text="OCR输出 (可编辑):")
        self.ocr_output_label.pack(pady=(5, 0))
        self.ocr_output_text = scrolledtext.ScrolledText(self.right_frame, height=10, wrap=tk.WORD)
        self.ocr_output_text.pack(pady=5, fill="both", expand=True)
        self.ocr_output_text.insert(tk.END, "OCR输出将显示在这里...")
        
        # 日志输出
        self.log_output_label = tk.Label(self.right_frame, text="日志输出:")
        self.log_output_label.pack(pady=(5, 0))
        self.log_output_text = scrolledtext.ScrolledText(self.right_frame, height=6, wrap=tk.WORD)
        self.log_output_text.pack(pady=5, fill="both")
        self.log_output_text.insert(tk.END, "日志输出将显示在这里...")
        self.log_output_text.config(state=tk.DISABLED)
        
        # 设置日志处理器
        self.log_handler = LogTextHandler(self.log_output_text)
        logger.addHandler(self.log_handler)

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        logger.info("应用程序已启动")

    def update_bpm(self, value): self.bpm_label.config(text=str(int(float(value))))
    def update_volume(self, value): self.volume_label.config(text=str(int(float(value))))
    def update_waveform(self, event=None): pass
    def update_octave(self, value): self.octave_label.config(text=str(int(float(value))))
    def update_contrast_label(self, value): self.contrast_label.config(text=f"{float(value):.1f}")
    def update_threshold_label(self, value): self.threshold_label.config(text=f"{int(float(value))}")

    def save_settings(self):
        self.config = { "bpm": self.bpm_var.get(), "volume": self.volume_var.get(), "waveform": self.waveform_var.get(), "octave": self.octave_var.get() }
        save_config(self.config)
        logger.info(f"设置已保存: {self.config}")
        messagebox.showinfo("成功", "设置已保存")

    def log_message(self, message):
        self.log_label.config(text=f"状态: {message}")
        logger.info(message)
        self.root.update_idletasks()

    def update_progress(self, value):
        self.progress['value'] = value
        self.root.update_idletasks()

    def reset_state_for_new_image(self):
        self.sheet_music_text = ""
        self.parsed_notes = []
        self.generated_audio_path = None
        self.processed_image_path = None
        self.ocr_button.config(state=tk.NORMAL)
        self.parse_button.config(state=tk.DISABLED)
        self.music_button.config(state=tk.DISABLED)
        self.play_audio_button.config(state=tk.DISABLED)
        self.process_button.config(state=tk.NORMAL)
        self.reset_process_button.config(state=tk.NORMAL)
        self.ocr_output_text.delete(1.0, tk.END)
        self.ocr_output_text.insert(tk.END, "准备进行OCR识别。")
        self.update_progress(0)
        self.contrast_var.set(1.5)
        self.threshold_var.set(7)
        self.binary_var.set(True)
        self.update_contrast_label(1.5)
        self.update_threshold_label(7)

    def upload_image(self):
        path = filedialog.askopenfilename(title="选择简谱图片", filetypes=(("Image Files", "*.png;*.jpg;*.jpeg"), ("所有文件", "*.*")))
        if path:
            try:
                self.image_path = path
                self.original_image = Image.open(self.image_path)
                self.display_image(self.original_image)
                self.log_message(f"图片已加载: {os.path.basename(self.image_path)}")
                self.reset_state_for_new_image()
                # 默认应用一次预处理
                self.apply_image_processing()
            except Exception as e:
                messagebox.showerror("错误", f"加载图片失败: {e}")
                self.log_message(f"加载图片错误: {e}")
                logger.error(f"加载图片错误: {e}", exc_info=True)
                self.image_path = None
        else:
            self.log_message("已取消图片选择。")

    def display_image(self, pil_image):
        img_copy = pil_image.copy()
        img_copy.thumbnail((350, 350))
        photo = ImageTk.PhotoImage(img_copy)
        self.image_label.config(image=photo, text="")
        self.image_label.image = photo

    def apply_image_processing(self):
        if not self.original_image: return
        try:
            # 1. 使用PIL增强对比度
            img_pil = self.original_image.copy()
            enhancer = ImageEnhance.Contrast(img_pil)
            img_pil = enhancer.enhance(self.contrast_var.get())

            # 2. 转换为OpenCV格式进行高级处理
            img_cv = np.array(img_pil.convert('L')) # 转为灰度图

            # 3. 应用二值化
            if self.binary_var.get():
                # 高斯模糊降噪
                img_cv = cv2.GaussianBlur(img_cv, (5, 5), 0)
                
                # 自适应阈值，对于光照不均的图片效果更好
                # blockSize必须是奇数, C是微调值
                blockSize = 11 
                C = self.threshold_var.get()
                img_cv = cv2.adaptiveThreshold(
                    img_cv, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, blockSize, C
                )

            # 4. 转回PIL格式用于显示和保存
            processed_pil_img = Image.fromarray(img_cv)
            self.display_image(processed_pil_img)
            
            # 5. 保存处理后的图像以供OCR使用
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            
            # 确保文件名安全
            base_name = os.path.basename(self.image_path)
            safe_base_name = "".join([c if c.isalnum() else "_" for c in base_name])
            self.processed_image_path = os.path.join(temp_dir, f"processed_{safe_base_name}.png")
            processed_pil_img.save(self.processed_image_path, "PNG")
            
            self.log_message("图像预处理完成。")
            self.ocr_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("预处理错误", f"图像预处理失败: {e}")
            self.log_message(f"图像预处理错误: {e}")
            logger.error(f"图像预处理错误: {e}", exc_info=True)

    def reset_image_processing(self):
        if self.original_image:
            self.display_image(self.original_image)
            self.processed_image_path = self.image_path # OCR将使用原图
            self.log_message("图像重置为原始状态。")

    def run_ocr(self):
        image_to_process = self.processed_image_path if self.processed_image_path else self.image_path
        if not image_to_process:
            messagebox.showwarning("警告", "请先上传图片。")
            return

        self.log_message("开始OCR识别... (可能需要一点时间)")
        self.ocr_button.config(state=tk.DISABLED)
        self.update_progress(10)
        threading.Thread(target=self._ocr_thread_task, args=(image_to_process,), daemon=True).start()

    def _ocr_thread_task(self, image_path):
        try:
            ocr_module = SheetOCR()
            self.sheet_music_text = ocr_module.recognize_sheet(image_path)
            self.update_progress(80)
            self.log_message("OCR识别完成。")
            self.ocr_output_text.delete(1.0, tk.END)
            self.ocr_output_text.insert(tk.END, self.sheet_music_text if self.sheet_music_text else "未识别到任何有效字符。请调整预处理参数或手动输入。")

            if self.sheet_music_text:
                self.parse_button.config(state=tk.NORMAL)
            else:
                messagebox.showwarning("OCR结果", "OCR未识别到任何相关字符。请尝试调整预处理参数（如二值化阈值），或在右侧文本框中手动输入简谱。")
                self.parse_button.config(state=tk.NORMAL) # 允许用户手动输入后进行解析
        except Exception as e:
            messagebox.showerror("OCR错误", f"OCR识别过程中发生错误: {e}")
            self.log_message(f"OCR错误: {e}")
            logger.error(f"OCR错误: {e}", exc_info=True)
        finally:
            self.ocr_button.config(state=tk.NORMAL)
            self.update_progress(0)

    def run_parse(self):
        # 从文本框获取最新文本，允许用户修改
        self.sheet_music_text = self.ocr_output_text.get(1.0, tk.END).strip()
        if not self.sheet_music_text:
            messagebox.showwarning("警告", "简谱文本为空，请输入或通过OCR识别。")
            return

        self.log_message("解析简谱...")
        self.parse_button.config(state=tk.DISABLED)
        self.update_progress(10)
        try:
            parser_module = NotationParser()
            self.parsed_notes = parser_module.parse_simple_notation(
                self.sheet_music_text, 
                bpm=self.bpm_var.get(),
                base_octave=self.octave_var.get()
            )
            self.update_progress(80)
            if not self.parsed_notes:
                messagebox.showwarning("解析结果", "无法从文本中解析出任何音符。请检查简谱格式。")
                self.log_message("解析失败或未产生任何音符。")
                self.parse_button.config(state=tk.NORMAL)
                return

            self.log_message(f"解析完成。找到 {len(self.parsed_notes)} 个音乐事件。")
            self.music_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("解析错误", f"解析过程中发生错误: {e}")
            self.log_message(f"解析错误: {e}")
            logger.error(f"解析错误: {e}", exc_info=True)
        finally:
            self.parse_button.config(state=tk.NORMAL)
            self.update_progress(0)

    def run_generate_audio(self):
        if not self.parsed_notes:
            messagebox.showwarning("警告", "请先解析简谱。")
            return

        self.log_message("生成8位音频...")
        self.music_button.config(state=tk.DISABLED)
        self.update_progress(10)

        base_filename = os.path.splitext(os.path.basename(self.image_path))[0] if self.image_path else "chiptune_output"
        self.generated_audio_path = os.path.join(OUTPUT_DIR, f"{base_filename}_chiptune.wav")

        threading.Thread(target=self._audio_thread_task, daemon=True).start()

    def _audio_thread_task(self):
        try:
            chiptune_module = ChiptuneGenerator()
            audio_segment = chiptune_module.generate_chiptune_segment(
                self.parsed_notes, 
                waveform=self.waveform_var.get(),
                volume=self.volume_var.get()
            )
            self.update_progress(70)
            audio_segment.export(self.generated_audio_path, format="wav")
            self.log_message(f"音频已生成: {self.generated_audio_path}")
            self.play_audio_button.config(state=tk.NORMAL)
            messagebox.showinfo("成功", f"音频已保存至:\n{self.generated_audio_path}")
            if messagebox.askyesno("打开文件夹", "是否打开输出文件夹?"):
                self._open_output_folder()

        except Exception as e:
            messagebox.showerror("音频生成错误", f"发生错误: {e}")
            self.log_message(f"音频生成错误: {e}")
            logger.error(f"音频生成错误: {e}", exc_info=True)
            self.generated_audio_path = None
        finally:
            self.music_button.config(state=tk.NORMAL)
            self.update_progress(0)

    def play_audio(self):
        if self.generated_audio_path and os.path.exists(self.generated_audio_path):
            self.log_message(f"正在播放 {self.generated_audio_path}...")
            self.play_audio_button.config(state=tk.DISABLED)
            try:
                audio_segment = AudioSegment.from_wav(self.generated_audio_path)
                threading.Thread(target=self._play_audio_thread, args=(audio_segment,), daemon=True).start()
            except Exception as e:
                messagebox.showerror("播放错误", f"无法播放音频: {e}\n请确保已安装'simpleaudio'或'ffplay'/'avplay'在您的PATH中。")
                self.log_message(f"播放错误: {e}")
                logger.error(f"播放错误: {e}", exc_info=True)
                self.play_audio_button.config(state=tk.NORMAL)
        else:
            messagebox.showwarning("无音频", "未生成音频文件或路径无效。")

    def _play_audio_thread(self, audio_segment):
        try:
            pydub_play(audio_segment)
            self.log_message("播放完成。")
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("播放错误", f"无法播放音频: {e}\n请确保已安装'simpleaudio'或'ffplay'/'avplay'(来自ffmpeg)在您的PATH中。"))
            self.log_message(f"播放执行错误: {e}")
            logger.error(f"播放执行错误: {e}", exc_info=True)
        finally:
            self.root.after(0, self.play_audio_button.config, {'state': tk.NORMAL})

    def _open_output_folder(self):
        abs_output_dir = os.path.abspath(OUTPUT_DIR)
        try:
            if sys.platform == "win32": os.startfile(abs_output_dir)
            elif sys.platform == "darwin": subprocess.Popen(["open", abs_output_dir])
            else: subprocess.Popen(["xdg-open", abs_output_dir])
        except Exception as e:
            messagebox.showerror("错误", f"无法打开输出文件夹: {e}\n路径: {abs_output_dir}")
            self.log_message(f"打开输出文件夹错误: {e}")
            logger.error(f"打开输出文件夹错误: {e}", exc_info=True)


# 自定义日志处理器，将日志输出到文本框
class LogTextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        
    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)
        self.text_widget.after(0, append)


# --- 2.简谱OCR识别模块 (IMPROVED) ---
class SheetOCR:
    def __init__(self, languages=['ch_sim', 'en']):
        try:
            self.reader = easyocr.Reader(languages, gpu=False)
            logger.info("EasyOCR初始化成功")
        except Exception as e:
            messagebox.showerror("EasyOCR初始化错误", f"EasyOCR初始化失败: {e}\n请确保正确安装了EasyOCR及其依赖项(如PyTorch)。")
            logger.error(f"EasyOCR初始化错误: {e}", exc_info=True)
            raise RuntimeError(f"EasyOCR初始化错误: {e}") from e

    def recognize_sheet(self, image_path):
        """
        Recognizes sheet music from a pre-processed image.
        Relies on external pre-processing for best results.
        """
        try:
            logger.info(f"使用预处理后的图片进行OCR: {image_path}")
            
            # 使用更宽松的OCR参数
            # allowlist 允许更多可能的字符，后续再清理
            result = self.reader.readtext(
                image_path, 
                detail=0, 
                paragraph=False, # 识别单个字符或短语
                allowlist='0123456789.-|OIli+', # 允许数字、点、横杠、竖线、易混淆字符及高音符号
                batch_size=8,
            )
            logger.info(f"原始OCR识别结果: {result}")
        except Exception as e:
            logger.error(f"EasyOCR readtext错误: {e}", exc_info=True)
            return ""

        if not result:
            logger.warning("OCR未识别到任何文本")
            return ""

        # 文本后处理 (关键步骤)
        full_text = " ".join(result)
        
        # 1. 智能替换常见错误
        # 将易混淆的字符替换为正确的简谱符号
        full_text = full_text.replace('l', '1').replace('I', '1').replace('|', ' ')
        full_text = full_text.replace('O', '0').replace('o', '0')
        
        # 2. 放宽过滤规则，保留所有数字和关键符号，交给解析器处理
        # 保留数字, 点, 横杠, 加减号(高低音), 和空格
        filtered_text = re.sub(r'[^0-9.+\-\s]', '', full_text)
        
        # 3. 清理多余空格
        cleaned_text = re.sub(r'\s+', ' ', filtered_text).strip()
        
        logger.info(f"清理后的OCR文本: {cleaned_text}")
        return cleaned_text


# --- 3. 简谱转音符（数据结构） (IMPROVED) ---
class NotationParser:
    def __init__(self):
        self.note_map_c_major = {
            '1': 0, '2': 2, '3': 4, '4': 5, '5': 7, '6': 9, '7': 11,
        }
        self.midi_base_c4 = 60  # C4 as reference for octave calculation
        logger.info("简谱解析器初始化完成")

    def parse_simple_notation(self, text_notation, bpm=120, base_octave=4):
        parsed_events = []
        
        # 预处理输入文本
        processed_text = text_notation.replace('|', ' ').replace('O', '0').replace('o', '0')
        tokens = processed_text.split()
        
        logger.info(f"开始解析简谱 (BPM: {bpm}, 基准八度: {base_octave}): {tokens}")

        quarter_note_duration_sec = 60.0 / bpm

        for original_token in tokens:
            if not original_token: continue
            
            token = original_token
            event_type = None
            pitch = None
            duration_beats = 0.0

            # 1. 解析八度修饰符 (前缀)
            octave_shift = 0
            while token.startswith('+'):
                octave_shift += 1
                token = token[1:]
            # 确保'-'后面是数字，以区分低音符号和独立的延长线
            while token.startswith('-') and len(token) > 1 and token[1] in '12345670': 
                octave_shift -= 1
                token = token[1:]

            # 2. 解析音符和休止符
            if token.startswith('0'):
                event_type = 'rest'
                duration_beats = 1.0 # '0' is a quarter rest
                token = token[1:] # consume '0'
            elif token and token[0] in '1234567':
                event_type = 'note'
                note_char = token[0]
                pitch_offset = self.note_map_c_major.get(note_char)
                if pitch_offset is not None:
                    pitch = self.midi_base_c4 + (12 * (base_octave - 4 + octave_shift)) + pitch_offset
                
                duration_beats = 1.0 # base is a quarter note
                token = token[1:] # consume note number
            
            # 3. 如果识别到事件，解析时长修饰符 (后缀)
            if event_type:
                # 延长线
                dash_count = token.count('-')
                duration_beats += dash_count
                
                # 附点
                dot_count = token.count('.')
                duration_multiplier = 1.0
                for i in range(dot_count):
                    duration_multiplier += 0.5 / (2**i)
                duration_beats *= duration_multiplier
                
                duration_ms = (duration_beats * quarter_note_duration_sec) * 1000
                parsed_events.append({
                    'type': event_type,
                    'pitch': pitch,
                    'duration_ms': duration_ms,
                    'original_char': original_token
                })
                logger.debug(f"解析到事件: '{original_token}', 类型: {event_type}, 音高: {pitch}, 时长: {duration_beats}拍")
            elif original_token: # 只有在原始token不为空时才警告
                logger.warning(f"解析过程中跳过无法识别的标记 '{original_token}'。")

        logger.info(f"简谱解析完成，共解析出 {len(parsed_events)} 个音乐事件")
        return parsed_events


# --- 4. 生成 8bit 风格音乐 ---
class ChiptuneGenerator:
    def midi_to_freq(self, midi_note):
        if midi_note is None: return 0
        return 440 * (2 ** ((midi_note - 69) / 12))

    def generate_chiptune_segment(self, parsed_notes, waveform="square", volume=-18):
        logger.info(f"开始生成音频，波形: {waveform}, 音量: {volume}")
        song = AudioSegment.empty()
        
        generators = {"square": Square, "sine": Sine, "triangle": Triangle, "sawtooth": Sawtooth}
        generator_class = generators.get(waveform, Square)
        if waveform not in generators:
            logger.warning(f"未知波形类型: {waveform}，使用默认方波")

        staccato_ratio = 0.85  # 音符实际发声时长占比, 留出空隙制造节奏感

        for note_event in parsed_notes:
            duration_ms = int(note_event['duration_ms'])
            if duration_ms <= 0: continue

            if note_event['type'] == 'note' and note_event['pitch'] is not None:
                frequency = self.midi_to_freq(note_event['pitch'])
                
                sound_duration = int(duration_ms * staccato_ratio)
                pause_duration = duration_ms - sound_duration

                if frequency > 0:
                    note_sound = generator_class(frequency).to_audio_segment(duration=sound_duration).apply_gain(volume)
                    # 平滑淡出以避免爆音
                    note_sound = note_sound.fade_out(int(sound_duration * 0.1) + 1)
                    song += note_sound
                
                if pause_duration > 0:
                    song += AudioSegment.silent(duration=pause_duration)
                    
                logger.debug(f"生成音符: 频率={frequency:.2f}Hz, 时长={sound_duration}ms + 停顿={pause_duration}ms")

            elif note_event['type'] == 'rest':
                song += AudioSegment.silent(duration=duration_ms)
                logger.debug(f"生成休止符: 时长={duration_ms}ms")
            
            else:
                logger.warning(f"跳过无效的音符事件: {note_event}")

        logger.info("音频生成完成")
        return song


# --- Main Execution ---
if __name__ == "__main__":
    try:
        # 预检查EasyOCR
        _ = easyocr.Reader(['ch_sim', 'en'], gpu=False, verbose=False)
        del _
        logger.info("EasyOCR预检查成功")
    except Exception as e:
        root_check = tk.Tk()
        root_check.withdraw()
        messagebox.showerror("启动错误", f"无法初始化EasyOCR: {e}\n\n请确保正确安装了EasyOCR及其依赖项(如CPU版PyTorch)。\n应用程序将关闭。")
        logger.critical(f"EasyOCR初始化失败: {e}", exc_info=True)
        sys.exit(1)

    root = tk.Tk()
    app = AppGUI(root)
    logger.info("应用程序GUI已创建")
    root.mainloop()
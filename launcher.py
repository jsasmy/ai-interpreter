import subprocess
import time
import webbrowser
import os
import sys
import tkinter as tk
from tkinter import messagebox
import threading

class AppLauncher:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.root = tk.Tk()
        self.root.title("AI 同声传译助手")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        self.setup_ui()
        
    def setup_ui(self):
        title_label = tk.Label(
            self.root, 
            text="AI 同声传译助手", 
            font=("微软雅黑", 18, "bold")
        )
        title_label.pack(pady=20)
        
        self.status_label = tk.Label(
            self.root, 
            text="点击启动按钮开始运行", 
            font=("微软雅黑", 10)
        )
        self.status_label.pack(pady=10)
        
        self.start_btn = tk.Button(
            self.root,
            text="启动服务",
            font=("微软雅黑", 12),
            width=15,
            height=2,
            command=self.start_services
        )
        self.start_btn.pack(pady=10)
        
        self.stop_btn = tk.Button(
            self.root,
            text="停止服务",
            font=("微软雅黑", 12),
            width=15,
            height=2,
            command=self.stop_services,
            state=tk.DISABLED
        )
        self.stop_btn.pack(pady=5)
        
        self.open_btn = tk.Button(
            self.root,
            text="打开浏览器",
            font=("微软雅黑", 10),
            width=12,
            command=self.open_browser,
            state=tk.DISABLED
        )
        self.open_btn.pack(pady=10)
        
    def get_base_path(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))
    
    def start_services(self):
        self.start_btn.config(state=tk.DISABLED)
        self.status_label.config(text="正在启动后端服务...")
        
        threading.Thread(target=self._start_backend, daemon=True).start()
        
    def _start_backend(self):
        try:
            base_path = self.get_base_path()
            backend_path = os.path.join(base_path, "backend")
            
            self.backend_process = subprocess.Popen(
                ["python", "main.py"],
                cwd=backend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            time.sleep(3)
            
            self.root.after(0, self._start_frontend)
            
        except Exception as e:
            self.root.after(0, lambda: self.status_label.config(text=f"后端启动失败: {e}"))
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
    
    def _start_frontend(self):
        self.status_label.config(text="正在启动前端服务...")
        
        try:
            base_path = self.get_base_path()
            frontend_path = os.path.join(base_path, "frontend")
            
            self.frontend_process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            time.sleep(5)
            
            self.status_label.config(text="服务已启动")
            self.stop_btn.config(state=tk.NORMAL)
            self.open_btn.config(state=tk.NORMAL)
            
            self.open_browser()
            
        except Exception as e:
            self.status_label.config(text=f"前端启动失败: {e}")
            self.start_btn.config(state=tk.NORMAL)
    
    def stop_services(self):
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process = None
            
        if self.frontend_process:
            self.frontend_process.terminate()
            self.frontend_process = None
            
        self.status_label.config(text="服务已停止")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)
    
    def open_browser(self):
        webbrowser.open("http://localhost:3001")
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
    
    def on_close(self):
        if messagebox.askokcancel("退出", "确定要退出并停止所有服务吗？"):
            self.stop_services()
            self.root.destroy()

if __name__ == "__main__":
    app = AppLauncher()
    app.run()

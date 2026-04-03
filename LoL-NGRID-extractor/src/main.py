import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ctypes
import os
import wad_extractor as wad_extractor

# 윈도우의 고해상도(DPI) 인식을 활성화 (글자를 선명하게 만듦)
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

class NgridApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ngrid Extractor")
        
        # 중앙 정렬 로직
        width, height = 1000, 800
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw // 2) - (width // 2)
        y = (sh // 2) - (height // 2)
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.resizable(False, False)
        
        self.global_wad_path = ""
        self.nav_data = wad_extractor.load_data()
        
        # UI 초기화 (첫 화면: 설정)
        self.show_setup_page()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_setup_page(self):
        """경로 설정 페이지"""
        self.clear_window()
        
        tk.Label(self.root, text="League of Legends 경로 설정", font=("Malgun Gothic", 16, "bold")).pack(pady=30)
        tk.Label(self.root, text="리그 오브 레전드 폴더를 선택해 주세요.", fg="gray").pack()

        # 경로 입력 프레임
        path_frame = tk.Frame(self.root)
        path_frame.pack(pady=30, padx=20, fill="x")

        # 기본 경로 표시 변수
        self.path_var = tk.StringVar(value=wad_extractor.get_default_lol_path())
        
        self.path_entry = tk.Entry(path_frame, textvariable=self.path_var, font=("Consolas", 10))
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=5)

        # 수동 선택 버튼
        btn_browse = ttk.Button(path_frame, text="폴더 선택...", style="TButton", command=self.browse_folder)
        btn_browse.pack(side="right")

        # 안내 문구
        self.status_label = tk.Label(self.root, text="Riot Games/League of Legends 폴더를 선택하세요.", fg="#3498db")
        self.status_label.pack()

        # 하단 버튼바
        bottom_bar = tk.Frame(self.root)
        bottom_bar.pack(side="bottom", fill="x", pady=30)

        btn_next = tk.Button(bottom_bar, text="다음 (Next) >", width=15, height=2, 
                             bg="#2ecc71", fg="white", font=("bold"), command=self.validate_and_next)
        btn_next.pack(pady=10)

    def browse_folder(self):
        """직접 폴더를 선택하는 기능"""
        selected = filedialog.askdirectory(title="League of Legends 폴더 선택")
        if selected:
            self.path_var.set(selected)

    def validate_and_next(self):
        """경로가 유효한지 확인 후 다음 페이지로"""
        base_dir = self.path_var.get()
        full_path = wad_extractor.get_full_wad_path(base_dir)
        
        if os.path.exists(full_path):
            self.global_wad_path = full_path
            self.show_extraction_page()
        else:
            # 파일을 못 찾은 경우 수동 파일 선택 권유
            if messagebox.askyesno("확인 실패", "해당 경로에서 리그 오브 레전드 파일을 찾을 수 없습니다.\nLeague of Legends 폴더를 선택해주세요"):
                manual_file = filedialog.askdirectory(title="League of Legends 폴더 선택")
                if manual_file:
                    full_path = wad_extractor.get_full_wad_path(manual_file)
                    self.global_wad_path = full_path
                    self.show_extraction_page()

    def show_extraction_page(self):
        """단계 2: 실제 추출 페이지"""
        self.clear_window()
        self.root.title("Ngrid Extractor")

        # 상단 정보
        info_bar = tk.Frame(self.root, bg="#2c3e50")
        info_bar.pack(fill="x")
        tk.Label(info_bar, text=f"성공적으로 연결됨: {os.path.basename(self.global_wad_path)}", 
                 fg="white", bg="#2c3e50", pady=5).pack()

        tk.Label(self.root, text="추출할 맵 경로를 선택하세요", font=("Malgun Gothic", 14, "bold")).pack(pady=30)

        # 콤보박스
        self.combo = ttk.Combobox(self.root, values=list(self.nav_data.keys()), width=70)
        self.combo.pack(pady=20)
        self.combo.bind("<<ComboboxSelected>>", self.on_extract_trigger)

        # 결과 표시
        self.hash_var = tk.StringVar(value="항목을 선택하세요.")
        tk.Entry(self.root, textvariable=self.hash_var, justify="center", font=("Consolas", 11),
                 bd=0, bg="#f8f9fa", fg="#2980b9").pack(pady=20, fill="x", padx=100)
        
        # 뒤로가기 버튼
        tk.Button(self.root, text="이전으로 (경로 재설정)", command=self.show_setup_page, 
                  relief="flat", fg="gray").pack(side="bottom", pady=20)

    def on_extract_trigger(self, event):
            self.root.config(cursor="watch")
            self.root.update_idletasks() 

            full_path_text = self.combo.get() 
            hash_val = self.nav_data.get(full_path_text)
        
            if hash_val:
                # 1. 추출 시도 (이때 extract_wad는 성공 시 저장된 폴더 경로를 반환하도록 짜야 합니다)
                success, final_output_dir = wad_extractor.extract_wad(hash_val, self.global_wad_path, full_path_text)
                
                self.root.config(cursor="") 
                
                if success:
                    # 2. 파일명 정보 추출 (예: crepe.aimesh_ngrid)
                    file_name = full_path_text.split('/')[-1]
                    folder_name = file_name.split('.')[0] 
                    
                    # 3. [핵심] 컨버터 실행 (드래그 앤 드롭 동작 수행)
                    # 추출된 폴더 경로와 파일명을 넘겨줍니다.
                    convert_success = wad_extractor.run_converter(final_output_dir, file_name)
                    
                    if convert_success:
                        messagebox.showinfo("완료", 
                            f"다운로드/{folder_name}로 추출 및 변환이 완료되었습니다.")
                        # 폴더 바로 열기 (선택 사항)
                        os.startfile(final_output_dir)
                    else:
                        messagebox.showwarning("주의", "추출은 성공했으나 컨버터 실행에 실패했습니다.")
                else:
                    messagebox.showerror("실패", "데이터 추출 중 오류가 발생했습니다.")
            else:
                self.root.config(cursor="")
                messagebox.showwarning("알림", "해시 정보를 찾을 수 없습니다.")
                
if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use('clam')
    app = NgridApp(root)
    root.mainloop()
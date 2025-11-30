import customtkinter as ctk
import socket
import subprocess
import os
from tkinter import filedialog, messagebox

# --- CONFIGURATION ---
VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe" 

class LANStreamerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Appearance Settings (High Contrast/Dark Theme) ---
        ctk.set_appearance_mode("Dark")     # Force Dark Mode
        ctk.set_default_color_theme("dark-blue") # Use dark-blue theme

        self.title("🔥 VLC Stream Hub 🔥")
        self.geometry("700x600") # Slightly larger window
        self.process = None 

        # Layout Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0) 
        self.grid_rowconfigure(1, weight=1) 
        
        # --- TITLE AREA ---
        self.label_title = ctk.CTkLabel(
            self, 
            text="STREAMING CONTROL CONSOLE", 
            font=("Consolas", 32, "bold"),
            text_color="#FFD700" # Gold/Yellow accent
        )
        self.label_title.grid(row=0, column=0, pady=(35, 15))

        # --- TABS (Bigger and bolder) ---
        self.tabview = ctk.CTkTabview(
            self, 
            width=650, 
            corner_radius=20, # More aggressive rounding
            fg_color="#1f2c41" # Slightly lighter background for contrast
        )
        self.tabview.grid(row=1, column=0, padx=30, pady=(10, 25), sticky="nsew")
        
        self.tab_server = self.tabview.add("SERVER MODE 💻")
        self.tab_client = self.tabview.add("CLIENT MODE 🎮")

        # Set specific padding for tab content
        self.tab_server.grid_columnconfigure((0, 1), weight=1)
        self.tab_client.grid_columnconfigure((0, 1), weight=1)


        self.setup_server_ui()
        self.setup_client_ui()
        
        # --- STATUS BAR (Footer) ---
        self.status_label = ctk.CTkLabel(
            self, 
            text="STATUS: OFFLINE", 
            text_color="#AAAAAA", 
            font=("Arial", 16)
        )
        self.status_label.grid(row=2, column=0, pady=(0, 20))
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ================= SERVER UI & LOGIC =================
    def setup_server_ui(self):
        
        # IP Display
        self.local_ip = self.get_local_ip()
        self.lbl_server_ip = ctk.CTkLabel(self.tab_server, 
            text=f"YOUR IP: {self.local_ip}", 
            font=("Consolas", 20, "bold"),
            text_color="#FFD700" # Gold/Yellow accent
        )
        self.lbl_server_ip.grid(row=0, column=0, columnspan=2, pady=(20, 25))

        # File Selection
        self.btn_browse = ctk.CTkButton(self.tab_server, 
            text="SELECT SOURCE FILE", 
            command=self.browse_file,
            fg_color="#3A465A", 
            hover_color="#4F5C75",
            corner_radius=15,
            height=40,
            font=("Arial", 16)
        )
        self.btn_browse.grid(row=1, column=0, columnspan=2, pady=10, padx=30, sticky="ew")
        
        self.lbl_file_path = ctk.CTkLabel(self.tab_server, 
            text="File: No source loaded", 
            text_color="#FFA07A", # Light Salmon
            wraplength=600
        )
        self.lbl_file_path.grid(row=2, column=0, columnspan=2, pady=(5, 25))
        self.selected_file = None

        # Protocol Selection
        self.lbl_proto = ctk.CTkLabel(self.tab_server, text="PROTOCOL:", font=("Arial", 16, "bold"))
        self.lbl_proto.grid(row=3, column=0, sticky="w", padx=(60, 10), pady=(10, 5))
        self.combo_proto = ctk.CTkComboBox(self.tab_server, values=["HTTP", "UDP"], corner_radius=10, height=35)
        self.combo_proto.set("HTTP")
        self.combo_proto.grid(row=3, column=1, sticky="ew", padx=(10, 60), pady=(10, 5))

        # Port Selection
        self.lbl_port = ctk.CTkLabel(self.tab_server, text="PORT:", font=("Arial", 16, "bold"))
        self.lbl_port.grid(row=4, column=0, sticky="w", padx=(60, 10), pady=5)
        self.entry_port = ctk.CTkEntry(self.tab_server, placeholder_text="8000", corner_radius=10, height=35)
        self.entry_port.insert(0, "8000") 
        self.entry_port.grid(row=4, column=1, sticky="ew", padx=(10, 60), pady=5)

        # Start/Stop Buttons
        self.btn_start_server = ctk.CTkButton(self.tab_server, 
            text="START STREAM ▶️", 
            fg_color="#FFD700", # Yellow/Gold
            hover_color="#CCAC00",
            text_color="#000000", # Black text on yellow for maximum contrast
            corner_radius=20, 
            command=self.start_stream,
            height=50,
            font=("Consolas", 18, "bold")
        )
        self.btn_start_server.grid(row=5, column=0, columnspan=2, pady=(40, 15), padx=50, sticky="ew")
        
        self.btn_stop_server = ctk.CTkButton(self.tab_server, 
            text="STOP STREAM 🛑", 
            fg_color="#CC0000", # Deep Red
            hover_color="#990000",
            corner_radius=15, 
            state="disabled", 
            command=self.stop_vlc,
            height=40
        )
        self.btn_stop_server.grid(row=6, column=0, columnspan=2, pady=(0, 20), padx=50, sticky="ew")

    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mp3")])
        if filename:
            self.selected_file = filename
            self.lbl_file_path.configure(text=f"File: {os.path.basename(filename)}", text_color="#32CD32") # Lime Green when loaded

    def start_stream(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a video file first.")
            return

        windows_file_path = os.path.normpath(self.selected_file)
        port = self.entry_port.get()
        protocol = self.combo_proto.get()
        
        if protocol == "HTTP":
            sout_cmd = f'#transcode{{scodec=none}}:duplicate{{dst=http{{mux=mkv,dst=:{port}/}},dst=display}}'
        else:
            sout_cmd = f':duplicate{{dst=udp{{dst=239.0.0.1:{port}}},dst=display}}'

        if not os.path.exists(self.selected_file):
            messagebox.showerror("Error", f"File not found or path is invalid: {self.selected_file}")
            return

        cmd_string = f'"{VLC_PATH}" "{windows_file_path}" :sout={sout_cmd} :no-sout-all :sout-keep'

        try:
            self.process = subprocess.Popen(cmd_string, shell=True)
            
            self.status_label.configure(text=f"STATUS: STREAMING! ({protocol} @ {port})", text_color="#FFD700")
            self.btn_start_server.configure(state="disabled")
            self.btn_stop_server.configure(state="normal")

        except FileNotFoundError:
            messagebox.showerror("Error", "VLC not found! Check the path in the code.")

    # ================= CLIENT UI & LOGIC =================
    def setup_client_ui(self):
        self.lbl_connect = ctk.CTkLabel(self.tab_client, 
            text="CONNECT TO REMOTE SERVER", 
            font=("Consolas", 20, "bold"),
            text_color="#FFD700"
        )
        self.lbl_connect.grid(row=0, column=0, columnspan=2, pady=(20, 25))

        # Server IP Input
        self.lbl_server_ip_client = ctk.CTkLabel(self.tab_client, text="SERVER IP:", font=("Arial", 16, "bold"))
        self.lbl_server_ip_client.grid(row=1, column=0, sticky="w", padx=(60, 10), pady=(15, 5))
        self.entry_server_ip = ctk.CTkEntry(self.tab_client, 
            placeholder_text="Enter Remote IP",
            corner_radius=10,
            height=35
        )
        self.entry_server_ip.grid(row=1, column=1, sticky="ew", padx=(10, 60), pady=(15, 5))

        # Protocol & Port (Must match server)
        self.lbl_client_proto = ctk.CTkLabel(self.tab_client, text="PROTOCOL:", font=("Arial", 16, "bold"))
        self.lbl_client_proto.grid(row=2, column=0, sticky="w", padx=(60, 10), pady=5)
        self.combo_client_proto = ctk.CTkComboBox(self.tab_client, values=["HTTP", "UDP"], corner_radius=10, height=35)
        self.combo_client_proto.set("HTTP")
        self.combo_client_proto.grid(row=2, column=1, sticky="ew", padx=(10, 60), pady=5)
        
        self.lbl_client_port = ctk.CTkLabel(self.tab_client, text="PORT:", font=("Arial", 16, "bold"))
        self.lbl_client_port.grid(row=3, column=0, sticky="w", padx=(60, 10), pady=5)
        self.entry_client_port = ctk.CTkEntry(self.tab_client, placeholder_text="8000", corner_radius=10, height=35)
        self.entry_client_port.insert(0, "8000")
        self.entry_client_port.grid(row=3, column=1, sticky="ew", padx=(10, 60), pady=5)

        self.btn_connect = ctk.CTkButton(self.tab_client, 
            text="CONNECT & PLAY 🔗", 
            fg_color="#00FFFF", # Cyan/Aqua
            hover_color="#00BFFF",
            text_color="#000000",
            corner_radius=20, 
            command=self.connect_stream,
            height=50,
            font=("Consolas", 18, "bold")
        )
        self.btn_connect.grid(row=4, column=0, columnspan=2, pady=(40, 15), padx=50, sticky="ew")
        
        self.btn_stop_client = ctk.CTkButton(self.tab_client, 
            text="STOP PLAYBACK 🛑", 
            fg_color="#CC0000", 
            hover_color="#990000",
            corner_radius=15, 
            state="disabled", 
            command=self.stop_vlc,
            height=40
        )
        self.btn_stop_client.grid(row=5, column=0, columnspan=2, pady=(0, 20), padx=50, sticky="ew")

    def connect_stream(self):
        ip = self.entry_server_ip.get()
        port = self.entry_client_port.get()
        protocol = self.combo_client_proto.get()
        
        if not ip:
            messagebox.showwarning("Input", "Please enter the Server IP.")
            return

        if protocol == "HTTP":
            url = f"http://{ip}:{port}/"
        else:
            url = f"udp://@239.0.0.1:{port}"

        cmd_string = f'"{VLC_PATH}" "{url}"'

        try:
            self.process = subprocess.Popen(cmd_string, shell=True)
            
            self.status_label.configure(text=f"STATUS: CLIENT CONNECTED ({ip})", text_color="#00FFFF")
            self.btn_connect.configure(state="disabled")
            self.btn_stop_client.configure(state="normal")

        except FileNotFoundError:
            messagebox.showerror("Error", "VLC not found!")

    # ================= SHARED LOGIC =================
    def stop_vlc(self):
        if self.process:
            try:
                subprocess.call("taskkill /IM vlc.exe /F", shell=True)
            except Exception:
                pass 
            self.process = None
            
        self.status_label.configure(text="STATUS: OFFLINE", text_color="#AAAAAA")
        
        self.btn_start_server.configure(state="normal")
        self.btn_stop_server.configure(state="disabled")
        self.btn_connect.configure(state="normal")
        self.btn_stop_client.configure(state="disabled")

    def on_close(self):
        self.stop_vlc()
        self.destroy()

if __name__ == "__main__":
    app = LANStreamerApp()
    app.mainloop()
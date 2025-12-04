import customtkinter as ctk
import socket
import subprocess
import os
from tkinter import filedialog, messagebox
import json
from PIL import Image

# --- CONFIGURATION ---
VLC_PATH_CONFIG_FILE = "vlc_config.json"
DEFAULT_VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
# Standard Multicast Address for RTP
MULTICAST_IP = "239.255.1.1" 

class LANStreamerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Appearance Settings ---
        ctk.set_appearance_mode("Light")
        ctk.set_widget_scaling(1.1)

        # 🎨 COLOR PALETTE (Kept for style consistency)
        self.custom_colors = {
            "bg_main": "#F0F2F5",          
            "fg_card": "#FFFFFF",          
            "text_dark": "#333333",        
            "text_medium": "#666666",      
            "text_light": "#999999",
            "ip_bg_start": "#F0F9FF",      
            "ip_bg_end": "#EEF2FF",        
            "ip_text": "#1D4ED8",          
            "blue_primary": "#1E40AF",     
            "red_error": "#F87171",        
            "start_stream_fg": "#059669", 
            "stop_stream_fg": "#E11D48",   
            "connect_play_fg": "#06B6D4",  
            "hover_start": "#34D399",      
            "hover_stop": "#F472B6",       
            "hover_connect": "#67E8F9",    
            "input_bg": "#FFFFFF",
            "input_border": "#D1D5DB",     
        }
        
        self.title("VLC Stream Hub - Compact")
        self.geometry("600x620") 
        self.minsize(580, 620) 
        self.configure(fg_color=self.custom_colors["bg_main"])
        
        # NOTE: Using a single self.process variable as per the user's latest code. 
        # This will need to be managed carefully in stop_vlc/on_close.
        self.process = None 
        
        self.vlc_path = self._load_vlc_path()
        
        # Configure grid weights to ensure the tabview expands and pushes the footer down
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 1. HEADER AREA (COMPACTED)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, pady=(15, 5), sticky="n") 
        
        self.label_title = ctk.CTkLabel(
            header_frame, 
            text="💿 VLC Stream Hub", 
            font=("Segoe UI", 24, "bold"), 
            text_color=self.custom_colors["blue_primary"]
        )
        self.label_title.pack(pady=0)

        # 2. TABS (MAIN CONTENT)
        self.tabview = ctk.CTkTabview(
            self,
            width=550, 
            height=480,
            corner_radius=20, 
            fg_color=self.custom_colors["fg_card"],
            segmented_button_fg_color=self.custom_colors["bg_main"],
            segmented_button_selected_color=self.custom_colors["fg_card"],
            segmented_button_unselected_color=self.custom_colors["bg_main"],
            segmented_button_selected_hover_color=self.custom_colors["bg_main"],
            segmented_button_unselected_hover_color=self.custom_colors["bg_main"],
            text_color=self.custom_colors["text_dark"],
            command=self._on_tab_change 
        )
        self.tabview.grid(row=1, column=0, padx=20, pady=(5, 10), sticky="nsew")
        
        self.tab_server = self.tabview.add("Server Mode")
        self.tab_client = self.tabview.add("Client Mode")

        self.setup_server_ui()
        self.setup_client_ui()
        
        # 3. STATUS BAR (Footer)
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=2, column=0, pady=(5, 15), sticky="s") 
        
        self.status_dot = ctk.CTkLabel(status_frame, text="●", font=("Arial", 20), text_color=self.custom_colors["stop_stream_fg"])
        self.status_dot.pack(side="left", padx=(0, 5))
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="STATUS: OFFLINE", 
            text_color=self.custom_colors["text_medium"], 
            font=("Segoe UI", 14)
        )
        self.status_label.pack(side="left")
        
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_tab_change(self):
        pass

    def _load_vlc_path(self):
        if os.path.exists(VLC_PATH_CONFIG_FILE):
            try:
                with open(VLC_PATH_CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get("vlc_path", DEFAULT_VLC_PATH)
            except json.JSONDecodeError:
                return DEFAULT_VLC_PATH
        return DEFAULT_VLC_PATH

    def _save_vlc_path(self, path):
        # NOTE: This function is now unused in the UI but remains functional
        with open(VLC_PATH_CONFIG_FILE, 'w') as f:
            json.dump({"vlc_path": path}, f)
            
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
        
        server_content_frame = ctk.CTkFrame(self.tab_server, fg_color="transparent", width=500) 
        server_content_frame.pack(fill="none", expand=False, padx=25, pady=10) 
        
        # Configure two equal columns for protocol and port
        server_content_frame.grid_columnconfigure(0, weight=1)
        server_content_frame.grid_columnconfigure(1, weight=1)

        # IP Address Display - Custom Styling
        lbl_your_ip = ctk.CTkLabel(server_content_frame, text="Your Local IP Address", font=("Segoe UI", 12), text_color=self.custom_colors["text_medium"])
        lbl_your_ip.grid(row=0, column=0, columnspan=2, pady=(5, 2))
        
        # IP Display Frame (Simulates the blue/indigo gradient box)
        ip_display_frame = ctk.CTkFrame(server_content_frame, 
                                        fg_color=self.custom_colors["ip_bg_start"], 
                                        border_color=self.custom_colors["blue_primary"],
                                        border_width=1,
                                        corner_radius=12)
        ip_display_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))

        self.local_ip = self.get_local_ip()
        self.lbl_server_ip = ctk.CTkLabel(ip_display_frame, 
            text=f"🌐 {self.local_ip}", 
            font=("Segoe UI", 18, "bold"),
            text_color=self.custom_colors["ip_text"],
            padx=15, 
            pady=8
        )
        self.lbl_server_ip.pack()

        # Server Mode Stream Status Indicator 
        self.lbl_stream_status = ctk.CTkLabel(
            server_content_frame, 
            text="STATUS: OFFLINE", 
            font=("Segoe UI", 14, "bold"), 
            text_color=self.custom_colors["stop_stream_fg"] 
        )
        self.lbl_stream_status.grid(row=2, column=0, columnspan=2, pady=(0, 20))

        # Source File
        lbl_source_file = ctk.CTkLabel(server_content_frame, text="Source File", font=("Segoe UI", 12), text_color=self.custom_colors["text_medium"], anchor="w")
        lbl_source_file.grid(row=3, column=0, columnspan=2, sticky="w", pady=(5, 2)) 

        # Select File Button
        self.btn_browse = ctk.CTkButton(server_content_frame, 
            text="Select Source File", 
            command=self.browse_file,
            fg_color="#F5F5F5", 
            hover_color="#DBEAFE", 
            text_color=self.custom_colors["text_dark"],
            border_width=2,
            border_color=self.custom_colors["input_border"], 
            corner_radius=12,
            height=40,
            font=("Segoe UI", 14, "bold"),
            compound="left",
            image=None 
        )
        self.btn_browse.grid(row=4, column=0, columnspan=2, pady=(0, 5), sticky="ew")
        
        self.lbl_file_path = ctk.CTkLabel(server_content_frame, 
            text="No source loaded", 
            text_color=self.custom_colors["red_error"],
            wraplength=480,
            font=("Segoe UI", 11)
        )
        self.lbl_file_path.grid(row=5, column=0, columnspan=2, pady=(0, 15), sticky="w")
        self.selected_file = None

        # --- Protocol and Port (Parallel Layout) ---
        
        # Protocol Label (Row 6, Column 0)
        lbl_proto = ctk.CTkLabel(server_content_frame, text="Protocol", font=("Segoe UI", 12), text_color=self.custom_colors["text_medium"], anchor="w")
        lbl_proto.grid(row=6, column=0, sticky="w", pady=(5, 2), padx=(0, 10)) 
        
        # Port Label (Row 6, Column 1)
        lbl_port = ctk.CTkLabel(server_content_frame, text="Port", font=("Segoe UI", 12), text_color=self.custom_colors["text_medium"], anchor="w")
        lbl_port.grid(row=6, column=1, sticky="w", pady=(5, 2), padx=(10, 0)) 
        
        # Protocol Combobox (Row 7, Column 0)
        self.combo_proto = ctk.CTkComboBox(server_content_frame, 
            values=["HTTP", "RTP", "UDP"], # RTSP REMOVED HERE
            corner_radius=12, 
            height=40,
            fg_color=self.custom_colors["input_bg"],
            dropdown_fg_color=self.custom_colors["input_bg"],
            button_color=self.custom_colors["input_border"],
            button_hover_color=self.custom_colors["input_border"],
            border_width=1,
            border_color=self.custom_colors["input_border"],
            font=("Segoe UI", 14),
            text_color=self.custom_colors["text_dark"]
        )
        self.combo_proto.set("HTTP")
        self.combo_proto.grid(row=7, column=0, pady=(0, 25), sticky="ew", padx=(0, 10)) 

        # Port Entry (Row 7, Column 1)
        self.entry_port = ctk.CTkEntry(server_content_frame, 
            placeholder_text="8000", 
            corner_radius=12, 
            height=40,
            fg_color=self.custom_colors["input_bg"],
            border_width=1,
            border_color=self.custom_colors["input_border"],
            font=("Segoe UI", 14),
            text_color=self.custom_colors["text_dark"]
        )
        self.entry_port.insert(0, "8000") 
        self.entry_port.grid(row=7, column=1, pady=(0, 25), sticky="ew", padx=(10, 0)) 
        
        # --- End Parallel Layout ---
        
        # Start/Stop Buttons (Rows 8 and 9, use columnspan=2)
        self.btn_start_server = ctk.CTkButton(server_content_frame, 
            text="▶️ START STREAM", 
            command=self.start_stream,
            fg_color=self.custom_colors["start_stream_fg"],
            hover_color=self.custom_colors["hover_start"],
            corner_radius=15, 
            height=50,
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        self.btn_start_server.grid(row=8, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        
        self.btn_stop_server = ctk.CTkButton(server_content_frame, 
            text="⏹️ STOP STREAM", 
            fg_color=self.custom_colors["stop_stream_fg"],
            hover_color=self.custom_colors["hover_stop"],
            corner_radius=15, 
            state="disabled", 
            command=self.stop_vlc,
            height=50,
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        self.btn_stop_server.grid(row=9, column=0, columnspan=2, pady=(0, 10), sticky="ew")


    def browse_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mp3")])
        if filename:
            self.selected_file = filename
            self.lbl_file_path.configure(text=f"File: {os.path.basename(filename)}", text_color=self.custom_colors["blue_primary"])

    def start_stream(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a video file first.")
            return

        # Check for VLC path existence
        if not os.path.exists(self.vlc_path):
            messagebox.showerror("Error", "VLC executable not found. Please ensure the path is set correctly in vlc_config.json, or install VLC at the default path.")
            return

        windows_file_path = os.path.normpath(self.selected_file)
        port = self.entry_port.get()
        protocol = self.combo_proto.get()
        local_ip = self.get_local_ip()
        
        # --- Server Mode VLC Output (sout) Configuration ---
        if protocol == "HTTP":
            # HTTP uses standard IP or 0.0.0.0 (default) to serve the stream
            sout_cmd = f'#transcode{{scodec=none}}:duplicate{{dst=http{{mux=mkv,dst=:{port}/}},dst=display}}'
            stream_target = f"{local_ip}:{port}"
            
        # RTSP case removed
             
        elif protocol == "RTP":
             # RTP streams sent to the Multicast IP (239.255.1.1)
             sout_cmd = f'#transcode{{scodec=none}}:duplicate{{dst=rtp{{dst={MULTICAST_IP},port={port},mux=ts}},dst=display}}'
             stream_target = f"{MULTICAST_IP}:{port}"
             
        elif protocol == "UDP":
             # UDP streams sent to the Local Unicast IP
             sout_cmd = f'#transcode{{scodec=none}}:duplicate{{dst=udp{{dst={local_ip},port={port},mux=ts}},dst=display}}'
             stream_target = f"{local_ip}:{port}"
             
        else:
            messagebox.showerror("Error", f"Unknown protocol selected: {protocol}")
            return
        # ---------------------------------------------------

        if not os.path.exists(self.selected_file):
            messagebox.showerror("Error", f"File not found or path is invalid: {self.selected_file}")
            return

        cmd_string = f'"{self.vlc_path}" "{windows_file_path}" :sout={sout_cmd} :no-sout-all :sout-keep'
        print(f"Server Command: {cmd_string}") # For debugging

        try:
            self.process = subprocess.Popen(cmd_string, shell=True)
            
            self.lbl_stream_status.configure(text=f"STATUS: STREAMING via {protocol} to {stream_target}", text_color=self.custom_colors["start_stream_fg"])

            self.status_dot.configure(text_color=self.custom_colors["start_stream_fg"])
            self.status_label.configure(text=f"STATUS: Streaming via {protocol} to {stream_target}", text_color=self.custom_colors["text_dark"])
            self.btn_start_server.configure(state="disabled")
            self.btn_stop_server.configure(state="normal")

        except FileNotFoundError:
            messagebox.showerror("Error", "VLC not found! Check the path in the settings.")

    # ================= CLIENT UI & LOGIC =================
    def setup_client_ui(self):
        
        client_content_frame = ctk.CTkFrame(self.tab_client, fg_color="transparent", width=500)
        client_content_frame.pack(fill="none", expand=False, padx=25, pady=10) 
        
        # Configure two equal columns for protocol and port
        client_content_frame.grid_columnconfigure(0, weight=1)
        client_content_frame.grid_columnconfigure(1, weight=1)

        # Header
        lbl_title_client = ctk.CTkLabel(client_content_frame, text="Connect to Remote Stream", font=("Segoe UI", 18, "bold"), text_color=self.custom_colors["blue_primary"])
        lbl_title_client.grid(row=0, column=0, columnspan=2, pady=(5, 5))
        lbl_subtitle_client = ctk.CTkLabel(client_content_frame, text="Enter target details to start playback", font=("Segoe UI", 12), text_color=self.custom_colors["text_medium"])
        lbl_subtitle_client.grid(row=1, column=0, columnspan=2, pady=(0, 25))

        # Server IP Input
        lbl_server_ip_client = ctk.CTkLabel(client_content_frame, text=f"Target IP Address (Use {MULTICAST_IP} for RTP)", font=("Segoe UI", 12), text_color=self.custom_colors["text_medium"], anchor="w")
        lbl_server_ip_client.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 2))
        self.entry_server_ip = ctk.CTkEntry(client_content_frame, 
            placeholder_text="e.g., 192.168.8.xxx (for UDP/HTTP) or 239.255.1.1 (for RTP)",
            corner_radius=12,
            height=40,
            fg_color=self.custom_colors["input_bg"],
            border_width=1,
            border_color=self.custom_colors["input_border"],
            font=("Segoe UI", 14),
            text_color=self.custom_colors["text_dark"]
        )
        self.entry_server_ip.grid(row=3, column=0, columnspan=2, pady=(0, 15), sticky="ew")

        # --- Protocol and Port (Parallel Layout) ---
        
        # Protocol Label (Row 4, Column 0)
        lbl_client_proto = ctk.CTkLabel(client_content_frame, text="Protocol", font=("Segoe UI", 12), text_color=self.custom_colors["text_medium"], anchor="w")
        lbl_client_proto.grid(row=4, column=0, sticky="w", pady=(5, 2), padx=(0, 10))
        
        # Port Label (Row 4, Column 1)
        lbl_client_port = ctk.CTkLabel(client_content_frame, text="Port", font=("Segoe UI", 12), text_color=self.custom_colors["text_medium"], anchor="w")
        lbl_client_port.grid(row=4, column=1, sticky="w", pady=(5, 2), padx=(10, 0))
        
        # Protocol Combobox (Row 5, Column 0)
        self.combo_client_proto = ctk.CTkComboBox(client_content_frame, 
            values=["HTTP", "RTP", "UDP"], # RTSP REMOVED HERE
            corner_radius=12, 
            height=40,
            fg_color=self.custom_colors["input_bg"],
            dropdown_fg_color=self.custom_colors["input_bg"],
            button_color=self.custom_colors["input_border"],
            button_hover_color=self.custom_colors["input_border"],
            border_width=1,
            border_color=self.custom_colors["input_border"],
            font=("Segoe UI", 14),
            text_color=self.custom_colors["text_dark"]
        )
        self.combo_client_proto.set("HTTP") 
        self.combo_client_proto.grid(row=5, column=0, pady=(0, 30), sticky="ew", padx=(0, 10))
        
        # Port Entry (Row 5, Column 1)
        self.entry_client_port = ctk.CTkEntry(client_content_frame, 
            placeholder_text="8000", 
            corner_radius=12, 
            height=40,
            fg_color=self.custom_colors["input_bg"],
            border_width=1,
            border_color=self.custom_colors["input_border"],
            font=("Segoe UI", 14),
            text_color=self.custom_colors["text_dark"]
        )
        self.entry_client_port.insert(0, "8000") 
        self.entry_client_port.grid(row=5, column=1, pady=(0, 30), sticky="ew", padx=(10, 0))

        # --- End Parallel Layout ---

        # Connect & Play Button (Row 6, Use columnspan=2)
        self.btn_connect = ctk.CTkButton(client_content_frame, 
            text="🔗 CONNECT & PLAY", 
            fg_color=self.custom_colors["connect_play_fg"],
            hover_color=self.custom_colors["hover_connect"],
            corner_radius=15, 
            command=self.connect_stream,
            height=50,
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        self.btn_connect.grid(row=6, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        
        # Stop Playback Button (Row 7, Use columnspan=2)
        self.btn_stop_client = ctk.CTkButton(client_content_frame, 
            text="⏹️ STOP PLAYBACK", 
            fg_color=self.custom_colors["stop_stream_fg"], 
            hover_color=self.custom_colors["hover_stop"],
            corner_radius=15, 
            state="disabled", 
            command=self.stop_vlc,
            height=50,
            font=("Segoe UI", 16, "bold"),
            text_color="#FFFFFF"
        )
        self.btn_stop_client.grid(row=7, column=0, columnspan=2, pady=(0, 0), sticky="ew")


    def connect_stream(self):
        if not os.path.exists(self.vlc_path):
            messagebox.showerror("Error", "VLC executable not found. Please ensure the path is set correctly in vlc_config.json, or install VLC at the default path.")
            return

        ip = self.entry_server_ip.get().strip()
        port = self.entry_client_port.get()
        protocol = self.combo_client_proto.get()
        
        if not ip:
            messagebox.showwarning("Input", "Please enter the Target IP address.")
            return

        if not port:
            messagebox.showwarning("Input", "Please enter the Port number.")
            return

        # --- Client URL Construction ---
        if protocol == "HTTP":
            url = f"http://{ip}:{port}/"
            
        # RTSP case removed
            
        elif protocol == "RTP" or protocol == "UDP":
            # RTP/UDP requires the listener format: protocol://@IP:Port
            url = f"{protocol.lower()}://@{ip}:{port}" 
            
        else:
            messagebox.showwarning("Protocol Error", "Invalid protocol selected.")
            return
        # -------------------------------

        print(f"Client Command: {self.vlc_path} {url}")
        cmd_string = f'"{self.vlc_path}" "{url}"'

        try:
            self.process = subprocess.Popen(cmd_string, shell=True)
            
            self.status_dot.configure(text_color=self.custom_colors["connect_play_fg"])
            self.status_label.configure(text=f"STATUS: Client Connected to {ip}:{port}", text_color=self.custom_colors["text_dark"])
            self.btn_connect.configure(state="disabled")
            self.btn_stop_client.configure(state="normal")

        except FileNotFoundError:
            messagebox.showerror("Error", "VLC not found! Check the path in the settings.")

    # ================= SHARED LOGIC =================
    def stop_vlc(self):
        # NOTE: This implementation uses taskkill /IM vlc.exe /F 
        # which will kill ALL running VLC instances, not just the one started by this app.
        if self.process:
            try:
                # Kills all processes named vlc.exe
                subprocess.call("taskkill /IM vlc.exe /F", shell=True)
            except Exception:
                pass 
            self.process = None
            
        if hasattr(self, 'lbl_stream_status'):
            self.lbl_stream_status.configure(text="STATUS: OFFLINE", text_color=self.custom_colors["stop_stream_fg"])

        self.status_dot.configure(text_color=self.custom_colors["stop_stream_fg"])
        self.status_label.configure(text="STATUS: OFFLINE", text_color=self.custom_colors["text_medium"])
        
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
# gui/layout.py
import customtkinter as ctk
from gui.controller import Controller
import threading
import cv2
from PIL import Image, ImageTk
from video.camera import Camera
import psutil
import time
import os
import pyvirtualcam  # Add this import
import numpy as np  # Fix for "np" not defined
from video.stream_server import start_stream_server, frame_lock
from tkinter import messagebox  # Add this import
try:
    import GPUtil
except ImportError:
    GPUtil = None


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        # Modern color scheme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(bg="#181C24")
        self.title("Smart Face Tracker Preview")
        self.geometry("1100x650")
        self.controller = Controller()
        self.tracked_face_idx = None

        self.ipcam_url = ctk.StringVar(value="http://<ip>:<port>/video")
        self.droidcam_index = ctk.StringVar(value="1")
        self.camera = None

        self.fps = 0
        self.last_frame_time = time.time()
        self.margin_value = ctk.DoubleVar(value=1.5)

        self.processor = None  # Will be set after background loading
        self.face_widgets = []
        self.loading_label = None
        self.running = True
        self.virtual_cam = None  # Ensure virtual_cam is not initialized automatically
        self.streaming_mode = ctk.StringVar(value="stream")  # Default to "stream"
        self.output_info_label = None  # Label to display mode-specific info

        self.setup_layout()
        self.show_loading_indicator()
        threading.Thread(target=self.init_face_processor, daemon=True).start()
        self.after(1000, self.update_stats_panel)  # Start stats update

    def show_loading_indicator(self):
        # Show a loading label in the face listbox
        if hasattr(self, "face_listbox"):
            for widget in self.face_listbox.winfo_children():
                widget.destroy()
            self.loading_label = ctk.CTkLabel(self.face_listbox, text="Loading faces...", font=("Segoe UI", 12, "italic"), text_color="#B0B8C7")
            self.loading_label.pack(pady=20)

    def init_face_processor(self):
        from video.processor import FaceProcessor
        self.processor = FaceProcessor()
        self.after(0, self.on_face_processor_ready)

    def on_face_processor_ready(self):
        if self.loading_label:
            self.loading_label.destroy()
        self.show_known_faces_thumbnails()
        threading.Thread(target=self.video_loop, daemon=True).start()  # Removed virtual cam initialization here

    def init_virtual_camera(self):
        # Initialize pyvirtualcam with the desired resolution and fps
        if self.virtual_cam is None:  # Only initialize if not already running
            try:
                self.virtual_cam = pyvirtualcam.Camera(width=960, height=540, fps=20, print_fps=False)
                print(f"Virtual camera started: {self.virtual_cam.device}")
            except Exception as e:
                print(f"Failed to start virtual camera: {e}")
                self.virtual_cam = None

    def setup_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=400, fg_color="#232837", corner_radius=18)  # Increased width to 300
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=(10, 0), pady=10)

        # Make sidebar content scrollable
        self.sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="#232837", corner_radius=0)
        self.sidebar_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        self.add_sidebar_widgets(self.sidebar_scroll)

        # Video Frame (16:9)
        self.video_frame = ctk.CTkCanvas(self, bg="#10131A", highlightthickness=0, bd=0)
        self.video_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.camera = Camera()

    def show_known_faces_thumbnails(self):
        if not self.processor or not hasattr(self.processor, "known_faces"):
            return
        self.face_widgets.clear()
        for widget in self.face_listbox.winfo_children():
            widget.destroy()
        for idx, (face_img, _) in enumerate(self.processor.known_faces):
            # Pass the filename (without extension) as the label
            name = os.path.splitext(self.processor.known_names[idx])[0]
            thumbnail = self.create_thumbnail(face_img, idx, name)
            thumbnail.pack(pady=7)
            self.face_widgets.append(thumbnail)

    def add_sidebar_widgets(self, parent):
        # Frame Ratio
        ctk.CTkLabel(parent, text="Frame Ratio", font=("Segoe UI", 16, "bold"), text_color="#E0E6F0").pack(pady=(18, 6))
        self.ratio_option = ctk.CTkOptionMenu(
            parent, values=["16:9", "1:1", "16:10"],
            command=self.controller.change_ratio,
            fg_color="#2D3346", button_color="#3B4257", dropdown_fg_color="#232837",
            dropdown_hover_color="#3B4257", corner_radius=12, text_color="#E0E6F0"
        )
        self.ratio_option.pack(pady=(0, 10))

        # Margin Selection
        ctk.CTkLabel(parent, text="Tracking Margin", font=("Segoe UI", 13), text_color="#B0B8C7").pack(pady=(6, 0))
        self.margin_option = ctk.CTkOptionMenu(
            parent, values=["0.5", "1.0", "1.5", "2.0"],
            command=self.change_margin,
            variable=self.margin_value,
            fg_color="#2D3346", button_color="#3B4257", dropdown_fg_color="#232837",
            dropdown_hover_color="#3B4257", corner_radius=12, text_color="#E0E6F0"
        )
        self.margin_option.pack(pady=(0, 10))

        # Available Faces
        ctk.CTkLabel(parent, text="Available Faces", font=("Segoe UI", 15, "bold"), text_color="#E0E6F0").pack(pady=(10, 6))
        self.face_listbox = ctk.CTkScrollableFrame(parent, height=200, fg_color="#232837", corner_radius=12)
        self.face_listbox.pack(fill="both", expand=True, padx=8)

        # Stats Panel
        ctk.CTkLabel(parent, text="Stats", font=("Segoe UI", 15, "bold"), text_color="#E0E6F0").pack(pady=(18, 6))
        self.stats_panel = ctk.CTkFrame(parent, fg_color="#232837", corner_radius=12)
        self.stats_panel.pack(fill="x", padx=8, pady=(0, 10))
        self.stats_label = ctk.CTkLabel(self.stats_panel, text="Loading...", font=("Consolas", 12), justify="left", text_color="#B0B8C7")
        self.stats_label.pack(anchor="w", padx=10, pady=8)

        # IP Webcam Option
        ctk.CTkLabel(parent, text="IP Webcam URL", font=("Segoe UI", 13), text_color="#B0B8C7").pack(pady=(10, 0))
        ip_entry = ctk.CTkEntry(parent, textvariable=self.ipcam_url, width=200, fg_color="#232837", border_color="#3B4257", corner_radius=10, text_color="#E0E6F0")
        ip_entry.pack(pady=(0, 5), padx=8)
        connect_btn = ctk.CTkButton(parent, text="Connect", command=self.connect_ipcam,
                                    fg_color="#3B82F6", hover_color="#2563EB", text_color="#fff", corner_radius=10, font=("Segoe UI", 12, "bold"))
        connect_btn.pack(pady=(0, 10), padx=8, fill="x")

        # DroidCam USB Option
        ctk.CTkLabel(parent, text="DroidCam USB Index", font=("Segoe UI", 13), text_color="#B0B8C7").pack(pady=(10, 0))
        droidcam_entry = ctk.CTkEntry(parent, textvariable=self.droidcam_index, width=60, fg_color="#232837", border_color="#3B4257", corner_radius=10, text_color="#E0E6F0")
        droidcam_entry.pack(pady=(0, 5), anchor="w", padx=18)
        droidcam_btn = ctk.CTkButton(parent, text="Connect DroidCam (USB)", command=self.connect_droidcam,
                                     fg_color="#10B981", hover_color="#059669", text_color="#fff", corner_radius=10, font=("Segoe UI", 12, "bold"))
        droidcam_btn.pack(pady=(0, 10), padx=8, fill="x")

        # Video Output Mode
        ctk.CTkLabel(parent, text="Video Output Mode", font=("Segoe UI", 13), text_color="#B0B8C7").pack(pady=(10, 0))
        self.output_mode_option = ctk.CTkOptionMenu(
            parent,
            values=["stream", "virtual_cam"],
            command=self.change_output_mode,
            variable=self.streaming_mode,
            fg_color="#2D3346", button_color="#3B4257", dropdown_fg_color="#232837",
            dropdown_hover_color="#3B4257", corner_radius=12, text_color="#E0E6F0"
        )
        self.output_mode_option.pack(pady=(0, 10))

        # Output Info Label
        self.output_info_label = ctk.CTkLabel(
            parent,
            text="",
            font=("Segoe UI", 14, "bold"),  # Larger font for better visibility
            text_color="#FFFFFF",  # White text for better contrast
            wraplength=220,  # Wrap text to fit the sidebar width
            justify="left",
            fg_color="#2D3346",  # Background color for better readability
            corner_radius=10,  # Rounded corners
            padx=10, pady=10  # Padding for better spacing
        )
        self.output_info_label.pack(pady=(10, 0))

    def change_output_mode(self, mode):
        if mode == "none":
            print("Stopped all video output.")
            self.stop_all_outputs()
            self.output_info_label.configure(
                text="Video output stopped.",
                fg_color="#2D3346"  # Neutral background color
            )
        elif mode == "stream":
            print("Switched to local streaming mode.")
            threading.Thread(target=start_stream_server, daemon=True).start()
            self.output_info_label.configure(
                text="Streaming at:\nhttp://localhost:8080\n\n"
                     "Guide:\n"
                     "1. Open the above link in your browser.\n"
                     "2. Use the browser window to view the video stream.\n"
                     "3. You can also use tools like OBS Studio to capture the stream.",
                fg_color="#1E5128"  # Green background for success
            )
        elif mode == "virtual_cam":
            print("Switched to virtual webcam mode.")
            self.init_virtual_camera()
            self.output_info_label.configure(
                text="Guide to use Virtual Webcam with OBS Studio:\n\n"
                     "1. Open OBS Studio.\n"
                     "2. Add a 'Video Capture Device' source.\n"
                     "3. Select 'OBS Virtual Camera' as the device.\n"
                     "4. Start the virtual camera in OBS (Tools > Start Virtual Camera).\n"
                     "5. Open your video conferencing app and select 'OBS Virtual Camera' as your webcam.",
                fg_color="#1E3A8A"  # Blue background for instructions
            )

    def stop_all_outputs(self):
        # Stop streaming and virtual cam
        global current_frame
        with frame_lock:
            current_frame = None
        if self.virtual_cam:
            self.virtual_cam.close()
            self.virtual_cam = None

    def update_stats_panel(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        fps = self.fps
        gpu_str = ""
        if GPUtil:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_str = f"\nGPU: {gpu.load*100:.1f}% ({gpu.memoryUsed:.0f}MB/{gpu.memoryTotal:.0f}MB)"
        stats = (
            f"CPU: {cpu:.1f}%\n"
            f"Memory: {mem:.1f}%\n"
            f"FPS: {fps:.1f}{gpu_str}"
        )
        self.stats_label.configure(text=stats)
        self.after(1000, self.update_stats_panel)

    def connect_ipcam(self):
        url = self.ipcam_url.get()
        try:
            if self.camera:
                self.camera.release()
            self.camera = Camera(source=url)
            print(f"Connected to IP webcam: {url}")
        except Exception as e:
            print(f"Failed to connect to IP webcam: {e}")

    def connect_droidcam(self):
        try:
            index = int(self.droidcam_index.get())
            if self.camera:
                self.camera.release()
            self.camera = Camera(source=index)
            print(f"Connected to DroidCam USB at index {index}")
        except Exception as e:
            print(f"Failed to connect to DroidCam USB: {e}")

    def video_loop(self):
        global current_frame
        while self.running:
            if not self.processor:
                time.sleep(0.1)
                continue
            frame = self.camera.get_frame()
            if frame is None:
                continue

            # Face detection + tracking
            faces, _ = self.processor.detect_faces(frame)

            # Crop to tracked face
            tracked_box = self.processor.get_tracked_box(faces)
            if tracked_box is not None:
                x, y, w_box, h_box = tracked_box
                x, y = int(max(0, x)), int(max(0, y))
                x2, y2 = int(min(frame.shape[1], x + w_box)), int(min(frame.shape[0], y + h_box))
                frame = frame[y:y2, x:x2]

            # Resize to preview resolution and apply aspect ratio
            frame = self.apply_frame_ratio(frame)

            # FPS calculation
            now = time.time()
            self.fps = 1.0 / (now - self.last_frame_time) if self.last_frame_time else 0
            self.last_frame_time = now

            # Convert to tkinter-compatible image
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update canvas
            self.video_frame.create_image(0, 0, anchor="nw", image=imgtk)
            self.video_frame.image = imgtk  # Prevent garbage collection

            # Send frame to virtual webcam
            if self.streaming_mode.get() == "virtual_cam" and self.virtual_cam:
                try:
                    # pyvirtualcam expects RGB numpy array
                    self.virtual_cam.send(np.array(img))
                    self.virtual_cam.sleep_until_next_frame()
                except Exception as e:
                    print(f"Virtual cam error: {e}")

            # Update the current frame for streaming
            if self.streaming_mode.get() == "stream":
                with frame_lock:
                    current_frame = frame

    def create_thumbnail(self, face_snip, index, name):
        face_snip = cv2.resize(face_snip, (100, 100))
        img = cv2.cvtColor(face_snip, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img)
        thumb = ImageTk.PhotoImage(pil_img)

        label = ctk.CTkLabel(
            self.face_listbox,
            image=thumb,
            text=name,  # Use the filename as label
            compound="top",
            fg_color="#232837",
            corner_radius=10,
            text_color="#E0E6F0",
            font=("Segoe UI", 11, "bold")
        )
        label.image = thumb

        def on_click():
            if not self.processor:
                return
            if self.processor.tracked_index == index:
                self.processor.set_tracked_index(None)
                print("Exited face tracking")
            else:
                self.processor.set_tracked_index(index)
                print(f"Tracking face #{index} ({name})")

        label.bind("<Button-1>", lambda e: on_click())
        return label

    def apply_frame_ratio(self, frame):
        h, w = frame.shape[:2]
        ratio_str = self.ratio_option.get()
        target_ratios = {
            "16:9": 16 / 9,
            "1:1": 1.0,
            "16:10": 16 / 10
        }
        target_ratio = target_ratios.get(ratio_str, 16/9)

        # Compute center crop
        current_ratio = w / h
        if (current_ratio > target_ratio):
            # too wide: crop width
            new_w = int(h * target_ratio)
            x1 = (w - new_w) // 2
            frame = frame[:, x1:x1 + new_w]
        else:
            # too tall: crop height
            new_h = int(w / target_ratio)
            y1 = (h - new_h) // 2
            frame = frame[y1:y1 + new_h, :]

        return cv2.resize(frame, (960, 540))

    def change_margin(self, value):
        try:
            margin = float(value)
            self.margin_value.set(margin)
            if self.processor:
                self.processor.tracking_margin = margin
            print(f"Changed tracking margin to: {margin}")
        except Exception:
            pass
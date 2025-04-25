# LivePortraitVideo

A smart face tracking and streaming application with a modern GUI, supporting local webcams, IP cameras, DroidCam, and output to both browser streaming and virtual webcam (for OBS/Zoom/Teams).

---

## Features

- **Face Detection & Tracking:** Detects and tracks faces in real-time using OpenCV and DeepFace.
- **Multiple Camera Sources:** Supports local webcams, IP cameras, and DroidCam (USB).
- **Modern GUI:** Built with CustomTkinter for a sleek, dark-themed interface.
- **Streaming Output:** Stream video to browser (`http://localhost:8080`) or as a virtual webcam (OBS Virtual Camera).
- **Stats Panel:** Real-time CPU, memory, FPS, and GPU usage.
- **Face Gallery:** Displays known faces for easy selection and tracking.
- **Customizable:** Change aspect ratio and tracking margin on the fly.

---

## Technologies Used

- **Python 3.8+**
- **OpenCV** (cv2)
- **DeepFace** (face recognition)
- **CustomTkinter** (modern GUI)
- **Flask** (video streaming server)
- **pyvirtualcam** (virtual webcam output)
- **Pillow** (image handling)
- **psutil, GPUtil** (system stats)
- **NumPy**

---

## How to Use

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install opencv-python deepface customtkinter flask pyvirtualcam pillow psutil gputil
```

### 2. Prepare Known Faces

- Place images of known faces in the `assets/known_faces_pics/` directory.
- Supported formats: `.jpg`, `.png`.

### 3. Run the Application

```bash
python main.py
```

### 4. Using the GUI

- **Select Camera Source:** Choose local webcam, IP camera (enter URL), or DroidCam (enter index).
- **Choose Output Mode:** 
  - `stream`: View in browser at [http://localhost:8080](http://localhost:8080).
  - `virtual_cam`: Use as a webcam in OBS/Zoom/Teams.
- **Track a Face:** Click a face thumbnail to track it.
- **Adjust Settings:** Change aspect ratio and tracking margin as needed.

---

## Screenshots

> Replace these with your own screenshots.

![Main GUI](assets/readme_screenshot_main.png)
*Main application window*

![Face Gallery](assets/readme_screenshot_faces.png)
*Face gallery for selection*

---

## Pros & Cons

### Pros

- **User-Friendly:** Modern, intuitive GUI.
- **Flexible Output:** Stream or virtual webcam.
- **Face Recognition:** Remembers and tracks known faces.
- **Customizable:** Easy to adjust tracking and output settings.

### Cons

- **Resource Intensive:** Deep learning models require a decent CPU/GPU.
- **Dependency Heavy:** Needs several Python packages.
- **Limited Face Recognition:** Relies on DeepFace; may not be robust in all lighting/angles.
- **No Cross-Platform Virtual Cam:** pyvirtualcam may not work on all OSes.

---

## What Can Be Improved

- **Better Error Handling:** More user-friendly error messages.
- **Face Management:** Add/remove faces from GUI.
- **Performance:** Optimize for lower-end hardware.
- **Cross-Platform Support:** Improve virtual cam support on Mac/Linux.
- **Recording:** Add option to record video.
- **Settings Persistence:** Save user preferences.
- **Documentation:** More detailed user and developer docs.

---

## License

MIT License

---

## Credits

- [OpenCV](https://opencv.org/)
- [DeepFace](https://github.com/serengil/deepface)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [pyvirtualcam](https://github.com/letmaik/pyvirtualcam)

---


import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
# main.py
# Requires: pip install psutil GPUtil
from gui.layout import App

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.camera.release(), app.destroy()))
    app.mainloop()

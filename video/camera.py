# video/camera.py
import cv2

class Camera:
    def __init__(self, source=0):
        # Accept both int (local) and str (IP cam URL)
        self.cap = cv2.VideoCapture(source)
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    def get_frame(self):
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        self.cap.release()

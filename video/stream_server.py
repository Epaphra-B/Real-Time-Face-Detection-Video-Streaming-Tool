import cv2
import threading
from flask import Flask, Response

app = Flask(__name__)
frame_lock = threading.Lock()
current_frame = None

@app.route('/')
def video_feed():
    def generate():
        global current_frame
        while True:
            with frame_lock:
                if current_frame is None:
                    continue
                _, buffer = cv2.imencode('.jpg', current_frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def start_stream_server():
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)

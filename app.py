import cv2
import numpy as np
import mediapipe as mp
import threading
import time
from flask import Flask, Response, render_template, request, jsonify

app = Flask(__name__, static_folder="static", template_folder="templates")

# Try different camera indexes
def find_camera_index():
    for i in range(5):  # Check up to 5 indexes
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✅ Camera found at index {i}")
            cap.release()
            return i
        cap.release()
    return -1

camera_index = find_camera_index()
if camera_index == -1:
    print("❌ No camera detected. Check permissions or try a different device.")

# Open camera if available
camera = cv2.VideoCapture(camera_index) if camera_index != -1 else None
if camera:
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduces lag

# Mediapipe FaceMesh Model
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False, max_num_faces=5, refine_landmarks=True
)

# Global Variables
current_shade = (0, 0, 255)  # Default red lipstick (BGR)
processed_frame = None
lock = threading.Lock()

def hex_to_bgr(hex_color):
    """Convert HEX color to BGR format"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (4, 2, 0))

@app.route("/apply_makeup", methods=["POST"])
def apply_makeup():
    global current_shade
    data = request.get_json()
    new_shade = data.get("shade", "#FF0000")  # Default red
    current_shade = hex_to_bgr(new_shade)
    print(f"Updated shade: {current_shade}")
    return jsonify({"status": "success", "new_shade": new_shade})

def apply_lipstick(image, lips_mask, color, opacity=0.6):
    """Applies lipstick with a natural finish"""
    soft_mask = cv2.GaussianBlur(lips_mask.astype(float) / 255, (5, 5), 2)
    color_layer = np.full_like(image, color, dtype=np.uint8)
    matte_color = cv2.addWeighted(color_layer, 0.6, np.zeros_like(color_layer), 0.4, 0)
    for c in range(3):
        image[:, :, c] = (image[:, :, c] * (1 - soft_mask * opacity) +
                          matte_color[:, :, c] * soft_mask * opacity)
    return np.clip(image, 0, 255).astype(np.uint8)

def process_makeup(image):
    global current_shade
    h, w, _ = image.shape
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            lips_outer = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 306, 270, 269, 267, 0, 37, 39, 40, 185]
            lips_inner = [78, 95, 88, 178, 87, 14, 317, 402, 318, 324, 308, 415, 310, 311, 312, 13, 82, 81, 80, 191]
            
            outer_lip_points = np.array([(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in lips_outer], np.int32)
            inner_lip_points = np.array([(int(face_landmarks.landmark[i].x * w), int(face_landmarks.landmark[i].y * h)) for i in lips_inner], np.int32)
            
            lip_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(lip_mask, [outer_lip_points], 255)
            cv2.fillPoly(lip_mask, [inner_lip_points], 0)
            
            image = apply_lipstick(image, lips_mask=lip_mask, color=current_shade)
    
    return image

def process_frame():
    """Threaded frame processing"""
    global processed_frame
    while True:
        if camera:
            success, frame = camera.read()
            if not success:
                continue
            frame = cv2.flip(frame, 1)
            frame = process_makeup(frame)
            with lock:
                processed_frame = frame
        time.sleep(0.03)

if camera:
    threading.Thread(target=process_frame, daemon=True).start()

def generate_frames():
    """Generate camera frames for video streaming"""
    global processed_frame
    while True:
        if processed_frame is not None:
            with lock:
                frame = processed_frame.copy()
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n")

@app.route("/video_feed")
def video_feed():
    if not camera:
        return "❌ Camera not available. Please check permissions."
    return Response(generate_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

import os
import pickle
import threading

KNOWN_FACES_DIR = "known_faces_pics"
PICKLE_FILE = "known_faces.pkl"

def extract_face_features(image_path):
    # ...existing code for extracting face features...
    pass

def load_face_features():
    if os.path.exists(PICKLE_FILE):
        with open(PICKLE_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_face_features(features):
    with open(PICKLE_FILE, "wb") as f:
        pickle.dump(features, f)

def update_face_features():
    features = load_face_features()
    current_files = set(os.listdir(KNOWN_FACES_DIR))
    # Remove deleted images
    removed = [k for k in features if k not in current_files]
    for k in removed:
        del features[k]
    # Add new images
    for fname in current_files:
        if fname not in features:
            img_path = os.path.join(KNOWN_FACES_DIR, fname)
            features[fname] = extract_face_features(img_path)
    save_face_features(features)

def background_update():
    thread = threading.Thread(target=update_face_features, daemon=True)
    thread.start()

# Call background_update() during app startup

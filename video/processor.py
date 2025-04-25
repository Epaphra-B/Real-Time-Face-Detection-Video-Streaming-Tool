import cv2
import numpy as np
import os
import pickle

class FaceProcessor:
    def __init__(self):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.known_faces = []  # list of (face image, embedding)
        self.known_names = []  # optional: store filenames or labels
        self.tracked_index = None
        self.smoothed_box = None
        self.cache_path = "assets/known_faces.pkl"
        self.tracking_margin = 1.5
        self._load_known_faces("assets/known_faces_pics")

    def _load_known_faces(self, folder):
        from deepface import DeepFace  # moved import here
        # Load cache if exists
        cache = {}
        if os.path.exists(self.cache_path):
            with open(self.cache_path, "rb") as f:
                cache = pickle.load(f)
        updated_cache = {}
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if not (fname.lower().endswith(".jpg") or fname.lower().endswith(".png")):
                continue
            img = cv2.imread(fpath)
            if img is None:
                continue
            mtime = os.path.getmtime(fpath)
            cache_key = (fname, mtime)
            if cache_key in cache:
                embedding = cache[cache_key]["embedding"]
                self.known_faces.append((img, embedding))
                self.known_names.append(fname)
                updated_cache[cache_key] = cache[cache_key]
            else:
                face_img = cv2.cvtColor(self._resize_face(img), cv2.COLOR_BGR2RGB)
                try:
                    embedding_objs = DeepFace.represent(face_img, model_name="Facenet", enforce_detection=False)
                    if isinstance(embedding_objs, list) and len(embedding_objs) > 0:
                        embedding = embedding_objs[0]["embedding"]
                        self.known_faces.append((img, embedding))
                        self.known_names.append(fname)
                        updated_cache[cache_key] = {"embedding": embedding}
                except Exception:
                    continue
        # Save updated cache
        with open(self.cache_path, "wb") as f:
            pickle.dump(updated_cache, f)

    def detect_faces(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        detected_known_faces = []
        for (x, y, w, h) in faces:
            face_snip = frame[y:y + h, x:x + w]
            if self._is_known(face_snip):
                detected_known_faces.append(face_snip)
        return faces, detected_known_faces

    def _is_known(self, new_face):
        if not self.known_faces:
            return False

        new_embedding = self._get_embedding(new_face)
        if new_embedding is None:
            return False

        for _, known_embedding in self.known_faces:
            similarity = self._cosine_similarity(new_embedding, known_embedding)
            if similarity > 0.7:  # threshold, can be tuned
                return True
        return False

    def _get_embedding(self, face_img):
        try:
            from deepface import DeepFace  # moved import here
            face_rgb = cv2.cvtColor(self._resize_face(face_img), cv2.COLOR_BGR2RGB)
            embedding_objs = DeepFace.represent(face_rgb, model_name="Facenet", enforce_detection=False)
            if isinstance(embedding_objs, list) and len(embedding_objs) > 0:
                return embedding_objs[0]["embedding"]
        except Exception:
            pass
        return None

    def _cosine_similarity(self, emb1, emb2):
        emb1 = np.array(emb1)
        emb2 = np.array(emb2)
        if np.linalg.norm(emb1) == 0 or np.linalg.norm(emb2) == 0:
            return 0
        return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

    def _resize_face(self, face_img, size=(160, 160)):
        return cv2.resize(face_img, size)

    def _mse(self, img1, img2):
        # Mean Squared Error
        err = np.sum((img1.astype("float") - img2.astype("float")) ** 2)
        err /= float(img1.shape[0] * img1.shape[1])
        return err

    def set_tracked_index(self, index):
        self.tracked_index = index
        self.smoothed_box = None  # reset smoothing

    def get_tracked_box(self, faces):
        if self.tracked_index is None or self.tracked_index >= len(faces):
            return None

        x, y, w, h = faces[self.tracked_index]
        margin = self.tracking_margin  # use dynamic margin
        cx, cy = x + w / 2, y + h / 2
        w *= (1 + margin * 2)
        h *= (1 + margin * 2)
        x = cx - w / 2
        y = cy - h / 2

        current_box = np.array([x, y, w, h], dtype=np.float32)

        if self.smoothed_box is None:
            self.smoothed_box = current_box
        else:
            alpha = 0.2  # smoothing factor
            self.smoothed_box = alpha * current_box + (1 - alpha) * self.smoothed_box

        return self.smoothed_box

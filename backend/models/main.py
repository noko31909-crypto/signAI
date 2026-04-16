import pickle
import cv2
import numpy as np
import mediapipe as mp
from collections import deque, Counter
import base64
import time
import os

# FastAPI and Uvicorn imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

# EXPLICIT IMPORTS: This fixes the "AttributeError: module 'mediapipe' has no attribute 'solutions'"
from mediapipe.python.solutions import hands as mp_hands_solution
from mediapipe.python.solutions import drawing_utils as mp_drawing
from mediapipe.python.solutions import drawing_styles as mp_drawing_styles

app = FastAPI(title="Sign Language Recognizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Model Loading ---
# This ensures we find the model.p file relative to where this script is saved
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "model.p")

try:
    with open(MODEL_PATH, "rb") as f:
        model_dict = pickle.load(f)
    model = model_dict["model"]
    print(f"✅ Model loaded successfully from {MODEL_PATH}")
except FileNotFoundError:
    print(f"❌ ERROR: Model file not found at {MODEL_PATH}")
    model = None
except Exception as e:
    print(f"❌ ERROR loading model: {e}")
    model = None

labels_dict = {
    0: "Yes", 1: "No", 2: "OK", 3: "Stop", 4: "I", 5: "You", 6: "We",
    7: "Friend", 8: "Hello", 9: "Goodbye", 10: "Love", 11: "Help",
    12: "Thank you", 13: "Please", 14: "Want", 15: "Can", 16: "Sorry",
    17: "Cannot", 18: "Eat", 19: "Work", 20: "Study", 21: "Watch",
    22: "Listen", 23: "Speak", 24: "Understand", 25: "Question",
    26: "Answer", 27: "Good", 28: "Bad", 29: "How are you",
    30: "What are you doing", 31: "See you"
}

class GestureProcessor:
    def __init__(self):
        # Using the explicit solution import
        self.hands = mp_hands_solution.Hands(
            static_image_mode=False,
            min_detection_confidence=0.7,
            max_num_hands=1
        )
        self.pred_buffer = deque(maxlen=10)
        self.current_gesture = None
        self.gesture_start_time = 0
        self.printed_gesture = None
        self.stable_prediction = None
        self.same_count = 0

    def process_frame(self, frame_bytes: bytes):
        if model is None:
            return {"error": "Model not loaded on server"}

        try:
            nparr = np.frombuffer(frame_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception:
            return {"gesture": None, "confidence": 0, "hands_detected": 0}

        if frame is None:
            return {"gesture": None, "confidence": 0, "hands_detected": 0}

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        if not results.multi_hand_landmarks:
            self.pred_buffer.clear()
            self.stable_prediction = None
            self.same_count = 0
            self.current_gesture = None
            self.printed_gesture = None
            return {"gesture": None, "confidence": 0, "hands_detected": 0}

        hand_landmarks = results.multi_hand_landmarks[0]
        data_aux, x_, y_, z_ = [], [], [], []

        for landmark in hand_landmarks.landmark:
            x_.append(landmark.x)
            y_.append(landmark.y)
            z_.append(landmark.z)

        for landmark in hand_landmarks.landmark:
            data_aux.append(landmark.x - min(x_))
            data_aux.append(landmark.y - min(y_))
            data_aux.append(landmark.z - min(z_))

        try:
            prediction = model.predict([np.asarray(data_aux)])
            predicted_class = prediction[0]
            confidence = float(np.max(model.predict_proba([np.asarray(data_aux)])))

            self.pred_buffer.append(predicted_class)
            final_prediction = Counter(self.pred_buffer).most_common(1)[0][0]

            if final_prediction == self.stable_prediction:
                self.same_count += 1
            else:
                self.same_count = 0
                self.stable_prediction = final_prediction

            now = time.time()
            is_new_gesture = False

            if final_prediction != self.current_gesture:
                self.current_gesture = final_prediction
                self.gesture_start_time = now
                self.printed_gesture = None
            elif self.same_count >= 5 and (now - self.gesture_start_time) >= 1.0:
                if self.printed_gesture != self.current_gesture:
                    self.printed_gesture = self.current_gesture
                    is_new_gesture = True

            display_gesture = labels_dict[int(final_prediction)] if self.same_count >= 5 else ""

            return {
                "gesture": display_gesture,
                "confidence": round(confidence, 3),
                "hands_detected": len(results.multi_hand_landmarks),
                "is_new_gesture": is_new_gesture,
                "spoken_gesture": labels_dict[int(final_prediction)] if is_new_gesture else None
            }

        except Exception as e:
            return {"gesture": None, "confidence": 0, "hands_detected": 1, "error": str(e)}

processors = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    processors[client_id] = GestureProcessor()
    print(f"📡 Client {client_id} connected via WebSocket")

    try:
        while True:
            data = await websocket.receive_bytes()
            result = processors[client_id].process_frame(data)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        if client_id in processors:
            del processors[client_id]
        print(f"🔌 Client {client_id} disconnected")

@app.get("/health")
def health():
    return {
        "status": "online", 
        "gestures_supported": len(labels_dict), 
        "model_loaded": model is not None
    }

if __name__ == "__main__":
    # Standard uvicorn run configuration
    print("🚀 Starting FastAPI Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
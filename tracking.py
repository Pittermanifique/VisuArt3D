from multiprocessing import Queue, shared_memory
import struct
import cv2
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

def face_detection(buffer_track,queue = None,camera_index=0):

    face_cascade_path = "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_cascade_path)

    base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
    options = vision.HandLandmarkerOptions(base_options=base_options,num_hands=16)
    detector = vision.HandLandmarker.create_from_options(options)

    life_pouce = 0

    cap = cv2.VideoCapture(camera_index)

    previous_faces = []

    next_face_id = 0      

    def distance(p1, p2):
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])
    
    def calculate_rot(cx,w):
        cw = w / 2
        rot = (cx - cw) / cw
        rot = max(-1, min(1, rot))
        return round(rot, 2)
    
    while True:
        ret, frame = cap.read()

        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        if not ret:
            print("Erreur : impossible de lire la caméra.")
            break

        height, width = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        current_faces = []

        for (x, y, w, h) in faces:
            cx = x + w // 2
            cy = y + h // 2

            assigned_id = None

            for old in previous_faces:
                if distance((cx, cy), (old["cx"], old["cy"])) < 50:
                    assigned_id = old["id"]
                    break

            if assigned_id is None:
                assigned_id = next_face_id
                next_face_id += 1

            current_faces.append({"id": assigned_id, "cx": cx, "cy": cy, "bbox": (x, y, w, h)})
        
        current_faces.sort(key=lambda f: f["bbox"][2] * f["bbox"][3], reverse=True)

        palms = detector.detect(mp_image)

        if current_faces:
            buffer_track[:] = struct.pack("f", calculate_rot(current_faces[0]["cx"], width))
        else:
            buffer_track[:] = struct.pack("f", 0.0)

        for f in current_faces:
            x, y, w, h = f["bbox"]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(frame, f"ID {f['id']}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            cv2.circle(frame, (f["cx"], f["cy"]), 5, (0,0,255), -1)

        if palms.hand_landmarks and queue:
            for hand_landmarks in palms.hand_landmarks:
                thumb_tip = hand_landmarks[4]  
                thumb_ip = hand_landmarks[3]    
                index_tip = hand_landmarks[8]   
                index_mcp = hand_landmarks[5]   
                middle_tip = hand_landmarks[12]
                ring_tip = hand_landmarks[16]
                pinky_tip = hand_landmarks[20]

                thumb_is_up = thumb_tip.y < thumb_ip.y 

                fingers_folded = (index_tip.y > index_mcp.y and 
                                middle_tip.y > hand_landmarks[9].y and 
                                ring_tip.y > hand_landmarks[13].y and 
                                pinky_tip.y > hand_landmarks[17].y)

                if thumb_is_up and fingers_folded:
                    life_pouce += 1
                    if life_pouce == 15:
                        life_pouce = 0
                        queue.put(("play_audio", None))
                else:
                    life_pouce = 0

        cv2.imshow("Detection continue", frame)

        previous_faces = current_faces

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        shm = shared_memory.SharedMemory(name='shm_track')
        shm.close()
        shm.unlink()
        print("Mémoire shm_track supprimée.")
    except FileNotFoundError:
        print("Aucune mémoire shm_track à supprimer.")

    shm_track = shared_memory.SharedMemory(create=True, size=4, name='shm_track')
    buffer = shm_track.buf

    face_detection(buffer)